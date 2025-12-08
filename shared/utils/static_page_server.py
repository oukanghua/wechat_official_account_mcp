"""
静态网页HTTP服务器
提供静态网页的HTTP访问服务
"""
import asyncio
import logging
import os
import threading
from pathlib import Path
from typing import Optional
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

logger = logging.getLogger(__name__)


class StaticPageHandler(SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""
    
    def __init__(self, *args, pages_dir=None, **kwargs):
        self.pages_dir = pages_dir
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        try:
            if self.path.startswith('/pages/'):
                # 访问静态网页：/pages/filename.html
                filename = self.path[7:]  # 去掉 '/pages/' 前缀
                
                # 安全检查：防止路径遍历攻击
                if '..' in filename or filename.startswith('/'):
                    self.send_error(403, "Forbidden")
                    return
                
                file_path = Path(self.pages_dir) / filename
                
                if not file_path.exists() or not file_path.is_file():
                    self.send_error(404, "File not found")
                    return
                
                # 设置内容类型
                if filename.endswith('.html'):
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.send_header('Cache-Control', 'no-cache')
                    self.end_headers()
                    
                    # 读取并返回文件内容
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.wfile.write(content.encode('utf-8'))
                else:
                    self.send_error(400, "Only HTML files are supported")
                    
            elif self.path == '/':
                # 首页：列出所有可用页面
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                html_content = self._generate_index_page()
                self.wfile.write(html_content.encode('utf-8'))
                
            else:
                self.send_error(404, "Page not found")
                
        except Exception as e:
            logger.error(f"处理请求失败: {e}")
            self.send_error(500, "Internal server error")
    
    def _generate_index_page(self) -> str:
        """生成索引页面"""
        try:
            # 读取元数据
            metadata_file = Path(self.pages_dir) / "metadata.json"
            pages = []
            
            if metadata_file.exists():
                import json
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    pages = list(metadata.values())
            
            # 按创建时间排序
            pages.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>静态网页服务</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            text-align: center;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .page-list {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .page-item {
            border-bottom: 1px solid #eee;
            padding: 15px 0;
        }
        .page-item:last-child {
            border-bottom: none;
        }
        .page-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .page-meta {
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .page-link {
            display: inline-block;
            background: #007cba;
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
        }
        .page-link:hover {
            background: #005a87;
        }
        .no-pages {
            text-align: center;
            color: #999;
            padding: 40px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>静态网页服务</h1>
        <p>生成和管理静态HTML网页的HTTP访问服务</p>
    </div>
    
    <div class="page-list">
        <h2>可用页面列表</h2>
"""
            
            if not pages:
                html += '        <div class="no-pages">暂无静态网页</div>\n'
            else:
                for page in pages:
                    filename = page.get('filename', '')
                    created_at = page.get('created_at', '')
                    file_size = page.get('file_size', 0)
                    
                    html += f"""        <div class="page-item">
            <div class="page-title">{filename}</div>
            <div class="page-meta">
                创建时间: {created_at} | 
                文件大小: {file_size} 字节
            </div>
            <a href="/pages/{filename}" class="page-link" target="_blank">访问页面</a>
        </div>
"""
            
            html += """    </div>
</body>
</html>"""
            return html
            
        except Exception as e:
            logger.error(f"生成索引页面失败: {e}")
            return "<h1>错误</h1><p>无法加载页面列表</p>"


class StaticPageServer:
    """静态网页HTTP服务器"""
    
    def __init__(self, pages_dir: str = "data/static_pages", port: int = 3004):
        """
        初始化HTTP服务器
        
        Args:
            pages_dir: 静态网页存储目录
            port: 服务端口
        """
        self.pages_dir = pages_dir
        self.port = port
        self.server = None
        self.server_thread = None
        self.is_running = False
        
        # 确保页面目录存在
        Path(self.pages_dir).mkdir(parents=True, exist_ok=True)
    
    def _create_handler(self, *args, **kwargs):
        """创建自定义请求处理器"""
        return StaticPageHandler(*args, pages_dir=self.pages_dir, **kwargs)
    
    def start(self):
        """启动HTTP服务器"""
        try:
            if self.is_running:
                logger.warning("服务器已经在运行中")
                return False
            
            self.server = HTTPServer(('0.0.0.0', self.port), self._create_handler)
            self.is_running = True
            
            # 在单独的线程中启动服务器
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            logger.info(f"静态网页HTTP服务器启动成功")
            logger.info(f"服务地址: http://localhost:{self.port}")
            logger.info(f"静态网页目录: {self.pages_dir}")
            logger.info(f"页面访问格式: http://localhost:{self.port}/pages/文件名.html")
            
            return True
            
        except Exception as e:
            logger.error(f"启动HTTP服务器失败: {e}")
            self.is_running = False
            return False
    
    def _run_server(self):
        """在独立线程中运行服务器"""
        try:
            logger.info(f"HTTP服务器线程启动，监听端口 {self.port}")
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"HTTP服务器运行异常: {e}")
        finally:
            self.is_running = False
    
    def stop(self):
        """停止HTTP服务器"""
        try:
            if self.server and self.is_running:
                self.server.shutdown()
                self.server.server_close()
                self.is_running = False
                logger.info("静态网页HTTP服务器已停止")
                return True
            return False
        except Exception as e:
            logger.error(f"停止HTTP服务器失败: {e}")
            return False
    
    def get_status(self) -> dict:
        """获取服务器状态"""
        return {
            "is_running": self.is_running,
            "port": self.port,
            "pages_dir": self.pages_dir,
            "server_url": f"http://localhost:{self.port}" if self.is_running else None
        }
    
    def get_page_url(self, filename: str) -> Optional[str]:
        """
        获取页面访问URL
        
        Args:
            filename: 文件名
            
        Returns:
            完整的访问URL，如果服务器未运行则返回None
        """
        if not self.is_running:
            return None
        
        # 确保文件名以.html结尾
        if not filename.endswith('.html'):
            filename += '.html'
        
        return f"http://localhost:{self.port}/pages/{filename}"


# 全局HTTP服务器实例
_static_page_server = None


def get_static_page_server() -> StaticPageServer:
    """获取全局静态网页服务器实例"""
    global _static_page_server
    if _static_page_server is None:
        _static_page_server = StaticPageServer()
    return _static_page_server


def start_static_page_server(port: int = 3004) -> bool:
    """
    启动静态网页HTTP服务器
    
    Args:
        port: 服务端口
        
    Returns:
        是否启动成功
    """
    global _static_page_server
    _static_page_server = StaticPageServer(port=port)
    return _static_page_server.start()


def get_static_page_url(filename: str) -> Optional[str]:
    """
    获取静态网页访问URL
    
    Args:
        filename: 文件名
        
    Returns:
        访问URL，如果服务器未运行则返回None
    """
    global _static_page_server
    if _static_page_server is None:
        return None
    
    return _static_page_server.get_page_url(filename)