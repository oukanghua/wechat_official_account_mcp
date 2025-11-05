import logging
from typing import Optional, Any
from .base import MessageHandler
from models import WechatMessage

logger = logging.getLogger(__name__)

class LinkMessageHandler(MessageHandler):
    """微信链接消息处理器"""
    
    def handle(self, message: WechatMessage) -> Optional[str]:
        """
        处理链接消息
        
        Args:
            message: 微信消息对象
            
        Returns:
            回复消息内容（XML格式）
        """
        try:
            # 获取链接信息
            title = getattr(message, 'title', '')
            description = getattr(message, 'description', '')
            url = getattr(message, 'url', '')
            
            logger.info(f'收到链接消息，标题: {title}, 来自用户: {message.from_user_name}')
            
            # 构建链接消息提示文本
            link_info_text = f"收到您分享的链接\n标题: {title}\n描述: {description}\n链接: {url}"
            
            # 调用AI处理链接消息
            ai_reply = self._invoke_ai(message.from_user_name, link_info_text)
            
            # 构建回复XML
            return self._build_reply_text(message.from_user_name, message.to_user_name, ai_reply)
            
        except Exception as e:
            logger.error(f'处理链接消息失败: {str(e)}')
            error_reply = "处理链接消息时发生错误。请稍后重试。"
            return self._build_reply_text(message.from_user_name, message.to_user_name, error_reply)
    
    def handle_message(self, message: WechatMessage, auth_manager: Any) -> str:
        """独立服务器模式下的消息处理方法"""
        try:
            title = getattr(message, 'title', '')
            url = getattr(message, 'url', '')
            logger.info(f"收到链接消息，标题: {title}")
            return f"收到您分享的链接：{title}\n{url}"
        except Exception as e:
            logger.error(f"处理链接消息失败: {str(e)}")
            return "收到您的链接消息"