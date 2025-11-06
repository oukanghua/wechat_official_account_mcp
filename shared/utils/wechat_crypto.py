import base64
import struct
import random
import string
import hashlib
from Crypto.Cipher import AES
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class WechatMessageCrypto:
    """微信消息加密解密工具"""
    
    def __init__(self, token: str, encoding_aes_key: str, app_id: str):
        """
        初始化加密工具
        
        Args:
            token: 微信公众号Token
            encoding_aes_key: 消息加密密钥
            app_id: 微信公众号AppID
        """
        self.token = token
        self.app_id = app_id
        
        # 解析encoding_aes_key
        if encoding_aes_key:
            # Base64解码
            aes_key = base64.b64decode(encoding_aes_key + '=')
            if len(aes_key) != 32:
                raise ValueError('encoding_aes_key长度不正确')
            self.aes_key = aes_key
            self.cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_key[:16])
        else:
            self.aes_key = None
            self.cipher = None
    
    def encrypt(self, text: str) -> str:
        """
        加密消息
        
        Args:
            text: 待加密的文本
            
        Returns:
            str: 加密后的Base64编码字符串
        """
        if not self.cipher:
            return text
        
        try:
            # 生成随机字符串
            random_str = self._generate_random_str(16)
            
            # 组合数据：随机字符串 + 消息长度(4字节) + 消息内容 + AppID
            text_bytes = text.encode('utf-8')
            msg_len = struct.pack('!I', len(text_bytes))
            content = random_str.encode('utf-8') + msg_len + text_bytes + self.app_id.encode('utf-8')
            
            # PKCS#7填充
            padded_content = self._pad_pkcs7(content)
            
            # AES加密
            encrypted = self.cipher.encrypt(padded_content)
            
            # Base64编码
            return base64.b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            logger.error(f'消息加密失败: {str(e)}')
            raise
    
    def decrypt(self, encrypted_text: str) -> str:
        """
        解密消息
        
        Args:
            encrypted_text: 加密的Base64编码字符串
            
        Returns:
            str: 解密后的文本
        """
        if not self.cipher:
            return encrypted_text
        
        try:
            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_text)
            
            # AES解密
            decrypted = self.cipher.decrypt(encrypted_bytes)
            
            # 去除PKCS#7填充
            unpadded = self._unpad_pkcs7(decrypted)
            
            # 解析数据：前16字节为随机字符串，接下来4字节为消息长度，然后是消息内容，最后是AppID
            msg_len = struct.unpack('!I', unpadded[16:20])[0]
            text = unpadded[20:20 + msg_len].decode('utf-8')
            
            # 验证AppID
            app_id = unpadded[20 + msg_len:].decode('utf-8')
            if app_id != self.app_id:
                raise ValueError('AppID验证失败')
            
            return text
            
        except Exception as e:
            logger.error(f'消息解密失败: {str(e)}')
            raise
    
    def verify_signature(self, signature: str, timestamp: str, nonce: str, encrypt_msg: str = None) -> bool:
        """
        验证消息签名
        
        Args:
            signature: 微信加密签名
            timestamp: 时间戳
            nonce: 随机数
            encrypt_msg: 加密消息（如果有）
            
        Returns:
            bool: 签名是否有效
        """
        try:
            # 排序
            if encrypt_msg:
                items = [self.token, timestamp, nonce, encrypt_msg]
            else:
                items = [self.token, timestamp, nonce]
            
            items.sort()
            
            # 拼接并计算SHA1
            s = ''.join(items)
            sha1 = hashlib.sha1(s.encode('utf-8')).hexdigest()
            
            # 验证签名
            return sha1 == signature
            
        except Exception as e:
            logger.error(f'签名验证失败: {str(e)}')
            return False
    
    def _generate_random_str(self, length: int) -> str:
        """
        生成随机字符串
        
        Args:
            length: 字符串长度
            
        Returns:
            str: 随机字符串
        """
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
    
    def _pad_pkcs7(self, data: bytes) -> bytes:
        """
        PKCS#7填充
        
        Args:
            data: 待填充的数据
            
        Returns:
            bytes: 填充后的数据
        """
        block_size = 32
        padding_size = block_size - (len(data) % block_size)
        padding = bytes([padding_size]) * padding_size
        return data + padding
    
    def _unpad_pkcs7(self, data: bytes) -> bytes:
        """
        去除PKCS#7填充
        
        Args:
            data: 填充的数据
            
        Returns:
            bytes: 原始数据
        """
        padding_size = data[-1]
        return data[:-padding_size]
    
    def decrypt_message(self, encrypted_xml: str, msg_signature: str, timestamp: str, nonce: str) -> str:
        """
        解密微信XML消息
        
        Args:
            encrypted_xml: 加密的XML消息
            msg_signature: 消息签名
            timestamp: 时间戳
            nonce: 随机数
            
        Returns:
            str: 解密后的XML消息
        """
        import xml.etree.ElementTree as ET
        
        if not self.cipher:
            # 明文模式，直接返回
            return encrypted_xml
        
        try:
            # 解析XML
            root = ET.fromstring(encrypted_xml)
            encrypt_tag = root.find('Encrypt')
            if encrypt_tag is None:
                return encrypted_xml
            
            encrypt_msg = encrypt_tag.text
            
            # 验证签名
            if not self.verify_signature(msg_signature, timestamp, nonce, encrypt_msg):
                raise ValueError('消息签名验证失败')
            
            # 解密
            decrypted_text = self.decrypt(encrypt_msg)
            
            return decrypted_text
            
        except Exception as e:
            logger.error(f'解密XML消息失败: {str(e)}')
            raise
    
    def encrypt_message(self, xml_content: str, timestamp: str = None, nonce: str = None) -> str:
        """
        加密微信XML消息
        
        Args:
            xml_content: 待加密的XML消息
            timestamp: 时间戳（可选）
            nonce: 随机数（可选）
            
        Returns:
            str: 加密后的XML消息
        """
        import xml.etree.ElementTree as ET
        import time
        
        if not self.cipher:
            # 明文模式，直接返回
            return xml_content
        
        try:
            # 加密
            encrypted_text = self.encrypt(xml_content)
            
            # 生成时间戳和随机数
            if not timestamp:
                timestamp = str(int(time.time()))
            if not nonce:
                nonce = self._generate_random_str(16)
            
            # 计算签名
            signature = self.verify_signature('', timestamp, nonce, encrypted_text)
            # 重新计算签名（因为verify_signature返回bool，我们需要重新计算）
            items = [self.token, timestamp, nonce, encrypted_text]
            items.sort()
            s = ''.join(items)
            signature = hashlib.sha1(s.encode('utf-8')).hexdigest()
            
            # 构建加密XML
            encrypted_xml = f'''<xml>
<Encrypt><![CDATA[{encrypted_text}]]></Encrypt>
<MsgSignature><![CDATA[{signature}]]></MsgSignature>
<TimeStamp>{timestamp}</TimeStamp>
<Nonce><![CDATA[{nonce}]]></Nonce>
</xml>'''
            
            return encrypted_xml
            
        except Exception as e:
            logger.error(f'加密XML消息失败: {str(e)}')
            raise