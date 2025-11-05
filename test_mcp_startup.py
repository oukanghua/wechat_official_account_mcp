#!/usr/bin/env python3
"""
测试 MCP 服务器启动
"""
import sys
import os
import traceback

print("=" * 60)
print("MCP 服务器启动诊断")
print("=" * 60)

# 1. 检查 Python 版本
print("\n1. Python 环境:")
print(f"   Python 版本: {sys.version}")
print(f"   Python 路径: {sys.executable}")
print(f"   当前工作目录: {os.getcwd()}")

# 2. 检查项目路径
print("\n2. 项目路径:")
main_py = os.path.join(os.getcwd(), "main.py")
print(f"   main.py 路径: {main_py}")
print(f"   main.py 存在: {os.path.exists(main_py)}")

# 3. 检查依赖
print("\n3. 检查依赖:")
try:
    import mcp
    print(f"   ✅ MCP 已安装: {getattr(mcp, '__version__', 'unknown version')}")
except ImportError as e:
    print(f"   ❌ MCP 未安装: {e}")
    sys.exit(1)

try:
    import flask
    print(f"   ✅ Flask 已安装: {flask.__version__}")
except ImportError as e:
    print(f"   ⚠️  Flask 未安装: {e}")

try:
    import requests
    print(f"   ✅ Requests 已安装: {requests.__version__}")
except ImportError as e:
    print(f"   ⚠️  Requests 未安装: {e}")

# 4. 检查项目模块
print("\n4. 检查项目模块:")
try:
    sys.path.insert(0, os.getcwd())
    from storage.auth_manager import AuthManager
    print("   ✅ storage.auth_manager 导入成功")
except Exception as e:
    print(f"   ❌ storage.auth_manager 导入失败: {e}")
    traceback.print_exc()

try:
    from tools.auth import register_auth_tools
    print("   ✅ tools.auth 导入成功")
except Exception as e:
    print(f"   ❌ tools.auth 导入失败: {e}")
    traceback.print_exc()

try:
    from utils.wechat_api_client import WechatApiClient
    print("   ✅ utils.wechat_api_client 导入成功")
except Exception as e:
    print(f"   ❌ utils.wechat_api_client 导入失败: {e}")
    traceback.print_exc()

# 5. 测试 MCP 服务器初始化
print("\n5. 测试 MCP 服务器初始化:")
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    print("   ✅ MCP SDK 导入成功")
    
    server = Server("wechat-official-account-mcp")
    print("   ✅ MCP Server 创建成功")
    
except Exception as e:
    print(f"   ❌ MCP 服务器初始化失败: {e}")
    traceback.print_exc()
    sys.exit(1)

# 6. 检查环境变量
print("\n6. 环境变量:")
env_vars = ['WECHAT_APP_ID', 'WECHAT_APP_SECRET', 'WECHAT_TOKEN', 'WECHAT_ENCODING_AES_KEY']
for var in env_vars:
    value = os.getenv(var, '')
    if value:
        # 隐藏敏感信息
        if 'SECRET' in var or 'KEY' in var:
            display_value = value[:10] + '...' if len(value) > 10 else '***'
        else:
            display_value = value
        print(f"   ✅ {var}: {display_value}")
    else:
        print(f"   ⚠️  {var}: 未设置")

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)

