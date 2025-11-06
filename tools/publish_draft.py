from typing import Dict, Any, Generator
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from ..utils.wechat_api_client import WechatApiClient
import logging

logger = logging.getLogger(__name__)

class PublishDraftTool(Tool):
    """发布微信公众号草稿工具"""
    
    def _invoke(self, tool_parameters: Dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """
        调用发布草稿工具
        
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
            media_id = tool_parameters.get('media_id', '')
            to_group = tool_parameters.get('to_group')
            to_tag = tool_parameters.get('to_tag')
            
            # 参数验证
            if not media_id:
                yield self.create_text_message('错误：草稿ID不能为空')
                return
            
            # 创建微信API客户端
            client = WechatApiClient(app_id, app_secret)
            
            # 调用API发布草稿
            result = client.publish_draft(media_id, to_group, to_tag)
            
            # 检查发布结果
            if 'errcode' in result and result['errcode'] != 0:
                error_msg = f"发布失败: {result.get('errmsg', '未知错误')}"
                logger.error(error_msg)
                yield self.create_text_message(error_msg)
                return
            
            # 构建返回消息
            publish_id = result.get('publish_id', '')
            message = f"草稿发布成功！\n"
            message += f"草稿ID: {media_id}\n"
            message += f"发布任务ID: {publish_id}\n"
            message += "文章将在审核通过后发布到公众号"
            
            if to_group:
                message += f"\n分组ID: {to_group}"
            elif to_tag:
                message += f"\n标签ID: {to_tag}"
            
            logger.info(f'成功发布草稿: {media_id}, 发布任务ID: {publish_id}')
            
            yield self.create_text_message(message)
            
        except Exception as e:
            logger.error(f'发布草稿失败: {str(e)}')
            yield self.create_text_message(f'发布草稿失败: {str(e)}')