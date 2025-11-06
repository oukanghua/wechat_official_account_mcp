#!/usr/bin/env python3
"""
MCP 服务器入口文件
用于启动 MCP 服务器
"""
import sys
import os

# 添加项目根目录到 Python 路径
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 导入并运行 MCP 服务器
from mcp.server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())

