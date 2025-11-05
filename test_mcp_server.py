#!/usr/bin/env python3
"""
测试 MCP 服务器是否能正确响应初始化请求
"""
import asyncio
import sys
import os
from io import BytesIO

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.server.stdio import stdio_server

# 创建服务器
server = Server("test-server")

@server.list_tools()
async def list_tools():
    return []

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    from mcp.types import TextContent
    return [TextContent(type="text", text="OK")]

async def main():
    print("Test MCP Server: Starting...", file=sys.stderr, flush=True)
    
    try:
        async with stdio_server() as streams:
            print(f"Test MCP Server: Streams type: {type(streams)}", file=sys.stderr, flush=True)
            
            if isinstance(streams, tuple):
                read_stream, write_stream = streams
            else:
                read_stream = getattr(streams, 'read', streams)
                write_stream = getattr(streams, 'write', streams)
            
            print("Test MCP Server: Starting server.run()...", file=sys.stderr, flush=True)
            
            # 尝试不传递初始化选项
            init_options = {}
            if hasattr(server, 'create_initialization_options'):
                try:
                    init_options = server.create_initialization_options()
                    print(f"Test MCP Server: Init options: {init_options}", file=sys.stderr, flush=True)
                except Exception as e:
                    print(f"Test MCP Server: Error getting init options: {e}", file=sys.stderr, flush=True)
            
            await server.run(read_stream, write_stream, init_options)
            
    except Exception as e:
        print(f"Test MCP Server: Error: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())


