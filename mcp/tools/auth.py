"""
认证工具 - 管理微信公众号认证配置和 Access Token
"""
import logging
from typing import Dict, Any, List
from mcp.types import Tool

logger = logging.getLogger(__name__)


def register_auth_tools() -> List[Tool]:
    """注册认证工具"""
    return [
        Tool(
            name="wechat_auth",
            description="管理微信公众号认证配置和 Access Token",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["configure", "get_token", "refresh_token", "get_config"],
                        "description": "操作类型：configure(配置), get_token(获取令牌), refresh_token(刷新令牌), get_config(获取配置)"
                    },
                    "appId": {
                        "type": "string",
                        "description": "微信公众号 AppID（配置时必需）"
                    },
                    "appSecret": {
                        "type": "string",
                        "description": "微信公众号 AppSecret（配置时必需）"
                    },
                    "token": {
                        "type": "string",
                        "description": "微信公众号 Token（可选，用于消息验证）"
                    },
                    "encodingAESKey": {
                        "type": "string",
                        "description": "微信公众号 EncodingAESKey（可选，用于消息加密）"
                    }
                },
                "required": ["action"]
            }
        )
    ]


async def handle_auth_tool(arguments: Dict[str, Any], auth_manager) -> str:
    """
    处理认证工具调用
    
    Args:
        arguments: 工具参数
        auth_manager: 认证管理器实例
        
    Returns:
        结果文本
    """
    action = arguments.get('action')
    
    try:
        if action == 'configure':
            app_id = arguments.get('appId')
            app_secret = arguments.get('appSecret')
            token = arguments.get('token', '')
            encoding_aes_key = arguments.get('encodingAESKey', '')
            
            if not app_id or not app_secret:
                return "错误：配置时 appId 和 appSecret 是必需的"
            
            auth_manager.set_config({
                'appId': app_id,
                'appSecret': app_secret,
                'token': token,
                'encodingAESKey': encoding_aes_key
            })
            
            return f"微信公众号配置已成功保存\n- AppID: {app_id}\n- Token: {token or '未设置'}\n- EncodingAESKey: {encoding_aes_key or '未设置'}"
        
        elif action == 'get_token':
            token_info = await auth_manager.get_access_token()
            import time
            expires_in = max(0, int((token_info['expiresAt'] - time.time() * 1000) / 1000))
            
            return f"Access Token 信息:\n- Token: {token_info['accessToken']}\n- 剩余有效时间: {expires_in} 秒"
        
        elif action == 'refresh_token':
            token_info = await auth_manager.refresh_access_token()
            import time
            expires_in = max(0, int((token_info['expiresAt'] - time.time() * 1000) / 1000))
            
            return f"Access Token 已刷新:\n- 新 Token: {token_info['accessToken']}\n- 有效时间: {expires_in} 秒"
        
        elif action == 'get_config':
            config = auth_manager.get_config()
            if not config:
                return "尚未配置微信公众号信息，请先使用 configure 操作进行配置。"
            
            return f"当前微信公众号配置:\n- AppID: {config['app_id']}\n- AppSecret: {config['app_secret'][:8]}...\n- Token: {config['token'] or '未设置'}\n- EncodingAESKey: {config['encoding_aes_key'] or '未设置'}"
        
        else:
            return f"未知操作: {action}"
    
    except Exception as e:
        import traceback
        error_detail = str(e)
        if logger.isEnabledFor(logging.DEBUG):
            error_detail += f"\n详细错误信息:\n{traceback.format_exc()}"
        logger.error(f'认证操作失败: {error_detail}', exc_info=True)
        return f"认证操作失败: {error_detail}"

