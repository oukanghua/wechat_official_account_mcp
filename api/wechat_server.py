"""
微信公众号消息接收服务器
独立运行，用于接收和处理微信公众号消息
"""
import logging
import os
import sys
from flask import Flask, request, Response
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 导入消息处理模块
from handlers.text import TextMessageHandler
from handlers.image import ImageMessageHandler
from handlers.voice import VoiceMessageHandler
from handlers.link import LinkMessageHandler
from handlers.event import EventMessageHandler
from handlers.unsupported import UnsupportedMessageHandler
from utils.message_parser import MessageParser
from utils.wechat_crypto import WechatMessageCrypto
from storage.auth_manager import AuthManager

# 初始化认证管理器
auth_manager = AuthManager()

# 消息处理器映射
MESSAGE_HANDLERS = {
    'text': TextMessageHandler(),
    'image': ImageMessageHandler(),
    'voice': VoiceMessageHandler(),
    'link': LinkMessageHandler(),
    'event': EventMessageHandler(),
}


def verify_signature(signature: str, timestamp: str, nonce: str, echostr: str, token: str) -> str:
    """
    验证微信服务器签名
    
    Args:
        signature: 微信传来的签名
        timestamp: 时间戳
        nonce: 随机数
        echostr: 随机字符串
        token: 配置的 token
        
    Returns:
        验证成功返回 echostr，失败返回空字符串
    """
    import hashlib
    
    # 按照字典序排序
    temp_list = [token, timestamp, nonce]
    temp_list.sort()
    
    # 拼接并加密
    temp_str = ''.join(temp_list)
    hash_str = hashlib.sha1(temp_str.encode('utf-8')).hexdigest()
    
    # 验证签名
    if hash_str == signature:
        return echostr
    return ''


@app.route('/wechat', methods=['GET'])
def wechat_get():
    """处理微信服务器验证请求"""
    try:
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')
        
        # 获取配置
        config = auth_manager.get_config()
        if not config:
            logger.error("未配置微信公众号信息")
            return Response('未配置', status=500)
        
        token = config.get('token', '')
        if not token:
            logger.error("未配置 token")
            return Response('未配置 token', status=500)
        
        # 验证签名
        result = verify_signature(signature, timestamp, nonce, echostr, token)
        
        if result:
            logger.info("微信服务器验证成功")
            return Response(result, status=200)
        else:
            logger.warning("微信服务器验证失败")
            return Response('验证失败', status=403)
    
    except Exception as e:
        logger.error(f"处理验证请求失败: {str(e)}", exc_info=True)
        return Response('服务器错误', status=500)


@app.route('/wechat', methods=['POST'])
def wechat_post():
    """处理微信消息"""
    try:
        # 获取配置
        config = auth_manager.get_config()
        if not config:
            logger.error("未配置微信公众号信息")
            return Response('未配置', status=500)
        
        # 创建加密工具
        crypto = WechatMessageCrypto(
            token=config.get('token', ''),
            encoding_aes_key=config.get('encoding_aes_key', ''),
            app_id=config.get('app_id', '')
        )
        
        # 解密消息
        try:
            msg_signature = request.args.get('msg_signature', '')
            timestamp = request.args.get('timestamp', '')
            nonce = request.args.get('nonce', '')
            
            if config.get('encoding_aes_key'):
                # 加密模式
                decrypted_xml = crypto.decrypt_message(
                    request.data.decode('utf-8'),
                    msg_signature,
                    timestamp,
                    nonce
                )
            else:
                # 明文模式
                decrypted_xml = request.data.decode('utf-8')
        
        except Exception as e:
            logger.error(f"消息解密失败: {str(e)}")
            return Response('解密失败', status=400)
        
        # 解析消息
        message = MessageParser.parse_xml(decrypted_xml)
        
        # 获取处理器
        handler = MESSAGE_HANDLERS.get(message.msg_type, UnsupportedMessageHandler())
        
        # 处理消息
        reply_content = handler.handle(message)
        
        # 构建回复
        reply_xml = MessageParser.build_text_reply(
            to_user=message.from_user,
            from_user=message.to_user,
            content=reply_content
        )
        
        # 加密回复（如果需要）
        if config.get('encoding_aes_key'):
            encrypted_reply = crypto.encrypt_message(reply_xml, timestamp, nonce)
            return Response(encrypted_reply, mimetype='application/xml')
        else:
            return Response(reply_xml, mimetype='application/xml')
    
    except Exception as e:
        logger.error(f"处理消息失败: {str(e)}", exc_info=True)
        return Response('', status=200)  # 返回空响应避免微信重试


def main():
    """启动 HTTP 服务器"""
    port = int(os.getenv('WECHAT_SERVER_PORT', 8000))
    host = os.getenv('WECHAT_SERVER_HOST', '0.0.0.0')
    
    logger.info(f"微信公众号消息服务器启动在 {host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    main()

