#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试微信公众号插件的核心功能
"""

import os
import sys
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config():
    """测试配置加载"""
    logger.info("测试配置加载...")
    try:
        from config import Config
        config = Config()
        logger.info(f"配置加载成功: {config.config}")
        return True
    except Exception as e:
        logger.error(f"配置加载失败: {str(e)}")
        return False

def test_api_client():
    """测试微信API客户端"""
    logger.info("测试微信API客户端...")
    try:
        from utils.wechat_api_client import WechatApiClient
        
        # 从环境变量获取测试凭据
        app_id = os.getenv('TEST_WECHAT_APP_ID', 'test_app_id')
        app_secret = os.getenv('TEST_WECHAT_APP_SECRET', 'test_app_secret')
        
        # 只测试初始化，不实际调用API
        client = WechatApiClient(app_id, app_secret)
        logger.info("微信API客户端初始化成功")
        return True
    except Exception as e:
        logger.error(f"微信API客户端测试失败: {str(e)}")
        return False

def test_message_parser():
    """测试消息解析器"""
    logger.info("测试消息解析器...")
    try:
        from utils.message_parser import MessageParser
        
        # 测试XML解析
        xml_str = """
        <xml>
            <ToUserName><![CDATA[toUser]]></ToUserName>
            <FromUserName><![CDATA[fromUser]]></FromUserName>
            <CreateTime>1348831860</CreateTime>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA[test content]]></Content>
            <MsgId>1234567890123456</MsgId>
        </xml>
        """
        
        message = MessageParser.parse_xml(xml_str)
        parsed = MessageParser.parse(message)
        
        logger.info(f"消息解析成功: {parsed}")
        return True
    except Exception as e:
        logger.error(f"消息解析器测试失败: {str(e)}")
        return False

def test_message_handler():
    """测试消息处理器"""
    logger.info("测试消息处理器...")
    try:
        from handlers.text import TextMessageHandler
        
        handler = TextMessageHandler()
        
        # 测试消息
        test_message = {
            'ToUserName': 'test_to',
            'FromUserName': 'test_from',
            'CreateTime': '1234567890',
            'MsgType': 'text',
            'Content': '你好',
            'MsgId': '1234567890'
        }
        
        reply = handler.handle(test_message)
        logger.info("消息处理器测试成功")
        return True
    except Exception as e:
        logger.error(f"消息处理器测试失败: {str(e)}")
        return False

def test_tools_loading():
    """测试工具加载"""
    logger.info("测试工具加载...")
    try:
        from tools import GetAccessTokenTool, CreateDraftTool, PublishDraftTool, UploadMediaTool
        
        logger.info("工具加载成功")
        return True
    except Exception as e:
        logger.error(f"工具加载失败: {str(e)}")
        return False

def run_all_tests():
    """运行所有测试"""
    logger.info("开始运行插件测试...")
    
    tests = [
        test_config,
        test_api_client,
        test_message_parser,
        test_message_handler,
        test_tools_loading
    ]
    
    results = {}
    passed = 0
    
    for test in tests:
        test_name = test.__name__
        logger.info(f"运行测试: {test_name}")
        
        try:
            result = test()
            results[test_name] = result
            if result:
                passed += 1
                logger.info(f"✅ 测试通过: {test_name}")
            else:
                logger.error(f"❌ 测试失败: {test_name}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"❌ 测试异常: {test_name}, 错误: {str(e)}")
    
    logger.info("\n测试结果汇总:")
    logger.info(f"总测试数: {len(tests)}")
    logger.info(f"通过测试数: {passed}")
    logger.info(f"失败测试数: {len(tests) - passed}")
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
    
    return passed == len(tests)

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)