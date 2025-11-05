import logging
import traceback
from typing import Dict, Any
from .base import MessageHandler
from models import WechatMessage

logger = logging.getLogger(__name__)

class TextMessageHandler(MessageHandler):
    """文本消息处理器"""
    
    def handle(self, message: WechatMessage, session: Any, app_settings: Dict[str, Any]) -> str:
        """
        处理文本消息并返回回复内容
        
        Args:
            message: 微信文本消息对象
            session: 当前会话对象
            app_settings: 应用设置
            
        Returns:
            str: 处理后的回复内容
        """
        try:
            # 记录处理开始
            logger.info(f"开始处理用户文本消息: '{message.content[:50]}...'")
            
            # 获取会话ID
            conversation_id = self._get_conversation_id(
                session, 
                self.get_storage_key(message.from_user, app_settings.get("app").get("app_id"))
            )
            
            # 构建输入参数
            inputs = {
                "msgId": message.msg_id,
                "msgType": message.msg_type,
                "fromUser": message.from_user,
                "media_id": message.media_id,
                "createTime": message.create_time,
                "content": message.content
            }
            
            # 调用AI获取响应
            response_generator = self._invoke_ai(
                session, 
                app_settings, 
                message.content, 
                conversation_id,
                inputs=inputs,
                user_id=message.from_user
            )
            
            # 处理AI响应
            answer = self._process_ai_response(response_generator)
            
            logger.info(f"处理完成，响应长度: {len(answer)}")
            
            return answer
            
        except Exception as e:
            logger.error(f"处理文本消息失败: {str(e)}")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"异常堆栈: {traceback.format_exc()}")
            return f"抱歉，处理您的消息时出现问题: {str(e)}"
    
    def handle_message(self, message: WechatMessage, auth_manager: Any) -> str:
        """
        独立服务器模式下的消息处理方法（支持 Dify AI 集成）
        
        Args:
            message: 微信消息对象
            auth_manager: 认证管理器
            
        Returns:
            str: 回复内容
        """
        try:
            logger.info(f"收到文本消息: {message.content[:50]}")
            
            # 尝试使用 Dify AI（如果配置了）
            try:
                from utils.dify_api_client import get_dify_client
                dify_client = get_dify_client()
                
                if dify_client:
                    import os
                    from dotenv import load_dotenv
                    load_dotenv()
                    
                    app_id = os.getenv('DIFY_APP_ID', '')
                    if app_id:
                        # 调用 Dify API
                        response_generator = dify_client.chat(
                            app_id=app_id,
                            query=message.content,
                            user=message.from_user
                        )
                        
                        # 处理响应
                        answer_parts = []
                        for chunk in response_generator:
                            if isinstance(chunk, dict):
                                if 'answer' in chunk:
                                    answer_parts.append(chunk['answer'])
                                elif chunk.get('event') == 'message_end':
                                    break
                        
                        if answer_parts:
                            answer = ''.join(answer_parts)
                            logger.info(f"Dify AI 响应成功，长度: {len(answer)}")
                            return answer
            except ImportError:
                logger.debug("Dify API 客户端未配置，使用默认回复")
            except Exception as e:
                logger.warning(f"Dify AI 调用失败: {str(e)}，使用默认回复")
            
            # 默认处理：直接回复收到的内容
            return f"收到您的消息: {message.content}"
        except Exception as e:
            logger.error(f"处理消息失败: {str(e)}")
            return "收到您的消息"