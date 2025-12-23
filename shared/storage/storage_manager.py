"""
存储管理器 - 管理本地素材存储，支持S3兼容存储服务
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


class StorageManager:
    """存储管理器 - 支持本地存储和S3兼容存储"""
    
    def __init__(self, db_file: str = "data/storage.db"):
        """
        初始化存储管理器
        
        Args:
            db_file: 数据库文件路径（使用 JSON 文件存储）
        """
        self.db_file = db_file
        self.data: Dict[str, Any] = {
            'media': [],  # 素材列表
            'static_pages': [],  # 静态网页列表
            'wechat_messages': []  # 微信消息列表
        }
        
        # 初始化S3相关配置
        self._init_s3_config()
        
        # 加载数据
        self._load_data()
        
        # 启动定时同步（如果配置了）
        self._start_scheduled_sync()
    
    def _init_s3_config(self):
        """初始化S3相关配置"""
        # 远程存储开关
        self.remote_enabled = os.getenv('STORAGE_REMOTE_ENABLE', 'false').lower() == 'true'
        
        # S3配置
        self.s3_endpoint_url = os.getenv('STORAGE_S3_ENDPOINT', '')
        self.s3_access_key = os.getenv('STORAGE_S3_ACCESS_KEY', '')
        self.s3_secret_key = os.getenv('STORAGE_S3_SECRET_KEY', '')
        self.s3_bucket_name = os.getenv('STORAGE_S3_BUCKET', '')
        self.s3_region_name = os.getenv('STORAGE_S3_REGION', '')
        self.s3_path_prefix = os.getenv('STORAGE_S3_PATH_PREFIX', '')
        
        # 定时同步配置
        self.sync_cron = os.getenv('STORAGE_SYN_CRON', '')
        self.sync_override = os.getenv('STORAGE_SYN_OVERRIDE', 'false').lower() == 'true'
        
        # 初始化S3客户端（如果启用了远程存储）
        self.s3_client = None
        if self.remote_enabled:
            self._init_s3_client()
    
    def _init_s3_client(self):
        """初始化S3客户端"""
        try:
            import boto3
            from botocore.config import Config
            
            # 创建S3客户端配置
            s3_config = Config(
                region_name=self.s3_region_name,
                signature_version='s3v4',
                retries={
                    'max_attempts': 3,
                    'mode': 'standard'
                }
            )
            
            # 初始化S3客户端
            self.s3_client = boto3.client(
                's3',
                endpoint_url=self.s3_endpoint_url,
                aws_access_key_id=self.s3_access_key,
                aws_secret_access_key=self.s3_secret_key,
                config=s3_config
            )
            
            # 检查桶是否存在
            self.s3_client.head_bucket(Bucket=self.s3_bucket_name)
            logger.info(f"S3客户端初始化成功，桶: {self.s3_bucket_name}")
        except Exception as e:
            logger.error(f"S3客户端初始化失败: {e}")
            self.s3_client = None
            self.remote_enabled = False
    
    def _start_scheduled_sync(self):
        """启动定时同步任务"""
        if not self.remote_enabled or not self.sync_cron:
            return
        
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            
            # 创建调度器
            self.scheduler = BackgroundScheduler()
            
            # 添加定时任务
            self.scheduler.add_job(
                self.sync_from_remote,
                trigger=CronTrigger.from_crontab(self.sync_cron),
                id='remote_sync_job',
                name='Remote Storage Sync',
                replace_existing=True
            )
            
            # 启动调度器
            self.scheduler.start()
            logger.info(f"定时同步任务已启动，Cron表达式: {self.sync_cron}")
        except Exception as e:
            logger.error(f"启动定时同步任务失败: {e}")
    
    def _load_data(self):
        """加载数据"""
        db_dir = Path(self.db_file).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                if 'media' not in self.data:
                    self.data['media'] = []
                if 'static_pages' not in self.data:
                    self.data['static_pages'] = []
                if 'wechat_messages' not in self.data:
                    self.data['wechat_messages'] = []
            except Exception as e:
                logger.error(f"加载存储数据失败: {e}")
                self.data = {'media': [], 'static_pages': []}
        else:
            self.data = {'media': [], 'static_pages': []}
    
    def _save_data(self):
        """保存数据"""
        db_dir = Path(self.db_file).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            
            # 如果启用了远程存储，将数据文件同步到S3
            if self.remote_enabled and self.s3_client:
                self._upload_to_s3(self.db_file, self._get_s3_key(self.db_file))
        except Exception as e:
            logger.error(f"保存存储数据失败: {e}")
    
    def _get_s3_key(self, file_path: str) -> str:
        """获取S3存储的键名"""
        relative_path = os.path.relpath(file_path, os.getcwd())
        key_parts = []
        if self.s3_path_prefix:
            key_parts.append(self.s3_path_prefix)
        key_parts.append(relative_path.replace('\\', '/'))
        return '/'.join(key_parts)
    
    def _upload_to_s3(self, file_path: str, s3_key: str) -> bool:
        """上传文件到S3存储"""
        if not self.s3_client or not os.path.exists(file_path):
            return False
        
        try:
            self.s3_client.upload_file(
                Filename=file_path,
                Bucket=self.s3_bucket_name,
                Key=s3_key
            )
            logger.info(f"文件上传到S3成功: {s3_key}")
            return True
        except Exception as e:
            logger.error(f"文件上传到S3失败: {s3_key}, 错误: {e}")
            return False
    
    def _download_from_s3(self, s3_key: str, file_path: str) -> bool:
        """从S3存储下载文件"""
        if not self.s3_client:
            return False
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            self.s3_client.download_file(
                Bucket=self.s3_bucket_name,
                Key=s3_key,
                Filename=file_path
            )
            logger.info(f"从S3下载文件成功: {s3_key} -> {file_path}")
            return True
        except Exception as e:
            logger.error(f"从S3下载文件失败: {s3_key}, 错误: {e}")
            return False
    
    def _delete_from_s3(self, s3_key: str) -> bool:
        """从S3存储删除文件"""
        if not self.s3_client:
            return False
        
        try:
            self.s3_client.delete_object(
                Bucket=self.s3_bucket_name,
                Key=s3_key
            )
            logger.info(f"从S3删除文件成功: {s3_key}")
            return True
        except Exception as e:
            logger.error(f"从S3删除文件失败: {s3_key}, 错误: {e}")
            return False
    
    def _list_s3_objects(self, prefix: str = '') -> List[str]:
        """列出S3存储中的对象"""
        if not self.s3_client:
            return []
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket_name,
                Prefix=prefix
            )
            
            objects = []
            if 'Contents' in response:
                objects = [obj['Key'] for obj in response['Contents']]
            
            logger.info(f"从S3列出对象成功，找到 {len(objects)} 个对象")
            return objects
        except Exception as e:
            logger.error(f"从S3列出对象失败: {e}")
            return []
    
    def _get_s3_object_info(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """获取S3对象的元信息"""
        if not self.s3_client:
            return None
        
        try:
            response = self.s3_client.head_object(
                Bucket=self.s3_bucket_name,
                Key=s3_key
            )
            
            return {
                'last_modified': response['LastModified'],
                'content_length': response['ContentLength'],
                'content_type': response.get('ContentType', '')
            }
        except Exception as e:
            logger.error(f"获取S3对象信息失败: {s3_key}, 错误: {e}")
            return None
    
    def sync_from_remote(self) -> Dict[str, Any]:
        """从远程S3存储同步文件到本地"""
        if not self.remote_enabled or not self.s3_client:
            return {'status': 'error', 'message': '远程存储未启用'}
        
        try:
            # 列出S3中的所有对象
            s3_objects = self._list_s3_objects(self.s3_path_prefix)
            
            sync_count = 0
            override_count = 0
            
            for s3_key in s3_objects:
                # 过滤掉不需要同步的对象（如隐藏文件）
                if s3_key.endswith('/'):  # 跳过目录
                    continue
                if s3_key.startswith('.'):  # 跳过隐藏文件
                    continue
                
                # 计算本地文件路径
                relative_key = s3_key.replace(self.s3_path_prefix, '') if self.s3_path_prefix else s3_key
                local_file_path = os.path.join(os.getcwd(), relative_key.lstrip('/'))
                
                # 确保目标目录存在
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                
                # 检查本地文件是否存在
                if os.path.exists(local_file_path):
                    if self.sync_override:
                        # 获取文件的修改时间
                        local_mtime = datetime.fromtimestamp(os.path.getmtime(local_file_path))
                        # 将local_mtime转换为带时区的datetime对象（UTC）
                        from datetime import timezone
                        local_mtime = local_mtime.replace(tzinfo=timezone.utc)
                        s3_obj_info = self._get_s3_object_info(s3_key)
                        
                        if s3_obj_info and s3_obj_info['last_modified'] > local_mtime:
                            # S3文件更新，覆盖本地文件
                            if self._download_from_s3(s3_key, local_file_path):
                                sync_count += 1
                                override_count += 1
                                logger.info(f"同步并覆盖本地文件: {local_file_path}")
                    else:
                        logger.info(f"本地文件已存在，跳过同步: {local_file_path}")
                else:
                    # 本地文件不存在，下载
                    if self._download_from_s3(s3_key, local_file_path):
                        sync_count += 1
                        logger.info(f"从S3下载新文件: {local_file_path}")
            
            # 重新加载数据
            self._load_data()
            
            return {
                'status': 'success',
                'message': f'同步完成',
                'sync_count': sync_count,
                'override_count': override_count,
                'total_objects': len(s3_objects)
            }
        except Exception as e:
            logger.error(f"从远程同步文件失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def sync_to_remote(self) -> Dict[str, Any]:
        """将本地文件同步到远程S3存储"""
        if not self.remote_enabled or not self.s3_client:
            return {'status': 'error', 'message': '远程存储未启用'}
        
        try:
            sync_count = 0
            
            # 同步整个data目录
            data_dir = os.path.join(os.getcwd(), 'data')
            
            # 遍历data目录下的所有文件
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    # 跳过隐藏文件
                    if file.startswith('.'):
                        continue
                    
                    # 构建本地文件路径
                    local_file_path = os.path.join(root, file)
                    
                    # 生成S3键名
                    s3_key = self._get_s3_key(local_file_path)
                    
                    # 上传文件到S3
                    if self._upload_to_s3(local_file_path, s3_key):
                        sync_count += 1
            
            return {
                'status': 'success',
                'message': '同步到远程成功',
                'sync_count': sync_count
            }
        except Exception as e:
            logger.error(f"同步到远程失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def save_media(self, media_info: Dict[str, Any]):
        """
        保存素材信息
        
        Args:
            media_info: 素材信息字典，包含 media_id, type, created_at, url 等
        """
        media_id = media_info.get('media_id')
        if not media_id:
            logger.warning("素材信息缺少 media_id，跳过保存")
            return
        
        # 检查是否已存在
        existing_index = None
        for i, media in enumerate(self.data['media']):
            if media.get('media_id') == media_id:
                existing_index = i
                break
        
        if existing_index is not None:
            # 更新现有记录
            self.data['media'][existing_index].update(media_info)
            logger.info(f"更新素材信息: {media_id}")
        else:
            # 添加新记录
            self.data['media'].append(media_info)
            logger.info(f"保存素材信息: {media_id}")
        
        self._save_data()
    
    def get_media(self, media_id: str) -> Optional[Dict[str, Any]]:
        """
        获取素材信息
        
        Args:
            media_id: 素材ID
            
        Returns:
            素材信息字典，如果不存在则返回 None
        """
        # 每次都重新从文件加载数据，确保获取最新内容
        self._load_data()
        for media in self.data['media']:
            if media.get('media_id') == media_id:
                return media
        return None
    
    def list_media(self, media_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出素材
        
        Args:
            media_type: 素材类型过滤（可选）
            
        Returns:
            素材列表
        """
        # 每次都重新从文件加载数据，确保获取最新内容
        self._load_data()
        if media_type:
            return [m for m in self.data['media'] if m.get('type') == media_type]
        return self.data['media'].copy()
    
    def delete_media(self, media_id: str) -> bool:
        """
        删除素材信息
        
        Args:
            media_id: 素材ID
            
        Returns:
            是否删除成功
        """
        for i, media in enumerate(self.data['media']):
            if media.get('media_id') == media_id:
                del self.data['media'][i]
                self._save_data()
                logger.info(f"删除素材信息: {media_id}")
                return True
        return False

    # ========== 微信消息管理方法 ==========

    def save_wechat_message(self, message_info: Dict[str, Any]):
        """
        保存微信消息信息
        
        Args:
            message_info: 微信消息信息字典，包含 from_user, to_user, msg_type, content 等
        """
        # 使用时间戳作为唯一标识
        import time
        message_id = str(int(time.time() * 1000))
        message_info['message_id'] = message_id
        
        # 添加到消息列表开头（最新的在前面）
        self.data['wechat_messages'].insert(0, message_info)
        
        # 限制消息数量，避免文件过大（保留最近1000条）
        if len(self.data['wechat_messages']) > 1000:
            self.data['wechat_messages'] = self.data['wechat_messages'][:1000]
        
        logger.info(f"保存微信消息: {message_id}")
        self._save_data()

    def get_wechat_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        获取微信消息信息
        
        Args:
            message_id: 消息ID
            
        Returns:
            微信消息信息字典，如果不存在则返回 None
        """
        # 每次都重新从文件加载数据，确保获取最新内容
        self._load_data()
        for message in self.data['wechat_messages']:
            if message.get('message_id') == message_id:
                return message
        return None

    def list_wechat_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        列出微信消息
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            微信消息列表
        """
        # 每次都重新从文件加载数据，确保获取最新内容
        self._load_data()
        return self.data['wechat_messages'][:limit]

    def delete_wechat_message(self, message_id: str) -> bool:
        """
        删除微信消息信息
        
        Args:
            message_id: 消息ID
            
        Returns:
            是否删除成功
        """
        for i, message in enumerate(self.data['wechat_messages']):
            if message.get('message_id') == message_id:
                del self.data['wechat_messages'][i]
                self._save_data()
                logger.info(f"删除微信消息: {message_id}")
                return True
        return False

    def clear_wechat_messages(self) -> bool:
        """
        清空所有微信消息
        
        Returns:
            是否清空成功
        """
        try:
            self.data['wechat_messages'] = []
            self._save_data()
            logger.info("清空所有微信消息")
            return True
        except Exception as e:
            logger.error(f"清空微信消息失败: {e}")
            return False

    # ========== 静态网页管理方法 ==========

    def save_static_page(self, page_info: Dict[str, Any]):
        """
        保存静态网页信息
        
        Args:
            page_info: 静态网页信息字典，包含 filename, filepath, created_at 等
        """
        filename = page_info.get('filename')
        if not filename:
            logger.warning("静态网页信息缺少 filename，跳过保存")
            return

        # 检查是否已存在
        existing_index = None
        for i, page in enumerate(self.data['static_pages']):
            if page.get('filename') == filename:
                existing_index = i
                break

        if existing_index is not None:
            # 更新现有记录
            self.data['static_pages'][existing_index].update(page_info)
            logger.info(f"更新静态网页信息: {filename}")
        else:
            # 添加新记录
            self.data['static_pages'].append(page_info)
            logger.info(f"保存静态网页信息: {filename}")

        self._save_data()
        
        # 如果启用了远程存储，将静态页面文件同步到S3
        if self.remote_enabled and self.s3_client:
            filepath = page_info.get('filepath')
            if filepath and os.path.exists(filepath):
                s3_key = self._get_s3_key(filepath)
                self._upload_to_s3(filepath, s3_key)

    def get_static_page(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        获取静态网页信息
        
        Args:
            filename: 文件名
            
        Returns:
            静态网页信息字典，如果不存在则返回 None
        """
        # 每次都重新从文件加载数据，确保获取最新内容
        self._load_data()
        for page in self.data['static_pages']:
            if page.get('filename') == filename:
                return page
        return None

    def list_static_pages(self) -> List[Dict[str, Any]]:
        """
        列出所有静态网页
        
        Returns:
            静态网页列表
        """
        # 每次都重新从文件加载数据，确保获取最新内容
        self._load_data()
        return self.data['static_pages'].copy()

    def delete_static_page(self, filename: str) -> bool:
        """
        删除静态网页信息
        
        Args:
            filename: 文件名
            
        Returns:
            是否删除成功
        """
        for i, page in enumerate(self.data['static_pages']):
            if page.get('filename') == filename:
                # 获取文件路径
                filepath = page.get('filepath')
                
                # 删除本地文件
                if filepath and os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                        logger.info(f"删除本地静态网页文件: {filepath}")
                    except Exception as e:
                        logger.error(f"删除本地静态网页文件失败: {filepath}, 错误: {e}")
                
                # 如果启用了远程存储，从S3删除文件
                if self.remote_enabled and self.s3_client:
                    if filepath:
                        s3_key = self._get_s3_key(filepath)
                        self._delete_from_s3(s3_key)
                    else:
                        # 如果没有filepath，构建默认路径
                        default_filepath = os.path.join(os.getcwd(), 'data', 'static_pages', filename)
                        s3_key = self._get_s3_key(default_filepath)
                        self._delete_from_s3(s3_key)
                
                # 删除记录并保存数据
                del self.data['static_pages'][i]
                self._save_data()
                logger.info(f"删除静态网页信息: {filename}")
                return True
        return False
        
    def get_static_storage_stats(self) -> Dict[str, Any]:
        """
        获取静态存储统计信息
        
        Returns:
            包含文件数量、总大小、最早创建时间、最新创建时间的字典
        """
        # 每次都重新从文件加载数据，确保获取最新内容
        self._load_data()
        pages = self.data['static_pages']
        total_files = len(pages)
        
        if total_files == 0:
            return {
                'total_files': 0,
                'total_size': 0,
                'earliest_created': None,
                'latest_created': None
            }
        
        # 计算总文件大小
        total_size = sum(page.get('file_size', 0) for page in pages)
        
        # 计算最早和最新创建时间
        created_times = [page.get('created_at', '') for page in pages if page.get('created_at')]
        created_times.sort()
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'earliest_created': created_times[0] if created_times else None,
            'latest_created': created_times[-1] if created_times else None
        }

