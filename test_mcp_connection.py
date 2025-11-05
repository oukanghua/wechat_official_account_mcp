#!/usr/bin/env python3
"""
测试 MCP 服务器连接
用于验证服务器是否能正常启动和响应
"""
import sys
import os
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    print("[OK] MCP SDK imported successfully")
except ImportError as e:
    print(f"[ERROR] MCP SDK import failed: {e}")
    sys.exit(1)

try:
    # 导入项目模块
    from storage.auth_manager import AuthManager
    from tools.auth import register_auth_tools
    print("[OK] Project modules imported successfully")
except ImportError as e:
    print(f"[ERROR] Project modules import failed: {e}")
    sys.exit(1)

# 创建服务器
try:
    server = Server("wechat-official-account-mcp")
    print(f"[OK] MCP server created: {server.name}")
except Exception as e:
    print(f"[ERROR] MCP server creation failed: {e}")
    sys.exit(1)

# 测试工具注册
try:
    tools = register_auth_tools()
    print(f"[OK] Tools registered successfully, found {len(tools)} tools")
except Exception as e:
    print(f"[ERROR] Tool registration failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("MCP 服务器配置验证完成")
print("="*60)
print("\n服务器应该可以正常启动。")
print("如果 Claude Desktop 仍然报错，请检查：")
print("1. 配置文件路径是否正确")
print("2. 环境变量是否正确设置")
print("3. Claude Desktop 是否已重启")

