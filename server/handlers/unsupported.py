import logging
from typing import Optional, Any
from .base import MessageHandler
from shared.models import WechatMessage

logger = logging.getLogger(__name__)

class UnsupportedMessageHandler(MessageHandler):
    """微信不支持消息类型处理器"""
    
    def handle(self, message: WechatMessage) -> Optional[str]:
        """
        处理不支持的消息类型
        
        Args:
            message: 微信消息对象
            
        Returns:
            回复消息内容（XML格式）
        """
        try:
            message_type = getattr(message, 'msg_type', 'unknown')
            logger.warning(f'收到不支持的消息类型: {message_type} 来自用户: {message.from_user_name}')
            
            # 返回不支持消息的提示
            reply_text = f"当前不支持处理{message_type}类型的消息。请尝试发送文本、图片、语音或链接。"
            
            # 构建回复XML
            return self._build_reply_text(message.from_user_name, message.to_user_name, reply_text)
            
        except Exception as e:
            logger.error(f'处理不支持消息类型失败: {str(e)}')
            return None
    
    def handle_message(self, message: WechatMessage, auth_manager: Any) -> str:
        """独立服务器模式下的消息处理方法"""
        try:
            message_type = getattr(message, 'msg_type', 'unknown')
            logger.warning(f'收到不支持的消息类型: {message_type}')
            return f"当前不支持处理{message_type}类型的消息"
        except Exception as e:
            logger.error(f"处理不支持消息失败: {str(e)}")
            return "收到您的消息"