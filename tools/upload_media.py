import requests
from typing import Dict, Any, Generator
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from ..utils.wechat_api_client import WechatApiClient
import logging

logger = logging.getLogger(__name__)

class UploadMediaTool(Tool):
    """上传临时素材工具"""
    
    def _invoke(self, tool_parameters: Dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """
        调用上传媒体工具
        
        Args:
            tool_parameters: 工具参数
            
        Yields:
            ToolInvokeMessage: 工具调用消息
        """
        try:
            # 获取凭据
            app_id = self.runtime.credentials.get('app_id')
            app_secret = self.runtime.credentials.get('app_secret')
            
            if not app_id or not app_secret:
                yield self.create_text_message('错误：缺少App ID或App Secret配置')
                return
            
            # 获取参数
            media_type = tool_parameters.get('media_type', '')
            media_url = tool_parameters.get('media_url', '')
            
            # 支持的媒体类型
            valid_types = ['image', 'voice', 'video', 'thumb']
            
            # 参数验证
            if media_type not in valid_types:
                yield self.create_text_message(f'错误：不支持的媒体类型。支持的类型：{valid_types}')
                return
            
            if not media_url:
                yield self.create_text_message('错误：媒体文件URL不能为空')
                return
            
            # 创建微信API客户端
            client = WechatApiClient(app_id, app_secret)
            
            # 从URL下载文件
            logger.info(f'正在从URL下载媒体文件: {media_url}')
            
            try:
                response = requests.get(media_url, stream=True, timeout=30)
                response.raise_for_status()
                file_content = response.content
            except Exception as e:
                yield self.create_text_message(f'下载媒体文件失败: {str(e)}')
                return
            
            # 获取文件名
            content_disposition = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            else:
                # 从URL中提取文件名
                filename = media_url.split('/')[-1].split('?')[0]
                if not filename:
                    filename = f'media.{media_type}'
            
            # 上传到微信服务器
            logger.info(f'正在上传媒体文件: {filename}')
            result = client.upload_media(media_type, file_content=file_content, filename=filename)
            
            # 检查结果
            if 'errcode' in result and result['errcode'] != 0:
                error_msg = f"上传失败: {result.get('errmsg', '未知错误')}"
                logger.error(error_msg)
                yield self.create_text_message(error_msg)
                return
            
            # 构建返回消息
            media_id = result.get('media_id', '')
            expire_time = result.get('expires_in', '')
            
            message = f"媒体文件上传成功！\n"
            message += f"媒体ID: {media_id}\n"
            message += f"媒体类型: {media_type}\n"
            message += f"文件名: {filename}\n"
            message += f"有效期: {expire_time} 秒 (72小时)"
            
            logger.info(f'媒体上传成功，media_id: {media_id}')
            
            yield self.create_text_message(message)
            
        except Exception as e:
            logger.error(f'上传媒体失败: {str(e)}')
            yield self.create_text_message(f'上传媒体失败: {str(e)}')