from abc import ABC, abstractmethod
from typing import Dict, Any, Generator, Optional
import logging
import time
import hashlib

logger = logging.getLogger(__name__)

class MessageHandler(ABC):
    """消息处理器基类"""
    
    def __init__(self):
        self.retry_count = 0
    
    @abstractmethod
    def handle(self, message: Any, session: Any, app_settings: Dict[str, Any]) -> str:
        """
        处理消息并返回回复内容
        
        Args:
            message: 消息对象
            session: 当前会话对象
            app_settings: 应用设置
            
        Returns:
            str: 回复内容
        """
        pass
    
    def _get_conversation_id(self, session: Any, storage_key: str) -> str:
        """
        获取或创建会话ID
        
        Args:
            session: 会话对象
            storage_key: 存储键
            
        Returns:
            str: 会话ID
        """
        try:
            # 从存储中获取会话ID
            conversation_id = session.storage.get(storage_key)
            
            # 如果不存在，创建新的会话ID
            if not conversation_id:
                conversation_id = hashlib.md5(f"{storage_key}_{time.time()}".encode()).hexdigest()
                session.storage.set(storage_key, conversation_id)
            
            return conversation_id
            
        except Exception as e:
            logger.error(f'获取会话ID失败: {str(e)}')
            # 返回默认会话ID
            return hashlib.md5(f"default_{time.time()}".encode()).hexdigest()
    
    def get_storage_key(self, user_id: str, app_id: str) -> str:
        """
        获取存储键
        
        Args:
            user_id: 用户ID
            app_id: 应用ID
            
        Returns:
            str: 存储键
        """
        return f"wechat_conversation_{app_id}_{user_id}"
    
    def _invoke_ai(self, session: Any, app_settings: Dict[str, Any], query: str, 
                  conversation_id: str, inputs: Dict = None, user_id: str = None) -> Generator:
        """
        调用AI获取响应
        
        Args:
            session: 会话对象
            app_settings: 应用设置
            query: 用户查询
            conversation_id: 会话ID
            inputs: 输入参数
            user_id: 用户ID
            
        Returns:
            Generator: AI响应生成器
        """
        try:
            # 调用Dify应用
            response = session.app.invoke(
                inputs=inputs or {},
                query=query,
                user=user_id or 'wechat_user',
                conversation_id=conversation_id,
                response_mode="streaming"
            )
            
            return response
            
        except Exception as e:
            logger.error(f'调用AI失败: {str(e)}')
            # 返回错误信息
            yield {'answer': f'抱歉，AI处理失败: {str(e)}'}
    
    def _process_ai_response(self, response_generator: Generator) -> str:
        """
        处理AI响应
        
        Args:
            response_generator: 响应生成器
            
        Returns:
            str: 处理后的响应内容
        """
        try:
            answer_parts = []
            
            # 收集所有响应部分
            for chunk in response_generator:
                if 'answer' in chunk:
                    answer_parts.append(chunk['answer'])
            
            # 组合响应
            return ''.join(answer_parts)
            
        except Exception as e:
            logger.error(f'处理AI响应失败: {str(e)}')
            return f'抱歉，处理响应时发生错误: {str(e)}'
    
    def clear_cache(self, session: Any, user_id: str, app_id: str) -> bool:
        """
        清理用户缓存
        
        Args:
            session: 会话对象
            user_id: 用户ID
            app_id: 应用ID
            
        Returns:
            bool: 是否清理成功
        """
        try:
            # 删除会话ID
            storage_key = self.get_storage_key(user_id, app_id)
            session.storage.delete(storage_key)
            
            # 调用应用的清理方法（如果有）
            if hasattr(session.app, 'clear_conversation'):
                # 获取旧会话ID
                old_conversation_id = session.storage.get(storage_key)
                if old_conversation_id:
                    session.app.clear_conversation(old_conversation_id)
            
            logger.info(f'清理用户缓存成功: {user_id}')
            return True
            
        except Exception as e:
            logger.error(f'清理用户缓存失败: {str(e)}')
            return False