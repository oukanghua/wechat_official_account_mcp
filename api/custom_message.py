"""
微信公众号客服消息发送器
"""
import json
import logging
import time
from typing import Dict, Any, Optional

import requests

logger = logging.getLogger(__name__)


class WechatCustomMessageSender:
    """微信公众号客服消息发送器"""
    
    TOKEN_CACHE = {}  # 用于缓存 access token
    
    def __init__(self, app_id: str, app_secret: str, api_base_url: str = None):
        """
        初始化客服消息发送器
        
        Args:
            app_id: 微信公众号 AppID
            app_secret: 微信公众号 AppSecret
            api_base_url: 微信 API 基础 URL，默认为 api.weixin.qq.com
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.api_base_url = api_base_url or "api.weixin.qq.com"
    
    def _get_access_token(self) -> str:
        """
        获取微信 API access token
        
        Returns:
            有效的 access_token 字符串
        
        Raises:
            Exception: 当获取 token 失败时
        """
        # 检查缓存中是否有有效的 token
        cache_key = f"{self.app_id}_{self.app_secret}"
        if cache_key in self.TOKEN_CACHE:
            token_info = self.TOKEN_CACHE[cache_key]
            # 检查 token 是否过期（在过期前 5 分钟刷新）
            if token_info['expires_at'] > time.time() + 300:
                return token_info['token']
        
        # 请求新的 access token
        url = f"https://{self.api_base_url}/cgi-bin/token?grant_type=client_credential&appid={self.app_id}&secret={self.app_secret}"
        
        try:
            response = requests.get(url, timeout=10)
            result = response.json()
            
            if 'access_token' in result:
                # 计算过期时间（token 有效期通常为 7200 秒）
                expires_at = time.time() + result.get('expires_in', 7200)
                # 保存到缓存
                self.TOKEN_CACHE[cache_key] = {
                    'token': result['access_token'],
                    'expires_at': expires_at
                }
                return result['access_token']
            else:
                error_msg = f"获取 access token 失败: {result.get('errmsg', 'unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)
        
        except Exception as e:
            logger.error(f"请求 access token 错误: {str(e)}")
            raise
    
    def send_text_message(self, open_id: str, content: str) -> Dict[str, Any]:
        """
        发送文本客服消息
        
        Args:
            open_id: 用户 OpenID
            content: 文本消息内容
            
        Returns:
            API 响应结果
        """
        try:
            # 获取 access token
            access_token = self._get_access_token()
            
            # 构建请求 URL
            url = f"https://{self.api_base_url}/cgi-bin/message/custom/send?access_token={access_token}"
            
            # 构建请求数据
            data = {
                "touser": open_id,
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
            
            # 发送请求
            response = requests.post(
                url=url,
                data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            # 解析响应
            result = response.json()
            
            if result.get('errcode', 0) != 0:
                error_msg = f"发送客服消息失败: {result.get('errmsg', 'unknown error')}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'raw_response': result
                }
            
            return {
                'success': True,
                'raw_response': result
            }
            
        except Exception as e:
            logger.error(f"发送客服消息错误: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def set_typing_status(self, open_id: str, typing: bool) -> Dict[str, Any]:
        """
        设置公众号正在输入状态
        
        Args:
            open_id: 用户的 OpenID
            typing: True-开始输入，False-结束输入
            
        Returns:
            操作结果
        """
        try:
            access_token = self._get_access_token()

            url = f"https://{self.api_base_url}/cgi-bin/message/custom/typing?access_token={access_token}"

            data = {
                "touser": open_id,
                "command": "Typing" if typing else "CancelTyping"
            }

            response = requests.post(
                url=url, 
                data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            result = response.json()

            if result.get("errcode") != 0:
                logger.error(f"设置正在输入状态失败: {result}")
                return {"success": False, "error": result.get("errmsg")}
            return {"success": True}
        
        except Exception as e:
            logger.error(f"设置正在输入状态异常: {str(e)}")
            return {"success": False, "error": str(e)}


