#!/usr/bin/env python3
"""
MCP 服务器入口文件
用于启动 MCP 服务器
"""
import asyncio
from mcp_server import main

if __name__ == "__main__":
    asyncio.run(main())

