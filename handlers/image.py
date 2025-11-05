import logging
from typing import Optional, Any
from .base import MessageHandler
from models import WechatMessage

logger = logging.getLogger(__name__)

class ImageMessageHandler(MessageHandler):
    """微信图片消息处理器"""
    
    def handle(self, message: WechatMessage) -> Optional[str]:
        """
        处理图片消息
        
        Args:
            message: 微信消息对象
            
        Returns:
            回复消息内容（XML格式）
        """
        try:
            # 获取图片信息
            pic_url = getattr(message, 'pic_url', '')
            media_id = getattr(message, 'media_id', '')
            
            logger.info(f'收到图片消息，media_id: {media_id}, 来自用户: {message.from_user_name}')
            
            # 构建图片消息提示文本
            image_info_text = f"收到您发送的图片\n图片链接: {pic_url}\n媒体ID: {media_id[:10]}...{media_id[-10:]}"
            
            # 调用AI处理图片消息
            ai_reply = self._invoke_ai(message.from_user_name, image_info_text)
            
            # 构建回复XML
            return self._build_reply_text(message.from_user_name, message.to_user_name, ai_reply)
            
        except Exception as e:
            logger.error(f'处理图片消息失败: {str(e)}')
            error_reply = "处理图片消息时发生错误。请稍后重试。"
            return self._build_reply_text(message.from_user_name, message.to_user_name, error_reply)
    
    def handle_message(self, message: WechatMessage, auth_manager: Any) -> str:
        """独立服务器模式下的消息处理方法"""
        try:
            media_id = getattr(message, 'media_id', '')
            logger.info(f"收到图片消息，media_id: {media_id}")
            return "收到您的图片消息"
        except Exception as e:
            logger.error(f"处理图片消息失败: {str(e)}")
            return "收到您的图片消息"