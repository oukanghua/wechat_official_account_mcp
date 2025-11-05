import os
from typing import Dict, Any
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


def load_config() -> Dict[str, Any]:
    """
    加载配置信息
    
    Returns:
        配置字典
    """
    # 加载.env文件
    load_dotenv()
    
    # 基础配置
    config = {
        # 微信公众号配置
        'app_id': os.environ.get('WECHAT_APP_ID', ''),
        'app_secret': os.environ.get('WECHAT_APP_SECRET', ''),
        'token': os.environ.get('WECHAT_TOKEN', ''),
        'encoding_aes_key': os.environ.get('WECHAT_ENCODING_AES_KEY', ''),
        
        # API配置
        'api_timeout': int(os.environ.get('API_TIMEOUT', '30')),
        'api_proxy': os.environ.get('API_PROXY', ''),
        
        # 消息处理配置
        'message_timeout': int(os.environ.get('MESSAGE_TIMEOUT', '10')),
        'retry_ratio': float(os.environ.get('RETRY_RATIO', '0.1')),
        
        # 缓存配置
        'cache_ttl': int(os.environ.get('CACHE_TTL', '7100')),  # access_token默认有效期-100秒
        
        # 日志配置
        'log_level': os.environ.get('LOG_LEVEL', 'INFO'),
        
        # 服务器配置
        'server_port': int(os.environ.get('SERVER_PORT', '8000')),
        'server_host': os.environ.get('SERVER_HOST', '0.0.0.0'),
    }
    
    # 验证必要配置
    required_configs = ['app_id', 'app_secret', 'token']
    missing_configs = [key for key in required_configs if not config[key]]
    
    if missing_configs:
        logger.warning(f'缺少必要配置: {missing_configs}')
    
    logger.info('配置加载完成')
    return config