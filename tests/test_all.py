#!/usr/bin/env python3
"""
统一测试文件
包含所有测试功能
"""
import sys
import os

# 添加项目根目录到 Python 路径
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import unittest
from typing import Optional


def test_mcp_connection():
    """测试 MCP 服务器连接"""
    print("\n=== 测试 MCP 服务器连接 ===")
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        print("[OK] MCP SDK 导入成功")
        
        server = Server("test")
        print("[OK] MCP 服务器创建成功")
        
        return True
    except Exception as e:
        print(f"[ERROR] MCP 连接测试失败: {e}")
        return False


def test_module_imports():
    """测试模块导入"""
    print("\n=== 测试模块导入 ===")
    
    modules = [
        ("mcp.tools.auth", "register_auth_tools"),
        ("mcp.tools.media", "register_media_tools"),
        ("mcp.tools.draft", "register_draft_tools"),
        ("mcp.tools.publish", "register_publish_tools"),
        ("shared.storage.auth_manager", "AuthManager"),
        ("shared.storage.storage_manager", "StorageManager"),
        ("shared.utils.wechat_api_client", "WechatApiClient"),
        ("server.handlers.text", "TextMessageHandler"),
        ("server.utils.message_parser", "MessageParser"),
    ]
    
    success = True
    for module_name, attr_name in modules:
        try:
            module = __import__(module_name, fromlist=[attr_name])
            getattr(module, attr_name)
            print(f"[OK] {module_name}.{attr_name}")
        except Exception as e:
            print(f"[ERROR] {module_name}.{attr_name}: {e}")
            success = False
    
    return success


def test_wechat_config():
    """测试微信配置"""
    print("\n=== 测试微信配置 ===")
    try:
        from shared.storage.auth_manager import AuthManager
        
        auth_manager = AuthManager()
        config = auth_manager.get_config()
        
        if config:
            print(f"[OK] 配置已存在: AppID={config.get('app_id', 'N/A')}")
        else:
            print("[WARN] 配置不存在，需要先配置")
        
        return True
    except Exception as e:
        print(f"[ERROR] 配置测试失败: {e}")
        return False


def test_server_import():
    """测试服务器模块导入"""
    print("\n=== 测试服务器模块导入 ===")
    try:
        # 测试是否可以导入服务器模块
        import server.wechat_server
        print("[OK] 服务器模块导入成功")
        return True
    except Exception as e:
        print(f"[ERROR] 服务器模块导入失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 50)
    print("微信公众号 MCP 服务器 - 测试套件")
    print("=" * 50)
    
    results = []
    
    # 运行测试
    results.append(("MCP 连接", test_mcp_connection()))
    results.append(("模块导入", test_module_imports()))
    results.append(("微信配置", test_wechat_config()))
    results.append(("服务器导入", test_server_import()))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n所有测试通过！")
        return 0
    else:
        print(f"\n{total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())

