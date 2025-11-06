"""
微信公众号消息服务器
用于接收和处理微信服务端发送的消息
"""
import logging
import os
import hashlib
from typing import Optional, Dict, Any
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


class WeChatMessageServer:
    """微信公众号消息服务器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化微信消息服务器
        
        Args:
            config: 配置字典，包含 app_id, app_secret, token, encoding_aes_key
                   如果为 None，则从环境变量或数据库加载
        """
        self.app = Flask(__name__)
        self.config = config or self._load_config()
        self._setup_routes()
        logger.info("微信消息服务器初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """从环境变量或数据库加载配置"""
        from shared.storage.auth_manager import AuthManager
        
        auth_manager = AuthManager()
        config = auth_manager.get_config()
        
        if not config:
            # 从环境变量加载
            config = {
                'app_id': os.getenv('WECHAT_APP_ID', ''),
                'app_secret': os.getenv('WECHAT_APP_SECRET', ''),
                'token': os.getenv('WECHAT_TOKEN', ''),
                'encoding_aes_key': os.getenv('WECHAT_ENCODING_AES_KEY', '')
            }
            
            if config.get('app_id') and config.get('app_secret'):
                try:
                    auth_manager.set_config(config)
                    logger.info(f"已从环境变量加载配置: app_id={config['app_id']}")
                except Exception as e:
                    logger.error(f"保存配置到数据库失败: {str(e)}")
        
        return config
    
    def _setup_routes(self):
        """设置路由"""
        @self.app.route('/wechat', methods=['GET'])
        def verify_server():
            """微信服务器验证接口"""
            return self.handle_verification()
        
        @self.app.route('/wechat', methods=['POST'])
        def receive_message():
            """接收微信消息接口"""
            return self.handle_message()
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """健康检查接口"""
            return self.health_check()
    
    def verify_signature(self, signature: str, timestamp: str, nonce: str, echostr: str = '') -> bool:
        """
        验证微信服务器签名
        
        对应 PHP 代码的 checkSignature() 方法：
        - 将 token, timestamp, nonce 放入数组
        - 使用字符串排序（SORT_STRING）
        - 拼接成字符串
        - SHA1 加密
        - 与传入的 signature 比较
        
        Args:
            signature: 微信传来的签名
            timestamp: 时间戳
            nonce: 随机数
            echostr: 随机字符串（可选，仅用于日志）
            
        Returns:
            bool: 验证成功返回 True，失败返回 False
        """
        token = self.config.get('token', '')
        if not token:
            logger.error("未配置 token")
            return False
        
        # 按照字典序排序（对应 PHP 的 sort($tmpArr, SORT_STRING)）
        temp_list = [token, timestamp, nonce]
        temp_list.sort()  # Python 的 sort() 默认就是字符串排序
        
        # 拼接成字符串（对应 PHP 的 implode($tmpArr)）
        temp_str = ''.join(temp_list)
        
        # SHA1 加密（对应 PHP 的 sha1($tmpStr)）
        hash_str = hashlib.sha1(temp_str.encode('utf-8')).hexdigest()
        
        # 验证签名（对应 PHP 的 if($tmpStr == $signature)）
        if hash_str == signature:
            logger.info("签名验证成功")
            return True
        else:
            logger.warning(f"签名验证失败: 期望 {hash_str}, 实际 {signature}")
            return False
    
    def handle_verification(self) -> Response:
        """
        处理微信服务器验证请求（GET /wechat）
        
        这是微信公众平台在配置服务器 URL 时调用的接口
        
        对应 PHP 代码的 valid() 方法：
        - 获取 echostr 参数
        - 验证签名
        - 验证成功则直接返回 echostr（纯文本，无其他内容）
        """
        try:
            signature = request.args.get('signature', '')
            timestamp = request.args.get('timestamp', '')
            nonce = request.args.get('nonce', '')
            echostr = request.args.get('echostr', '')
            
            logger.info(f"收到微信服务器验证请求: signature={signature[:10]}..., timestamp={timestamp}, nonce={nonce}, echostr={echostr}")
            
            # 验证签名（对应 PHP 的 checkSignature()）
            if self.verify_signature(signature, timestamp, nonce, echostr):
                # 验证成功，直接返回 echostr（对应 PHP 的 echo $echoStr; exit;）
                logger.info("微信服务器验证成功，返回 echostr")
                return Response(echostr, status=200, mimetype='text/plain')
            else:
                # 验证失败，返回空或错误（PHP 代码中验证失败不返回任何内容）
                logger.warning("微信服务器验证失败")
                return Response('', status=403)
        
        except Exception as e:
            logger.error(f"处理验证请求失败: {str(e)}", exc_info=True)
            return Response('', status=500)
    
    def handle_message(self) -> Response:
        """
        处理微信消息（POST /wechat）
        
        接收微信服务端发送的用户消息，处理后返回回复
        """
        try:
            # 获取配置
            if not self.config:
                logger.error("未配置微信公众号信息")
                return Response('未配置', status=500)
            
            # 获取请求参数
            msg_signature = request.args.get('msg_signature', '')
            timestamp = request.args.get('timestamp', '')
            nonce = request.args.get('nonce', '')
            
            # 解密消息
            from shared.utils.wechat_crypto import WechatMessageCrypto
            from server.utils.message_parser import MessageParser
            
            crypto = WechatMessageCrypto(
                token=self.config.get('token', ''),
                encoding_aes_key=self.config.get('encoding_aes_key', ''),
                app_id=self.config.get('app_id', '')
            )
            
            try:
                if self.config.get('encoding_aes_key'):
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
                
                logger.debug(f"解密后的消息: {decrypted_xml[:200]}...")
            
            except Exception as e:
                logger.error(f"消息解密失败: {str(e)}")
                return Response('解密失败', status=400)
            
            # 解析消息
            message = MessageParser.parse_xml(decrypted_xml)
            logger.info(f"收到消息: 类型={message.msg_type}, 用户={message.from_user}, 内容={message.content[:50] if message.content else 'N/A'}...")
            
            # 处理消息（这里可以调用消息处理器）
            reply_content = self.process_message(message)
            
            # 构建回复
            response_xml = MessageParser.build_text_reply(
                to_user=message.from_user,
                from_user=message.to_user,
                content=reply_content
            )
            
            # 加密回复（如果需要）
            if self.config.get('encoding_aes_key'):
                encrypted_response = crypto.encrypt_message(response_xml, timestamp, nonce)
                return Response(encrypted_response, mimetype='application/xml')
            else:
                return Response(response_xml, mimetype='application/xml')
        
        except Exception as e:
            logger.error(f"处理消息失败: {str(e)}", exc_info=True)
            # 返回空响应避免微信重试
            return Response('', status=200)
    
    def process_message(self, message) -> str:
        """
        处理消息并返回回复内容
        
        Args:
            message: 解析后的消息对象
            
        Returns:
            str: 回复内容
        """
        # 这里可以集成 Dify 或其他 AI 服务
        # 目前返回简单回复
        
        # 尝试使用 Dify AI（如果配置了）
        try:
            from server.utils.dify_api_client import get_dify_client
            dify_client = get_dify_client()
            
            if dify_client:
                app_id = os.getenv('DIFY_APP_ID', '')
                if app_id:
                    # 调用 Dify API
                    response_generator = dify_client.chat(
                        app_id=app_id,
                        query=message.content if hasattr(message, 'content') else '',
                        user=message.from_user
                    )
                    
                    # 处理响应
                    answer_parts = []
                    for chunk in response_generator:
                        if isinstance(chunk, dict):
                            if 'answer' in chunk:
                                answer_parts.append(chunk['answer'])
                            elif chunk.get('event') == 'message_end':
                                break
                    
                    if answer_parts:
                        answer = ''.join(answer_parts)
                        logger.info(f"Dify AI 响应成功，长度: {len(answer)}")
                        return answer
        except ImportError:
            logger.debug("Dify API 客户端未配置")
        except Exception as e:
            logger.warning(f"Dify AI 调用失败: {str(e)}")
        
        # 默认回复
        if hasattr(message, 'content') and message.content:
            return f"收到您的消息: {message.content}"
        else:
            return "收到您的消息"
    
    def health_check(self) -> Response:
        """健康检查接口"""
        try:
            status = {
                'status': 'ok',
                'config_loaded': bool(self.config),
                'has_token': bool(self.config.get('token') if self.config else False),
                'has_app_id': bool(self.config.get('app_id') if self.config else False)
            }
            
            import json
            return Response(
                json.dumps(status, ensure_ascii=False, indent=2),
                status=200,
                mimetype='application/json'
            )
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return Response('健康检查失败', status=500)
    
    def run(self, host: str = '0.0.0.0', port: int = 8000, debug: bool = False, 
            ssl_cert: Optional[str] = None, ssl_key: Optional[str] = None):
        """
        启动服务器
        
        Args:
            host: 监听地址
            port: 监听端口
            debug: 是否开启调试模式
            ssl_cert: SSL 证书路径（可选）
            ssl_key: SSL 密钥路径（可选）
        """
        if ssl_cert and ssl_key:
            logger.info(f"微信公众号消息服务器启动在 {host}:{port} (HTTPS)")
            self.app.run(host=host, port=port, debug=debug, ssl_context=(ssl_cert, ssl_key))
        else:
            logger.info(f"微信公众号消息服务器启动在 {host}:{port} (HTTP)")
            self.app.run(host=host, port=port, debug=debug)


def main():
    """主函数：启动微信消息服务器"""
    # 从环境变量获取配置
    port = int(os.getenv('WECHAT_SERVER_PORT', 80))
    host = os.getenv('WECHAT_SERVER_HOST', '0.0.0.0')
    ssl_cert = os.getenv('WECHAT_SSL_CERT', None)
    ssl_key = os.getenv('WECHAT_SSL_KEY', None)
    
    # 创建并启动服务器
    server = WeChatMessageServer()
    server.run(host=host, port=port, debug=False, ssl_cert=ssl_cert, ssl_key=ssl_key)


if __name__ == '__main__':
    main()

