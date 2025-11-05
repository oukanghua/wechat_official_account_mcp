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

# 导入工具和工具函数
# 延迟导入，在 main() 函数中导入，确保在正确的目录下
try:
    from tools.auth import register_auth_tools
    from tools.media import register_media_tools
    from tools.draft import register_draft_tools
    from tools.publish import register_publish_tools
    from storage.auth_manager import AuthManager
    from storage.storage_manager import StorageManager
except ImportError as e:
    logger.error(f"导入项目模块失败: {e}", exc_info=True)
    # 不要立即退出，让 main() 函数处理

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
            from storage.auth_manager import AuthManager
            from storage.storage_manager import StorageManager
            auth_manager = AuthManager()
            storage_manager = StorageManager()
        
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
        import traceback
        error_detail = str(e)
        # 总是包含堆栈信息，便于调试
        error_detail += f"\n\n详细错误信息:\n{traceback.format_exc()}"
        logger.error(f"调用工具 {name} 时出错: {error_detail}", exc_info=True)
        return [TextContent(type="text", text=f"工具调用失败: {error_detail}")]


async def main():
    """主函数"""
    global auth_manager, storage_manager
    
    # 立即输出启动信息到 stderr
    print("MCP Server: Starting...", file=sys.stderr, flush=True)
    
    try:
        # 确保在正确的目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        original_cwd = os.getcwd()
        os.chdir(script_dir)
        print(f"MCP Server: Changed directory from {original_cwd} to {script_dir}", file=sys.stderr, flush=True)
        
        # 添加项目目录到 Python 路径
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        
        # 加载环境变量
        if os.path.exists('.env'):
            from dotenv import load_dotenv
            load_dotenv()
            print("MCP Server: Loaded .env file", file=sys.stderr, flush=True)
        
        # 确保必要的目录存在
        required_dirs = ['tools', 'handlers', 'api', 'utils', 'storage', 'config']
        for dir_name in required_dirs:
            Path(dir_name).mkdir(exist_ok=True)
        
        # 现在导入项目模块（在正确的目录下）
        print("MCP Server: Importing project modules...", file=sys.stderr, flush=True)
        try:
            from tools.auth import register_auth_tools
            from tools.media import register_media_tools
            from tools.draft import register_draft_tools
            from tools.publish import register_publish_tools
            from storage.auth_manager import AuthManager
            from storage.storage_manager import StorageManager
            
            print("MCP Server: Project modules imported successfully", file=sys.stderr, flush=True)
            
            # 初始化存储管理器
            auth_manager = AuthManager()
            storage_manager = StorageManager()
            print("MCP Server: Storage managers initialized", file=sys.stderr, flush=True)
            
        except ImportError as e:
            print(f"MCP Server: ERROR - Failed to import project modules: {e}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            sys.exit(1)
        
        logger.info("微信公众号 MCP 服务器启动中...")
        logger.info(f"工作目录: {os.getcwd()}")
        logger.info(f"Python 版本: {sys.version}")
        logger.info(f"Python 路径: {sys.path[:3]}")
        sys.stderr.flush()  # 确保日志输出
        
        print("MCP Server: Initializing stdio_server...", file=sys.stderr, flush=True)
        
        # 使用 stdio 传输运行服务器
        # MCP SDK 的标准用法：使用 stdio_server 上下文管理器
        async with stdio_server() as streams:
            print("MCP Server: stdio_server initialized", file=sys.stderr, flush=True)
            
            # streams 可能是一个元组 (read, write) 或对象
            if isinstance(streams, tuple):
                read_stream, write_stream = streams
                print(f"MCP Server: Streams is tuple, length: {len(streams)}", file=sys.stderr, flush=True)
            else:
                # 如果 streams 是对象，尝试获取 read 和 write 属性
                read_stream = getattr(streams, 'read', streams)
                write_stream = getattr(streams, 'write', streams)
                print(f"MCP Server: Streams is object, type: {type(streams)}", file=sys.stderr, flush=True)
            
            print("MCP Server: Starting server.run()...", file=sys.stderr, flush=True)
            logger.info("MCP 服务器已启动，等待客户端连接...")
            sys.stderr.flush()
            
            # 获取初始化选项
            init_options = {}
            if hasattr(server, 'create_initialization_options'):
                try:
                    init_options = server.create_initialization_options()
                    print(f"MCP Server: Initialization options: {init_options}", file=sys.stderr, flush=True)
                except Exception as e:
                    print(f"MCP Server: Warning - Failed to get init options: {e}", file=sys.stderr, flush=True)
            
            print("MCP Server: Calling server.run()...", file=sys.stderr, flush=True)
            
            await server.run(
                read_stream,
                write_stream,
                init_options
            )
            
    except KeyboardInterrupt:
        print("MCP Server: Received keyboard interrupt", file=sys.stderr, flush=True)
        logger.info("收到中断信号，正在关闭服务器...")
        sys.stderr.flush()
    except Exception as e:
        print(f"MCP Server: FATAL ERROR - {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        logger.error(f"MCP 服务器启动异常: {str(e)}", exc_info=True)
        sys.stderr.flush()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
