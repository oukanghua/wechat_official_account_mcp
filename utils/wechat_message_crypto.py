import base64
import hashlib
import struct
from Crypto.Cipher import AES
import logging

logger = logging.getLogger(__name__)

class WechatMessageCrypto:
    """
    微信消息加解密工具类
    用于微信公众号消息的加密和解密
    """
    
    def __init__(self, token: str, encoding_aes_key: str, app_id: str):
        """
        初始化加解密工具
        
        Args:
            token: 微信公众号的Token
            encoding_aes_key: 微信公众号的EncodingAESKey
            app_id: 微信公众号的AppID
        """
        self.token = token
        self.app_id = app_id
        
        # 解析EncodingAESKey
        self.encoding_aes_key = encoding_aes_key + '='
        self.aes_key = base64.b64decode(self.encoding_aes_key)
        self.block_size = 32
    
    def encrypt(self, text: str) -> str:
        """
        加密消息
        
        Args:
            text: 待加密的文本
            
        Returns:
            str: 加密后的文本
        """
        try:
            # 生成随机的16字节填充
            import random
            import string
            
            nonce = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
            
            # 计算text长度
            text_length = len(text)
            
            # 构建消息内容: 随机16字节 + 4字节消息长度 + 消息内容 + app_id
            content = self._random_string(16) + struct.pack('!i', text_length) + text + self.app_id
            
            # PKCS#7填充
            padded_content = self._pad(content)
            
            # AES加密
            cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_key[:16])
            encrypted = cipher.encrypt(padded_content)
            
            # Base64编码
            encrypted_text = base64.b64encode(encrypted).decode('utf-8')
            
            return encrypted_text
            
        except Exception as e:
            logger.error(f"加密消息失败: {str(e)}")
            raise
    
    def decrypt(self, encrypted_text: str) -> str:
        """
        解密消息
        
        Args:
            encrypted_text: 加密的文本
            
        Returns:
            str: 解密后的文本
        """
        try:
            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_text)
            
            # AES解密
            cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_key[:16])
            decrypted = cipher.decrypt(encrypted_bytes)
            
            # 去除PKCS#7填充
            unpadded = self._unpad(decrypted)
            
            # 解析消息内容
            # 前16字节是随机字符串，接下来4字节是消息长度，然后是消息内容，最后是app_id
            text_length = struct.unpack('!i', unpadded[16:20])[0]
            text = unpadded[20:20 + text_length].decode('utf-8')
            
            # 验证app_id
            app_id = unpadded[20 + text_length:].decode('utf-8')
            if app_id != self.app_id:
                raise Exception('Invalid app_id')
            
            return text
            
        except Exception as e:
            logger.error(f"解密消息失败: {str(e)}")
            raise
    
    def verify_signature(self, signature: str, timestamp: str, nonce: str, echostr: str = None) -> bool:
        """
        验证微信消息签名
        
        Args:
            signature: 微信加密签名
            timestamp: 时间戳
            nonce: 随机数
            echostr: 随机字符串（用于验证服务器配置）
            
        Returns:
            bool: 签名是否有效
        """
        try:
            # 排序token、timestamp、nonce
            sort_list = [self.token, timestamp, nonce]
            if echostr:
                sort_list.append(echostr)
            
            sort_list.sort()
            
            # 拼接字符串
            sort_str = ''.join(sort_list)
            
            # SHA1加密
            sha1 = hashlib.sha1()
            sha1.update(sort_str.encode('utf-8'))
            hashcode = sha1.hexdigest()
            
            # 比较签名
            return hashcode == signature
            
        except Exception as e:
            logger.error(f"验证签名失败: {str(e)}")
            return False
    
    def generate_signature(self, timestamp: str, nonce: str, encrypted: str) -> str:
        """
        生成签名
        
        Args:
            timestamp: 时间戳
            nonce: 随机数
            encrypted: 加密后的消息
            
        Returns:
            str: 签名
        """
        try:
            # 排序token、timestamp、nonce、encrypted
            sort_list = [self.token, timestamp, nonce, encrypted]
            sort_list.sort()
            
            # 拼接字符串
            sort_str = ''.join(sort_list)
            
            # SHA1加密
            sha1 = hashlib.sha1()
            sha1.update(sort_str.encode('utf-8'))
            
            return sha1.hexdigest()
            
        except Exception as e:
            logger.error(f"生成签名失败: {str(e)}")
            raise
    
    def _pad(self, s: str) -> bytes:
        """
        PKCS#7填充
        
        Args:
            s: 待填充的字符串
            
        Returns:
            bytes: 填充后的字节串
        """
        s_bytes = s.encode('utf-8')
        pad = self.block_size - len(s_bytes) % self.block_size
        return s_bytes + (pad * chr(pad)).encode('utf-8')
    
    def _unpad(self, s: bytes) -> bytes:
        """
        去除PKCS#7填充
        
        Args:
            s: 待去除填充的字节串
            
        Returns:
            bytes: 去除填充后的字节串
        """
        pad = s[-1]
        return s[:-pad]
    
    def _random_string(self, length: int) -> str:
        """
        生成随机字符串
        
        Args:
            length: 字符串长度
            
        Returns:
            str: 随机字符串
        """
        import random
        import string
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
    
    def parse_encrypted_message(self, encrypted_msg: str) -> dict:
        """
        解析加密消息
        
        Args:
            encrypted_msg: 加密的消息
            
        Returns:
            dict: 解析后的消息字典
        """
        try:
            # 这里需要根据具体的XML结构进行解析
            # 实际应用中可能需要使用xml库解析
            from xml.etree import ElementTree as ET
            
            root = ET.fromstring(encrypted_msg)
            ToUserName = root.find('ToUserName').text
            Encrypt = root.find('Encrypt').text
            AgentID = root.find('AgentID').text if root.find('AgentID') is not None else None
            
            return {
                'ToUserName': ToUserName,
                'Encrypt': Encrypt,
                'AgentID': AgentID
            }
            
        except Exception as e:
            logger.error(f"解析加密消息失败: {str(e)}")
            raise