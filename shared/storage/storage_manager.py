"""
存储管理器 - 管理本地素材存储
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class StorageManager:
    """存储管理器"""
    
    def __init__(self, db_file: str = "data/storage.db"):
        """
        初始化存储管理器
        
        Args:
            db_file: 数据库文件路径（使用 JSON 文件存储）
        """
        self.db_file = db_file
        self.data: Dict[str, Any] = {
            'media': []  # 素材列表
        }
        self._load_data()
    
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
            except Exception as e:
                logger.error(f"加载存储数据失败: {e}")
                self.data = {'media': []}
        else:
            self.data = {'media': []}
    
    def _save_data(self):
        """保存数据"""
        db_dir = Path(self.db_file).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存存储数据失败: {e}")
    
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

