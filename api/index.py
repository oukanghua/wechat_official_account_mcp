#!/usr/bin/env python3
"""
Vercel 统一入口 - 同时支持 FastMCP 和 Flask Web 服务
路由配置:
- /mcp/* -> FastMCP 服务
- /*     -> Flask Web 服务
"""
import os
import sys
from pathlib import Path

script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

os.environ.setdefault('MCP_TRANSPORT', 'http')
os.environ.setdefault('MCP_HOST', '0.0.0.0')
os.environ.setdefault('WECHAT_MSG_SERVER_ENABLE', 'true')

data_dir = script_dir / 'data'
data_dir.mkdir(exist_ok=True)

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_mcp_handler():
    """创建 FastMCP 请求处理器"""
    from mcp_server import mcp, initialize_managers
    initialize_managers()

    async def mcp_app(scope, receive, send):
        if scope['type'] == 'http':
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [(b'content-type', b'text/plain')],
            })
            await send({
                'type': 'http.response.body',
                'body': b'FastMCP server is running\n',
            })
        elif scope['type'] == 'lifespan':
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    await send({'type': 'lifespan.startup.complete'})
                elif message['type'] == 'lifespan.shutdown':
                    await send({'type': 'lifespan.shutdown.complete'})
                    break
    return mcp_app


def create_web_app():
    """创建 Flask Web 应用"""
    from shared.utils.web_server import IntegratedStaticPageServer
    from tools.static_pages import StaticPageManager

    storage_dir = str(script_dir / 'data' / 'static_pages')
    db_file = str(script_dir / 'data' / 'storage.db')
    static_page_manager = StaticPageManager(storage_dir=storage_dir, db_file=db_file)

    web_server = IntegratedStaticPageServer(
        pages_dir=storage_dir,
        port=0,
        static_page_manager=static_page_manager
    )
    return web_server.app


def create_router():
    """创建路由分发器"""
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route
    from starlette.requests import Request
    from starlette.responses import JSONResponse, RedirectResponse
    from starlette.middleware.wsgi import WSGIMiddleware

    mcp_app = create_mcp_handler()
    web_app = create_web_app()

    async def health(request: Request):
        return JSONResponse({
            "status": "ok",
            "services": {"mcp": True, "web": True}
        })

    async def root(request: Request):
        return RedirectResponse(url="/web/")

    routes = [
        Route("/_health", health),
        Route("/", root),
        Mount("/mcp", app=mcp_app),
        Mount("/", app=WSGIMiddleware(web_app)),
    ]

    return Starlette(routes=routes)


logger.info("初始化统一服务...")
app = create_router()
logger.info("统一服务初始化完成")
