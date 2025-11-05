import xml.etree.ElementTree as ET
from typing import Dict, Any
from ..models import WechatMessage
import logging

logger = logging.getLogger(__name__)

class MessageParser:
    """微信消息解析器"""
    
    @staticmethod
    def parse_xml(xml_data: str) -> WechatMessage:
        """
        解析XML格式的微信消息
        
        Args:
            xml_data: XML格式的消息数据
            
        Returns:
            WechatMessage: 解析后的消息对象
        """
        try:
            # 解析XML
            root = ET.fromstring(xml_data)
            
            # 提取所有字段
            data = {}
            for child in root:
                # 将标签名转换为Python风格的键名（首字母大写，其余小写）
                key = child.tag
                value = child.text or ''
                data[key] = value
            
            # 转换特定字段
            if 'CreateTime' in data:
                data['CreateTime'] = int(data['CreateTime'])
            
            if 'Location_X' in data:
                data['Location_X'] = float(data['Location_X'])
            
            if 'Location_Y' in data:
                data['Location_Y'] = float(data['Location_Y'])
            
            if 'Scale' in data:
                data['Scale'] = float(data['Scale'])
            
            # 创建消息对象
            message = WechatMessage.from_dict(data)
            
            logger.debug(f"成功解析消息，类型: {message.msg_type}, 发送方: {message.from_user}")
            
            return message
            
        except ET.ParseError as e:
            logger.error(f"XML解析失败: {str(e)}")
            raise ValueError(f"无效的XML格式: {str(e)}")
        except Exception as e:
            logger.error(f"消息解析失败: {str(e)}")
            raise
    
    @staticmethod
    def format_xml(message: WechatMessage, content: str) -> str:
        """
        格式化回复消息为XML
        
        Args:
            message: 接收到的消息
            content: 回复内容
            
        Returns:
            str: XML格式的回复消息
        """
        return MessageParser.build_text_reply(message.from_user, message.to_user, content)
    
    @staticmethod
    def build_text_reply(to_user: str, from_user: str, content: str, create_time: int = None) -> str:
        """
        构建文本回复XML
        
        Args:
            to_user: 接收方用户名
            from_user: 发送方用户名
            content: 回复内容
            create_time: 创建时间（可选）
            
        Returns:
            str: XML格式的回复消息
        """
        import time
        
        if create_time is None:
            create_time = int(time.time())
        
        try:
            # 创建回复XML
            xml_template = f"""<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{create_time}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""
            
            return xml_template
            
        except Exception as e:
            logger.error(f"构建回复XML失败: {str(e)}")
            raise