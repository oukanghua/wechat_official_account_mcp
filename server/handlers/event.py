import logging
from typing import Dict, Any, Optional
from .base import MessageHandler
from shared.models import WechatMessage
from shared.utils.wechat_api_client import WechatApiClient

logger = logging.getLogger(__name__)

class EventMessageHandler(MessageHandler):
    """微信事件消息处理器"""
    
    def handle(self, message: WechatMessage) -> Optional[str]:
        """
        处理事件消息
        
        Args:
            message: 微信消息对象
            
        Returns:
            回复消息内容（XML格式）
        """
        try:
            # 获取事件类型
            event_type = getattr(message, 'event', '')
            logger.info(f'收到事件消息: {event_type} 来自用户: {message.from_user_name}')
            
            # 根据事件类型进行处理
            if event_type == 'subscribe':
                # 处理关注事件
                return self._handle_subscribe(message)
            elif event_type == 'unsubscribe':
                # 处理取消关注事件
                return self._handle_unsubscribe(message)
            elif event_type == 'CLICK':
                # 处理菜单点击事件
                return self._handle_menu_click(message)
            elif event_type == 'VIEW':
                # 处理菜单跳转事件
                return self._handle_menu_view(message)
            else:
                logger.warning(f'未处理的事件类型: {event_type}')
                return None
                
        except Exception as e:
            logger.error(f'处理事件消息失败: {str(e)}')
            return None
    
    def handle_message(self, message: WechatMessage, auth_manager: Any) -> str:
        """独立服务器模式下的消息处理方法"""
        try:
            event_type = getattr(message, 'event', '')
            logger.info(f"收到事件消息: {event_type}")
            
            if event_type == 'subscribe':
                return "欢迎关注！"
            elif event_type == 'unsubscribe':
                return ""  # 取消关注不回复
            else:
                return f"收到事件：{event_type}"
        except Exception as e:
            logger.error(f"处理事件消息失败: {str(e)}")
            return ""
    
    def _handle_subscribe(self, message: WechatMessage) -> Optional[str]:
        """
        处理关注事件
        
        Args:
            message: 微信消息对象
            
        Returns:
            回复消息内容（XML格式）
        """
        try:
            # 获取用户信息
            user_info = self._get_user_info(message.from_user_name)
            
            # 构建欢迎消息
            welcome_text = "欢迎关注！\n\n感谢您关注我们的公众号。\n您可以直接向我发送消息，我会尽快回复您。"
            
            if user_info:
                nickname = user_info.get('nickname', '')
                if nickname:
                    welcome_text = f"欢迎{nickname}！\n\n感谢您关注我们的公众号。\n您可以直接向我发送消息，我会尽快回复您。"
            
            # 记录关注事件
            logger.info(f'用户 {message.from_user_name} 关注了公众号')
            
            # 调用AI生成回复（可选）
            ai_reply = self._invoke_ai(message.from_user_name, welcome_text)
            
            # 构建回复XML
            return self._build_reply_text(message.from_user_name, message.to_user_name, ai_reply)
            
        except Exception as e:
            logger.error(f'处理关注事件失败: {str(e)}')
            # 返回默认欢迎消息
            default_welcome = "欢迎关注我们的公众号！"
            return self._build_reply_text(message.from_user_name, message.to_user_name, default_welcome)
    
    def _handle_unsubscribe(self, message: WechatMessage) -> None:
        """
        处理取消关注事件
        
        Args:
            message: 微信消息对象
        """
        logger.info(f'用户 {message.from_user_name} 取消关注了公众号')
        # 可以在这里进行清理操作，比如删除用户会话记录等
        self._clear_session(message.from_user_name)
        return None
    
    def _handle_menu_click(self, message: WechatMessage) -> Optional[str]:
        """
        处理菜单点击事件
        
        Args:
            message: 微信消息对象
            
        Returns:
            回复消息内容（XML格式）
        """
        try:
            event_key = getattr(message, 'event_key', '')
            logger.info(f'收到菜单点击事件: {event_key} 来自用户: {message.from_user_name}')
            
            # 根据不同的菜单key返回不同的内容
            menu_responses = {
                'MENU_ABOUT': '关于我们\n\n这是一个智能助手，可以回答您的问题，提供各种服务。',
                'MENU_HELP': '使用帮助\n\n1. 直接发送文字消息给我\n2. 点击菜单获取相关服务\n3. 您可以随时提问'
            }
            
            reply_text = menu_responses.get(event_key, f'收到您的菜单点击：{event_key}')
            
            # 调用AI生成回复
            ai_reply = self._invoke_ai(message.from_user_name, reply_text)
            
            return self._build_reply_text(message.from_user_name, message.to_user_name, ai_reply)
            
        except Exception as e:
            logger.error(f'处理菜单点击事件失败: {str(e)}')
            return None
    
    def _handle_menu_view(self, message: WechatMessage) -> None:
        """
        处理菜单跳转事件
        
        Args:
            message: 微信消息对象
        """
        event_key = getattr(message, 'event_key', '')
        logger.info(f'收到菜单跳转事件: {event_key} 来自用户: {message.from_user_name}')
        # 对于VIEW事件，不需要回复消息
        return None
    
    def _get_user_info(self, open_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户信息
        
        Args:
            open_id: 用户的open_id
            
        Returns:
            用户信息字典
        """
        try:
            # 从配置中获取app_id和app_secret
            app_id = self.get_config('app_id')
            app_secret = self.get_config('app_secret')
            
            if not app_id or not app_secret:
                logger.warning('缺少app_id或app_secret配置，无法获取用户信息')
                return None
            
            # 创建微信API客户端
            client = WechatApiClient(app_id, app_secret)
            
            # 调用API获取用户信息
            user_info = client.get_user_info(open_id)
            return user_info
            
        except Exception as e:
            logger.error(f'获取用户信息失败: {str(e)}')
            return None