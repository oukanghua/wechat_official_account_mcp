#!/usr/bin/env python3
"""
启动微信消息服务器的工具脚本
用于测试和开发
"""
import sys
import os

# 添加项目根目录到 Python 路径
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from server.wechat_message_server import WeChatMessageServer
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == '__main__':
    print("=" * 60)
    print("微信公众号消息服务器")
    print("=" * 60)
    print()
    
    # 检查配置
    from dotenv import load_dotenv
    load_dotenv()
    
    app_id = os.getenv('WECHAT_APP_ID', '')
    token = os.getenv('WECHAT_TOKEN', '')
    
    if not app_id or not token:
        print("⚠️  警告: 未配置 WECHAT_APP_ID 或 WECHAT_TOKEN")
        print("   请在 .env 文件中配置这些参数")
        print()
    
    # 获取端口配置
    port = int(os.getenv('WECHAT_SERVER_PORT', 8000))
    host = os.getenv('WECHAT_SERVER_HOST', '0.0.0.0')
    
    print(f"📡 服务器配置:")
    print(f"   - 监听地址: {host}")
    print(f"   - 监听端口: {port}")
    print(f"   - 验证接口: http://{host}:{port}/wechat (GET)")
    print(f"   - 消息接口: http://{host}:{port}/wechat (POST)")
    print(f"   - 健康检查: http://{host}:{port}/health")
    print()
    print("🚀 启动服务器...")
    print()
    
    # 创建并启动服务器
    server = WeChatMessageServer()
    server.run(host=host, port=port, debug=False)

