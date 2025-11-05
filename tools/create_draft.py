import json
from typing import Dict, Any, Generator
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from ..utils.wechat_api_client import WechatApiClient
import logging

logger = logging.getLogger(__name__)

class CreateDraftTool(Tool):
    """创建图文消息草稿工具"""
    
    def _invoke(self, tool_parameters: Dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """
        调用创建草稿工具
        
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
            title = tool_parameters.get('title', '')
            content = tool_parameters.get('content', '')
            author = tool_parameters.get('author', '')
            digest = tool_parameters.get('digest', '')
            thumb_media_id = tool_parameters.get('thumb_media_id', '')
            content_source_url = tool_parameters.get('content_source_url', '')
            need_open_comment = int(tool_parameters.get('need_open_comment', '0'))
            only_fans_can_comment = int(tool_parameters.get('only_fans_can_comment', '0'))
            
            # 参数验证
            validation_errors = []
            
            if not title:
                validation_errors.append('文章标题不能为空')
            elif len(title) > 64:
                validation_errors.append(f'标题过长：{len(title)}/64字符，请缩短标题')
            
            if not content:
                validation_errors.append('文章内容不能为空')
            
            if author and len(author) > 8:
                validation_errors.append(f'作者名过长：{len(author)}/8字符，请缩短作者名')
            
            if digest and len(digest) > 120:
                validation_errors.append(f'摘要过长：{len(digest)}/120字符，请缩短摘要')
            
            if not thumb_media_id:
                validation_errors.append('封面图片media_id不能为空')
            elif len(thumb_media_id) < 10:
                validation_errors.append('封面图片media_id格式可能不正确，长度过短')
            
            # 检查内容中的潜在问题
            if '<script' in content.lower() or '<iframe' in content.lower():
                validation_errors.append('内容包含可能不被允许的HTML标签（script/iframe）')
            
            if validation_errors:
                error_msg = "参数验证失败：\n\n" + "\n".join(validation_errors)
                error_msg += "\n\n请修正以上问题后重试"
                yield self.create_text_message(error_msg)
                return
            
            # 创建微信API客户端
            client = WechatApiClient(app_id, app_secret)
            
            # 构建文章数据
            article = {
                "title": title,
                "author": author,
                "digest": digest,
                "content": content,
                "content_source_url": content_source_url,
                "thumb_media_id": thumb_media_id,
                "show_cover_pic": 1,  # 默认显示封面
                "need_open_comment": need_open_comment,
                "only_fans_can_comment": only_fans_can_comment
            }
            
            # 调用API创建草稿
            logger.info(f'正在创建图文草稿: {title}')
            result = client.add_draft(article)
            
            # 检查结果
            if 'errcode' in result and result['errcode'] != 0:
                error_msg = f"创建草稿失败: {result.get('errmsg', '未知错误')}"
                logger.error(error_msg)
                yield self.create_text_message(error_msg)
                return
            
            logger.info(f'成功创建草稿: {result.get("media_id")}')
            
            yield self.create_text_message(
                f"草稿创建成功！\n" +
                f"草稿ID: {result.get('media_id')}\n" +
                f"标题: {title}\n" +
                f"作者: {author or '未设置'}\n" +
                f"摘要: {digest or '未设置'}\n" +
                f"封面图片ID: {thumb_media_id}"
            )
            
        except Exception as e:
            logger.error(f'创建草稿失败: {str(e)}')
            yield self.create_text_message(f'创建草稿失败: {str(e)}')