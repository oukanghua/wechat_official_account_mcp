import logging
from typing import Optional
from .base import MessageHandler
from ..models import WechatMessage

logger = logging.getLogger(__name__)

class VoiceMessageHandler(MessageHandler):
    """微信语音消息处理器"""
    
    def handle(self, message: WechatMessage) -> Optional[str]:
        """
        处理语音消息
        
        Args:
            message: 微信消息对象
            
        Returns:
            回复消息内容（XML格式）
        """
        try:
            # 获取语音信息
            media_id = getattr(message, 'media_id', '')
            format_type = getattr(message, 'format', '')
            recognition = getattr(message, 'recognition', '')
            
            logger.info(f'收到语音消息，format: {format_type}, media_id: {media_id[:10]}..., 来自用户: {message.from_user_name}')
            
            # 构建语音消息提示文本
            voice_info_text = f"收到您发送的语音消息\n语音格式: {format_type}\n"
            
            # 如果有语音识别结果，添加到文本中
            if recognition:
                voice_info_text += f"语音识别结果: {recognition}\n"
            else:
                voice_info_text += "当前没有语音识别结果\n"
            
            # 调用AI处理语音消息
            ai_reply = self._invoke_ai(message.from_user_name, voice_info_text)
            
            # 构建回复XML
            return self._build_reply_text(message.from_user_name, message.to_user_name, ai_reply)
            
        except Exception as e:
            logger.error(f'处理语音消息失败: {str(e)}')
            error_reply = "处理语音消息时发生错误。请稍后重试。"
            return self._build_reply_text(message.from_user_name, message.to_user_name, error_reply)