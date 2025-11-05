import logging
from typing import Dict, Any
from flask import Blueprint, request, jsonify
from handlers import (
    TextMessageHandler,
    EventMessageHandler,
    ImageMessageHandler,
    VoiceMessageHandler,
    LinkMessageHandler,
    UnsupportedMessageHandler
)
from utils.message_parser import MessageParser
from utils.wechat_crypto import WechatMessageCrypto

logger = logging.getLogger(__name__)

# 创建蓝图
api_bp = Blueprint('api', __name__)

# 消息类型与处理器映射
MESSAGE_HANDLERS = {
    'text': TextMessageHandler,
    'event': EventMessageHandler,
    'image': ImageMessageHandler,
    'voice': VoiceMessageHandler,
    'link': LinkMessageHandler,
}

# 配置
config_cache: Dict[str, Any] = {}


def get_config() -> Dict[str, Any]:
    """获取配置"""
    if not config_cache:
        from config import load_config
        config_cache.update(load_config())
    return config_cache


def verify_signature(signature: str, timestamp: str, nonce: str, echostr: str) -> str:
    """
    验证微信服务器签名
    
    Args:
        signature: 微信加密签名
        timestamp: 时间戳
        nonce: 随机数
        echostr: 随机字符串
        
    Returns:
        echostr 或错误信息
    """
    try:
        config = get_config()
        token = config.get('token', '')
        
        # 如果配置了加密，使用加密验证
        if config.get('encoding_aes_key'):
            crypto = WechatMessageCrypto(
                token,
                config.get('encoding_aes_key'),
                config.get('app_id')
            )
            result = crypto.verify_signature(signature, timestamp, nonce, echostr)
            return result if result else '验证失败'
        
        # 简单的签名验证
        import hashlib
        temp = [token, timestamp, nonce]
        temp.sort()
        temp = ''.join(temp)
        temp = hashlib.sha1(temp.encode('utf-8')).hexdigest()
        
        if temp == signature:
            return echostr
        return '验证失败'
        
    except Exception as e:
        logger.error(f'验证签名失败: {str(e)}')
        return '验证失败'


@api_bp.route('/wechat', methods=['GET'])
def wechat_check():
    """
    微信服务器验证接口
    """
    try:
        signature = request.args.get('signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')
        echostr = request.args.get('echostr')
        
        logger.info('收到微信服务器验证请求')
        
        # 验证签名
        result = verify_signature(signature, timestamp, nonce, echostr)
        return result
        
    except Exception as e:
        logger.error(f'微信验证失败: {str(e)}')
        return '验证失败'


@api_bp.route('/wechat', methods=['POST'])
def wechat_callback():
    """
    微信消息回调接口
    """
    try:
        # 获取请求参数
        signature = request.args.get('signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')
        msg_signature = request.args.get('msg_signature')
        
        # 获取请求体
        data = request.get_data(as_text=True)
        
        logger.info(f'收到微信消息回调，消息类型: {request.content_type}')
        
        # 解析消息
        config = get_config()
        parser = MessageParser()
        
        # 如果配置了加密，需要解密
        if config.get('encoding_aes_key'):
            crypto = WechatMessageCrypto(
                config.get('token'),
                config.get('encoding_aes_key'),
                config.get('app_id')
            )
            data = crypto.decrypt_message(data, msg_signature, timestamp, nonce)
        
        # 解析XML
        message = parser.parse(data)
        
        if not message:
            logger.error('无法解析消息')
            return ''
        
        # 根据消息类型选择处理器
        handler_class = MESSAGE_HANDLERS.get(message.msg_type, UnsupportedMessageHandler)
        handler = handler_class()
        
        # 处理消息
        reply = handler.handle(message)
        
        # 如果需要加密，加密回复
        if reply and config.get('encoding_aes_key'):
            reply = crypto.encrypt_message(reply, timestamp, nonce)
        
        return reply if reply else ''
        
    except Exception as e:
        logger.error(f'处理微信回调失败: {str(e)}')
        return ''


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    return jsonify({
        'status': 'ok',
        'service': 'wechat_complete_plugin'
    })