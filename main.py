#!/usr/bin/env python3
"""
微信公众号 MCP 服务器
合并了 dify_wechat_plugin 和 wechat-official-account-mcp 的功能
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    # 如果 MCP SDK 不可用，尝试使用替代方案
    try:
        from mcp import Server
        from mcp.stdio import stdio_server
        from mcp import Tool, TextContent
    except ImportError:
        logger.error("无法导入 MCP SDK，请安装: pip install mcp")
        sys.exit(1)

# 导入工具和工具函数
from tools.auth import register_auth_tools
from tools.media import register_media_tools
from tools.draft import register_draft_tools
from tools.publish import register_publish_tools

# 导入配置和存储管理器
from storage.auth_manager import AuthManager
from storage.storage_manager import StorageManager

# 创建 MCP 服务器实例
server = Server("wechat-official-account-mcp")

# 初始化存储管理器
auth_manager = AuthManager()
storage_manager = StorageManager()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具"""
    tools = []
    
    # 注册认证工具
    tools.extend(register_auth_tools())
    
    # 注册素材工具
    tools.extend(register_media_tools())
    
    # 注册草稿工具
    tools.extend(register_draft_tools())
    
    # 注册发布工具
    tools.extend(register_publish_tools())
    
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """调用工具"""
    try:
        # 认证工具
        if name == "wechat_auth":
            from tools.auth import handle_auth_tool
            result = await handle_auth_tool(arguments, auth_manager)
            return [TextContent(type="text", text=result)]
        
        # 临时素材工具
        elif name == "wechat_media_upload":
            from tools.media import handle_media_upload_tool
            from utils.wechat_api_client import WechatApiClient
            api_client = WechatApiClient.from_auth_manager(auth_manager)
            result = await handle_media_upload_tool(arguments, api_client, storage_manager)
            return [TextContent(type="text", text=result)]
        
        # 图文消息图片上传工具
        elif name == "wechat_upload_img":
            from tools.media import handle_upload_img_tool
            from utils.wechat_api_client import WechatApiClient
            api_client = WechatApiClient.from_auth_manager(auth_manager)
            result = await handle_upload_img_tool(arguments, api_client)
            return [TextContent(type="text", text=result)]
        
        # 永久素材工具
        elif name == "wechat_permanent_media":
            from tools.media import handle_permanent_media_tool
            from utils.wechat_api_client import WechatApiClient
            api_client = WechatApiClient.from_auth_manager(auth_manager)
            result = await handle_permanent_media_tool(arguments, api_client, storage_manager)
            return [TextContent(type="text", text=result)]
        
        # 草稿工具
        elif name == "wechat_draft":
            from tools.draft import handle_draft_tool
            from utils.wechat_api_client import WechatApiClient
            api_client = WechatApiClient.from_auth_manager(auth_manager)
            result = await handle_draft_tool(arguments, api_client)
            return [TextContent(type="text", text=result)]
        
        # 发布工具
        elif name == "wechat_publish":
            from tools.publish import handle_publish_tool
            from utils.wechat_api_client import WechatApiClient
            api_client = WechatApiClient.from_auth_manager(auth_manager)
            result = await handle_publish_tool(arguments, api_client)
            return [TextContent(type="text", text=result)]
        
        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]
    
    except Exception as e:
        logger.error(f"调用工具 {name} 时出错: {str(e)}", exc_info=True)
        return [TextContent(type="text", text=f"工具调用失败: {str(e)}")]


async def main():
    """主函数"""
    # 加载环境变量
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()
    
    # 确保必要的目录存在
    required_dirs = ['tools', 'handlers', 'api', 'utils', 'storage', 'config']
    for dir_name in required_dirs:
        Path(dir_name).mkdir(exist_ok=True)
    
    logger.info("微信公众号 MCP 服务器启动中...")
    
    # 使用 stdio 传输运行服务器
    try:
        async with stdio_server() as streams:
            await server.run(
                streams[0] if isinstance(streams, tuple) else streams.read,
                streams[1] if isinstance(streams, tuple) else streams.write,
                server.create_initialization_options() if hasattr(server, 'create_initialization_options') else {}
            )
    except Exception as e:
        logger.error(f"启动 MCP 服务器失败: {str(e)}")
        # 尝试使用简化的运行方式
        import sys
        await server.run(
            sys.stdin.buffer,
            sys.stdout.buffer
        )


if __name__ == "__main__":
    asyncio.run(main())
