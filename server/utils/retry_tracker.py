"""
消息状态跟踪器
用于跟踪消息处理状态和重试机制
"""
import logging
import threading
import time
from typing import Dict, Any, Optional, Union

from shared.models import WechatMessage

logger = logging.getLogger(__name__)


class MessageStatusTracker:
    """
    消息状态跟踪器
    用于跟踪消息处理状态和重试机制
    """
    # 类变量，用于存储所有正在处理的消息
    _messages: Dict[str, Dict[str, Any]] = {}
    
    # 字典操作锁
    _messages_lock = threading.Lock()
    
    # 清理线程标志
    _cleanup_thread_started = False
    
    @classmethod
    def track_message(cls, message: Union[WechatMessage, str]) -> Dict[str, Any]:
        """
        跟踪消息，如果消息已存在，更新重试次数并返回其状态，否则创建新状态
        
        Args:
            message: WechatMessage 对象或消息 ID 字符串
            
        Returns:
            消息的状态字典
        """
        tracking_id = cls._get_tracking_id(message)
        if not tracking_id:
            return cls._create_temp_status()
        
        with cls._messages_lock:
            # 检查消息是否已存在
            if tracking_id in cls._messages:
                # 增加重试次数
                cls._messages[tracking_id]['retry_count'] = cls._messages[tracking_id].get('retry_count', 0) + 1
                retry_count = cls._messages[tracking_id]['retry_count']
                logger.info(f"检测到重试请求: {tracking_id}, 当前重试次数: {retry_count}")
                return cls._messages[tracking_id]
            
            # 新消息，创建状态
            status = cls._create_status()
            cls._messages[tracking_id] = status
            
            # 启动清理线程（如果未启动）
            cls._ensure_cleanup_thread()
            
            return status
    
    @classmethod
    def update_status(cls, message: Union[WechatMessage, str], result: Optional[str] = None, 
                     is_completed: bool = False, error: Optional[str] = None) -> None:
        """
        更新消息的处理状态
        
        Args:
            message: WechatMessage 对象或消息 ID 字符串
            result: 处理结果
            is_completed: 是否已完成处理
            error: 错误信息
        """
        tracking_id = cls._get_tracking_id(message)
        if not tracking_id:
            return
        
        with cls._messages_lock:
            if tracking_id not in cls._messages:
                cls._messages[tracking_id] = cls._create_status()
            
            status = cls._messages[tracking_id]
            
            # 使用消息独立锁更新状态
            with status['lock']:
                # 更新状态
                if result is not None:
                    status['result'] = result
                
                if error is not None:
                    status['error'] = error
                
                if is_completed:
                    status['is_completed'] = True
                    # 设置完成事件
                    if 'completion_event' in status and not status['completion_event'].is_set():
                        status['completion_event'].set()
    
    @classmethod
    def mark_result_returned(cls, message: Union[WechatMessage, str]) -> bool:
        """
        原子操作：标记结果已返回
        如果结果已被标记为已返回，返回 False
        如果成功标记，返回 True
        
        Args:
            message: WechatMessage 对象或消息 ID 字符串
        """
        tracking_id = cls._get_tracking_id(message)
        if not tracking_id:
            return False
        
        with cls._messages_lock:
            if tracking_id not in cls._messages:
                return False
            
            status = cls._messages[tracking_id]
            
            # 使用消息独立锁更新状态
            with status['lock']:
                if status.get('result_returned', False):
                    logger.debug(f"结果已被标记为已返回，跳过处理: {tracking_id}")
                    return False
                
                status['result_returned'] = True
                return True
    
    @classmethod
    def get_status(cls, message: Union[WechatMessage, str]) -> Optional[Dict[str, Any]]:
        """
        获取消息的处理状态
        
        Args:
            message: WechatMessage 对象或消息 ID 字符串
        """
        tracking_id = cls._get_tracking_id(message)
        if not tracking_id:
            return None
        
        with cls._messages_lock:
            if tracking_id not in cls._messages:
                return None
            
            # 返回状态浅拷贝，排除锁对象
            return {k: v for k, v in cls._messages[tracking_id].items() 
                   if k not in ('lock', 'completion_event')}
    
    @classmethod
    def _get_tracking_id(cls, message: Union[WechatMessage, str]) -> Optional[str]:
        """
        根据消息类型获取跟踪 ID
        
        Args:
            message: WechatMessage 对象或消息 ID 字符串
            
        Returns:
            跟踪 ID 或 None
        """
        if isinstance(message, str):
            return message
        
        # 如果是 WechatMessage 对象
        if hasattr(message, 'msg_type'):
            # 对于事件消息，使用 from_user + event + create_time 作为标识符
            if message.msg_type == 'event':
                tracking_id = f"{message.from_user}_{message.event}_{message.create_time}"
                logger.debug(f"事件消息使用自定义标识符: {tracking_id}")
                return tracking_id
            # 对于普通消息，使用 msg_id
            elif hasattr(message, 'msg_id') and message.msg_id:
                return message.msg_id
        
        logger.warning(f"无法获取消息的跟踪 ID: {message}")
        return None
    
    @classmethod
    def _create_status(cls) -> Dict[str, Any]:
        """创建新的状态对象"""
        return {
            'result': None,
            'is_completed': False,
            'error': None,
            'start_time': time.time(),
            'completion_event': threading.Event(),
            'retry_count': 0,
            'result_returned': False,  # 标记结果是否已发送
            'lock': threading.Lock(),   # 每个消息独立的锁
        }
    
    @classmethod
    def _create_temp_status(cls) -> Dict[str, Any]:
        """创建临时状态对象（不跟踪）"""
        return cls._create_status()
    
    @classmethod
    def _ensure_cleanup_thread(cls) -> None:
        """确保清理线程已启动"""
        if not hasattr(cls, '_cleanup_thread_started') or not cls._cleanup_thread_started:
            cls._cleanup_thread_started = True
            thread = threading.Thread(
                target=cls._cleanup_expired_messages,
                daemon=True,
                name="MessageCleanupThread"
            )
            thread.start()
    
    @classmethod
    def _cleanup_expired_messages(cls) -> None:
        """定期清理过期的消息"""
        try:
            while True:
                # 每 60 秒清理一次
                time.sleep(60)
                
                with cls._messages_lock:
                    now = time.time()
                    # 清理已完成超过 10 分钟的消息
                    expired_keys = [
                        msg_id for msg_id, status in cls._messages.items()
                        if status.get('is_completed', False) and 
                           now - status.get('start_time', now) > 600  # 10 分钟
                    ]
                    
                    # 删除过期的消息
                    for msg_id in expired_keys:
                        cls._messages.pop(msg_id, None)
                    
                    if expired_keys:
                        logger.info(f"清理了 {len(expired_keys)} 个过期的消息，剩余消息: {len(cls._messages)}")
        except Exception as e:
            logger.error(f"消息清理线程异常退出: {str(e)}")
            cls._cleanup_thread_started = False


