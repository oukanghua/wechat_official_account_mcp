"""
认证管理器 - 管理微信公众号的认证配置和 Access Token
"""
import json
import time
import logging
import os
import sqlite3
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class AuthManager:
    """认证管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化认证管理器
        
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
                CREATE TABLE IF NOT EXISTS wechat_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_id TEXT NOT NULL UNIQUE,
                    app_secret TEXT NOT NULL,
                    token TEXT,
                    encoding_aes_key TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS access_token (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_id TEXT NOT NULL UNIQUE,
                    access_token TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY (app_id) REFERENCES wechat_config(app_id)
                )
            ''')
            
            conn.commit()
        finally:
            conn.close()
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        设置微信公众号配置
        
        Args:
            config: 配置字典，包含 app_id, app_secret, token, encoding_aes_key
        """
        app_id = config.get('appId') or config.get('app_id')
        app_secret = config.get('appSecret') or config.get('app_secret')
        token = config.get('token', '')
        encoding_aes_key = config.get('encodingAESKey') or config.get('encoding_aes_key', '')
        
        if not app_id or not app_secret:
            raise ValueError('app_id 和 app_secret 是必需的')
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            now = int(time.time())
            
            cursor.execute('''
                INSERT OR REPLACE INTO wechat_config 
                (app_id, app_secret, token, encoding_aes_key, created_at, updated_at)
                VALUES (?, ?, ?, ?, 
                    COALESCE((SELECT created_at FROM wechat_config WHERE app_id = ?), ?),
                    ?)
            ''', (app_id, app_secret, token, encoding_aes_key, app_id, now, now))
            
            conn.commit()
            logger.info(f'配置已保存: app_id={app_id}')
        finally:
            conn.close()
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """
        获取当前配置
        
        Returns:
            配置字典，如果不存在则返回 None
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT app_id, app_secret, token, encoding_aes_key
                FROM wechat_config
                ORDER BY updated_at DESC
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            if row:
                return {
                    'app_id': row[0],
                    'app_secret': row[1],
                    'token': row[2] or '',
                    'encoding_aes_key': row[3] or ''
                }
            return None
        finally:
            conn.close()
    
    async def get_access_token(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        获取 Access Token
        
        Args:
            force_refresh: 是否强制刷新
            
        Returns:
            包含 access_token 和 expires_at 的字典
        """
        config = self.get_config()
        if not config:
            raise ValueError('请先配置微信公众号信息')
        
        app_id = config['app_id']
        
        # 检查缓存
        if not force_refresh:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT access_token, expires_at
                    FROM access_token
                    WHERE app_id = ? AND expires_at > ?
                ''', (app_id, int(time.time())))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'accessToken': row[0],
                        'expiresAt': row[1] * 1000  # 转换为毫秒
                    }
            finally:
                conn.close()
        
        # 刷新 token
        return await self.refresh_access_token()
    
    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        刷新 Access Token
        
        Returns:
            包含 access_token 和 expires_at 的字典
        """
        config = self.get_config()
        if not config:
            raise ValueError('请先配置微信公众号信息')
        
        import requests
        
        app_id = config['app_id']
        app_secret = config['app_secret']
        
        url = 'https://api.weixin.qq.com/cgi-bin/token'
        params = {
            'grant_type': 'client_credential',
            'appid': app_id,
            'secret': app_secret
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'errcode' in data and data['errcode'] != 0:
            raise Exception(f"获取 token 失败: {data.get('errmsg', '未知错误')}")
        
        access_token = data['access_token']
        expires_in = data.get('expires_in', 7200)
        expires_at = int(time.time()) + expires_in - 600  # 提前10分钟过期
        
        # 保存到数据库
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO access_token 
                (app_id, access_token, expires_at, created_at)
                VALUES (?, ?, ?, ?)
            ''', (app_id, access_token, expires_at, int(time.time())))
            
            conn.commit()
            logger.info(f'Access Token 已刷新: app_id={app_id}')
        finally:
            conn.close()
        
        return {
            'accessToken': access_token,
            'expiresAt': expires_at * 1000  # 转换为毫秒
        }

