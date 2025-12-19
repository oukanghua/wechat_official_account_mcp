#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号信息发起端脚本
模拟微信公众号发送消息到web_server，并处理重试逻辑
每次发送等待5秒，超时后用同样的参数再次发送，直到收到AI回复消息，最多重试3次
"""

import time
import requests
import hashlib
import random
import logging
from xml.etree import ElementTree as ET

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WechatMessageSender:
    def __init__(self):
        # 从.env文件读取配置，或者直接硬编码配置
        self.token = "93ae007b834c476b731d7ab89154d260"  # 从.env文件中WECHAT_TOKEN获取
        self.url = "http://localhost:3004/xst_insight/wechat/reply"
        self.max_retries = 3
        self.timeout = 5  # 每次请求超时时间5秒
        
        # 模拟微信公众号的基本信息
        self.app_id = "wxd2685048ebe96e85"  # 从.env文件中WECHAT_APP_ID获取
        self.to_user = "wx_test_account"  # 接收消息的用户OpenID（模拟）
        self.from_user = "wx_official_account"  # 公众号原始ID（模拟）
    
    def _generate_signature(self, timestamp, nonce):
        """生成微信消息签名"""
        temp_list = [self.token, timestamp, nonce]
        temp_list.sort()
        temp_str = ''.join(temp_list)
        sha1_hash = hashlib.sha1(temp_str.encode('utf-8')).hexdigest()
        return sha1_hash
    
    def _build_xml_message(self, content, msg_id):
        """构建微信文本消息XML格式"""
        timestamp = str(int(time.time()))
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<xml>
    <ToUserName><![CDATA[{self.to_user}]]></ToUserName>
    <FromUserName><![CDATA[{self.from_user}]]></FromUserName>
    <CreateTime>{timestamp}</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[{content}]]></Content>
    <MsgId>{msg_id}</MsgId>
</xml>"""
    
    def send_message(self, content):
        """发送微信消息并处理重试逻辑"""
        msg_id = str(random.randint(1000000000, 9999999999))  # 生成随机消息ID
        timestamp = str(int(time.time()))
        nonce = str(random.randint(100000, 999999))
        signature = self._generate_signature(timestamp, nonce)
        
        # 构建请求参数
        params = {
            'signature': signature,
            'timestamp': timestamp,
            'nonce': nonce,
            'echostr': ''
        }
        
        # 构建XML消息
        xml_message = self._build_xml_message(content, msg_id)
        
        retries = 0
        success = False
        response_content = None
        
        while retries < self.max_retries and not success:
            retries += 1
            logger.info(f"第{retries}次发送消息，内容: {content}")
            
            try:
                # 发送POST请求
                response = requests.post(
                    self.url,
                    params=params,
                    data=xml_message,
                    headers={'Content-Type': 'application/xml; charset=utf-8'},
                    timeout=self.timeout
                )
                
                logger.info(f"收到响应，状态码: {response.status_code}, 响应内容: {response.text}")
                
                # 检查响应状态码
                if response.status_code == 200:
                    # 解析XML响应
                    try:
                        root = ET.fromstring(response.text)
                        msg_type = root.find('MsgType').text if root.find('MsgType') is not None else ''
                        if msg_type == 'text':
                            response_content = root.find('Content').text if root.find('Content') is not None else ''
                            logger.info(f"成功收到AI回复: {response_content}")
                            success = True
                        else:
                            logger.warning(f"收到非文本响应，类型: {msg_type}")
                    except Exception as e:
                        logger.error(f"解析响应XML失败: {e}")
                else:
                    logger.warning(f"收到错误状态码: {response.status_code}")
            
            except requests.Timeout:
                logger.warning(f"第{retries}次请求超时")
            except Exception as e:
                logger.error(f"第{retries}次请求异常: {e}")
            
            # 如果未成功且还有重试次数，等待1秒后重试
            if not success and retries < self.max_retries:
                logger.info(f"等待1秒后重试...")
                time.sleep(1)
        
        if success:
            return response_content
        else:
            logger.error(f"经过{self.max_retries}次重试后仍未收到成功响应")
            return None

if __name__ == "__main__":
    sender = WechatMessageSender()
    
    # 测试消息
    test_message = "本周资讯报告总结。"
    logger.info(f"开始发送测试消息: {test_message}")
    
    response = sender.send_message(test_message)
    
    if response:
        logger.info(f"最终收到AI回复: {response}")
    else:
        logger.error("未能收到AI回复")
