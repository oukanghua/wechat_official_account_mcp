"""
Dify API 客户端
用于调用 Dify API 进行 AI 对话
"""
import logging
import requests
import json
from typing import Dict, Any, Optional, Generator
import time

logger = logging.getLogger(__name__)


class DifyApiClient:
    """Dify API 客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.dify.ai/v1"):
        """
        初始化 Dify API 客户端
        
        Args:
            api_key: Dify API Key
            base_url: Dify API 基础 URL，默认为 https://api.dify.ai/v1
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def chat(self, app_id: str, query: str, user: str = "wechat_user", 
             conversation_id: Optional[str] = None, inputs: Optional[Dict[str, Any]] = None,
             response_mode: str = "streaming") -> Generator:
        """
        调用 Dify Chat API
        
        Args:
            app_id: Dify 应用 ID
            query: 用户查询
            user: 用户 ID
            conversation_id: 会话 ID（可选）
            inputs: 输入参数（可选）
            response_mode: 响应模式，"streaming" 或 "blocking"
            
        Yields:
            Dict: 响应块
        """
        url = f"{self.base_url}/chat-messages"
        
        data = {
            "inputs": inputs or {},
            "query": query,
            "user": user,
            "response_mode": response_mode
        }
        
        if conversation_id:
            data["conversation_id"] = conversation_id
        
        try:
            if response_mode == "streaming":
                # 流式响应
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=data,
                    stream=True,
                    timeout=300
                )
                
                if response.status_code != 200:
                    error_msg = f"API 请求失败: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    yield {'answer': f'抱歉，AI处理失败: {error_msg}'}
                    return
                
                # 解析 SSE 流
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                event_data = json.loads(line_str[6:])
                                yield event_data
                                
                                # 如果收到结束事件，停止
                                if event_data.get('event') == 'message_end':
                                    break
                            except json.JSONDecodeError:
                                logger.warning(f"无法解析 SSE 数据: {line_str}")
            else:
                # 阻塞式响应
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=data,
                    timeout=300
                )
                
                if response.status_code != 200:
                    error_msg = f"API 请求失败: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    yield {'answer': f'抱歉，AI处理失败: {error_msg}'}
                    return
                
                result = response.json()
                yield result
                
        except Exception as e:
            logger.error(f"调用 Dify API 失败: {str(e)}")
            yield {'answer': f'抱歉，AI处理失败: {str(e)}'}


def get_dify_client() -> Optional[DifyApiClient]:
    """
    获取 Dify API 客户端（如果配置了）
    
    Returns:
        DifyApiClient 实例或 None
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv('DIFY_API_KEY', '')
    base_url = os.getenv('DIFY_BASE_URL', 'https://api.dify.ai/v1')
    app_id = os.getenv('DIFY_APP_ID', '')
    
    if api_key and app_id:
        return DifyApiClient(api_key, base_url)
    
    return None


