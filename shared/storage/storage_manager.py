"""
存储管理器 - 管理素材等数据的本地存储
"""
import sqlite3
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class StorageManager:
    """存储管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化存储管理器
        
        Args:
            db_path: SQLite 数据库路径，默认为 ./data/wechat_mcp.db
        """
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'data',
                'wechat_mcp.db'
            )
        
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_db()
    
    def _ensure_db_dir(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            Path(db_dir).mkdir(parents=True, exist_ok=True)
    
    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_id TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    url TEXT,
                    local_path TEXT
                )
            ''')
            
            conn.commit()
        finally:
            conn.close()
    
    def save_media(self, media_info: Dict[str, Any]) -> bool:
        """
        保存素材信息
        
        Args:
            media_info: 素材信息字典
            
        Returns:
            是否保存成功
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO media 
                (media_id, type, created_at, url, local_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                media_info.get('mediaId') or media_info.get('media_id'),
                media_info.get('type', ''),
                media_info.get('createdAt') or media_info.get('created_at', 0),
                media_info.get('url', ''),
                media_info.get('localPath') or media_info.get('local_path', '')
            ))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f'保存素材信息失败: {str(e)}')
            return False
        finally:
            conn.close()
    
    def get_media(self, media_id: str) -> Optional[Dict[str, Any]]:
        """
        获取素材信息
        
        Args:
            media_id: 素材ID
            
        Returns:
            素材信息字典，如果不存在则返回 None
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT media_id, type, created_at, url, local_path
                FROM media
                WHERE media_id = ?
            ''', (media_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'media_id': row[0],
                    'type': row[1],
                    'created_at': row[2],
                    'url': row[3],
                    'local_path': row[4]
                }
            return None
        finally:
            conn.close()

