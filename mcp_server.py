#!/usr/bin/env python3
"""
微信公众号 MCP 服务器
提供微信公众号管理的完整 MCP 工具集
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

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

# 创建 MCP 服务器实例
server = Server("wechat-official-account-mcp")

# 存储管理器在 main() 中初始化
auth_manager = None
storage_manager = None


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具"""
    try:
        # 动态导入，确保在正确的目录下
        from tools.auth import register_auth_tools
        from tools.media import register_media_tools
        from tools.draft import register_draft_tools
        from tools.publish import register_publish_tools
        
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
    except Exception as e:
        logger.error(f"注册工具失败: {e}", exc_info=True)
        return []


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """调用工具"""
    global auth_manager, storage_manager
    
    try:
        # 确保存储管理器已初始化
        if auth_manager is None or storage_manager is None:
            from shared.storage.auth_manager import AuthManager
            from shared.storage.storage_manager import StorageManager
            auth_manager = AuthManager()
            storage_manager = StorageManager()
        
        # 认证工具
        if name == "wechat_auth":
            from tools.auth import handle_auth_tool
            result = await handle_auth_tool(arguments, auth_manager)
            return [TextContent(type="text", text=result)]
        
        # 需要 API 客户端的工具
        elif name in ["wechat_media_upload", "wechat_upload_img", "wechat_permanent_media", 
                      "wechat_draft", "wechat_publish"]:
            from shared.utils.wechat_api_client import WechatApiClient
            api_client = await WechatApiClient.from_auth_manager(auth_manager)
            
            if name == "wechat_media_upload":
                from tools.media import handle_media_upload_tool
                result = await handle_media_upload_tool(arguments, api_client, storage_manager)
            elif name == "wechat_upload_img":
                from tools.media import handle_upload_img_tool
                result = await handle_upload_img_tool(arguments, api_client)
            elif name == "wechat_permanent_media":
                from tools.media import handle_permanent_media_tool
                result = await handle_permanent_media_tool(arguments, api_client, storage_manager)
            elif name == "wechat_draft":
                from tools.draft import handle_draft_tool
                result = await handle_draft_tool(arguments, api_client)
            elif name == "wechat_publish":
                from tools.publish import handle_publish_tool
                result = await handle_publish_tool(arguments, api_client)
            
            return [TextContent(type="text", text=result)]
        
        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]
    
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\n详细错误信息:\n{traceback.format_exc()}"
        logger.error(f"调用工具 {name} 时出错: {error_detail}", exc_info=True)
        return [TextContent(type="text", text=f"工具调用失败: {error_detail}")]


async def main():
    """主函数"""
    global auth_manager, storage_manager
    
    try:
        # 添加项目目录到 Python 路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        
        # 加载环境变量（.env 文件）
        if os.path.exists('.env'):
            from dotenv import load_dotenv
            load_dotenv()
        
        # 注意：系统环境变量（如 MCP 客户端设置的 env）会自动被 os.getenv() 读取
        
        # 确保数据目录存在
        Path('data').mkdir(exist_ok=True)
        
        # 导入项目模块
        try:
            from tools.auth import register_auth_tools
            from tools.media import register_media_tools
            from tools.draft import register_draft_tools
            from tools.publish import register_publish_tools
            from shared.storage.auth_manager import AuthManager
            from shared.storage.storage_manager import StorageManager
            
            # 初始化存储管理器
            auth_manager = AuthManager()
            storage_manager = StorageManager()
            
        except ImportError as e:
            logger.error(f"导入项目模块失败: {e}", exc_info=True)
            sys.exit(1)
        
        logger.info("微信公众号 MCP 服务器启动中...")
        
        # 使用 stdio 传输运行服务器
        async with stdio_server() as streams:
            logger.info("MCP 服务器已启动，等待客户端连接...")
            
            # streams 可能是一个元组 (read, write) 或对象
            if isinstance(streams, tuple):
                read_stream, write_stream = streams
            else:
                read_stream = getattr(streams, 'read', streams)
                write_stream = getattr(streams, 'write', streams)
            
            # 获取初始化选项
            init_options = {}
            if hasattr(server, 'create_initialization_options'):
                try:
                    init_options = server.create_initialization_options()
                except Exception:
                    pass
            
            await server.run(read_stream, write_stream, init_options)
            
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"MCP 服务器启动异常: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

