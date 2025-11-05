from typing import Dict, Any, Generator
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from ..utils.wechat_api_client import WechatApiClient
import logging

logger = logging.getLogger(__name__)

class GetAccessTokenTool(Tool):
    """获取微信公众号访问令牌工具"""
    
    def _invoke(self, tool_parameters: Dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """
        调用获取访问令牌工具
        
        Args:
            tool_parameters: 工具参数，包含force_refresh
            
        Yields:
            ToolInvokeMessage: 工具调用消息
        """
        try:
            # 获取凭据
            app_id = self.runtime.credentials.get('app_id')
            app_secret = self.runtime.credentials.get('app_secret')
            
            if not app_id or not app_secret:
                raise ToolProviderCredentialValidationError('App ID和App Secret不能为空')
            
            # 获取参数
            force_refresh = tool_parameters.get('force_refresh', False)
            
            # 创建微信API客户端
            client = WechatApiClient(app_id, app_secret)
            
            # 获取访问令牌
            access_token = client.get_access_token(force_refresh)
            
            # 记录访问令牌（注意安全）
            logger.info('成功获取微信公众号访问令牌')
            
            yield self.create_text_message(access_token)
            
        except Exception as e:
            logger.error(f'获取访问令牌失败: {str(e)}')
            yield self.create_text_message(f'获取访问令牌时发生错误: {str(e)}')