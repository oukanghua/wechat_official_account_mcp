"""
静态网页HTTP服务器
提供静态网页的HTTP访问服务，集成微信消息处理和聊天界面
"""
import asyncio
import logging
import os
import threading
import json
import hashlib
import xml.etree.ElementTree as ET
import time
import re
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from http.server import HTTPServer, SimpleHTTPRequestHandler, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver
import mimetypes

logger = logging.getLogger(__name__)


def render_template(template_path: str, variables: Dict[str, Any]) -> str:
    """
    简单的模板渲染引擎
    
    Args:
        template_path: 模板文件路径
        variables: 模板变量字典
        
    Returns:
        渲染后的HTML字符串
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # 简单的变量替换
        def replace_var(match):
            var_name = match.group(1)
            return str(variables.get(var_name, ''))
        
        # 替换 {{ variable }}
        html = re.sub(r'\{\{\s*(\w+)\s*\}\}', replace_var, template)
        
        # 简单的循环处理（for page in pages_info）
        def replace_for_loop(match):
            loop_content = match.group(1)
            loop_var = match.group(2)
            items = variables.get(loop_var, [])
            
            result = ""
            for item in items:
                # 为每个item创建上下文
                item_context = variables.copy()
                item_context.update(item)
                
                # 替换item中的变量
                item_html = loop_content
                for key, value in item.items():
                    item_html = item_html.replace(f"{{{{ {key} }}}}", str(value))
                result += item_html
            
            return result
        
        # 处理 {% for page in pages_info %} ... {% endfor %}
        html = re.sub(r'\{\%\s*for\s+(\w+)\s+in\s+(\w+)\s*\%\}(.*?)\{\%\s*endfor\s*\%\}', 
                     replace_for_loop, html, flags=re.DOTALL)
        
        # 简单的条件判断处理
        def replace_if(match):
            condition = match.group(1).strip()
            if_content = match.group(2)
            
            # 简单的条件判断：检查变量是否存在且不为空
            var_name = condition.replace(' not ', ' not ').replace(' and ', ' and ').replace(' or ', ' or ')
            if var_name in variables and variables[var_name]:
                return if_content
            return ""
        
        # 处理 {% if condition %} ... {% endif %}
        html = re.sub(r'\{\%\s*if\s+(\w+)\s*\%\}(.*?)\{\%\s*endif\s*\%\}', 
                     replace_if, html, flags=re.DOTALL)
        
        return html
        
    except Exception as e:
        logger.error(f"模板渲染失败 {template_path}: {e}")
        return f"<h1>模板渲染失败</h1><p>错误: {e}</p>"


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
            
            # 获取模板路径
            template_path = Path(__file__).parent.parent.parent / "templates" / "index_template.html"
            
            # 准备模板变量
            template_vars = {
                'title': '静态网页服务',
                'subtitle': '生成和管理静态HTML网页的HTTP访问服务',
                'pages_url': '/pages/',
                'chat_url': '/chat'
            }
            
            # 使用模板渲染
            html = render_template(str(template_path), template_vars)
            
            # 添加页面列表（简单的字符串替换方式）
            page_items = ""
            if not pages:
                page_items = '<div style="text-align: center; color: #999; padding: 40px;">暂无静态网页</div>'
            else:
                for page in pages:
                    filename = page.get('filename', '')
                    created_at = page.get('created_at', '')
                    file_size = page.get('file_size', 0)
                    
                    page_items += f"""                <div class="page-item">
                    <div class="page-title">{filename}</div>
                    <div class="page-meta">
                        创建时间: {created_at} | 
                        文件大小: {file_size} 字节
                    </div>
                    <a href="/pages/{filename}" class="page-link" target="_blank">访问页面</a>
                </div>
"""
            
            # 在页面内容中添加页面列表
            if '</div>' in html and '<div class="nav-grid">' in html:
                # 在导航卡片后面插入页面列表
                html = html.replace('</div>\n        \n        <div class="footer">', 
                                   f'''</div>
        
        <div style="margin-top: 30px; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
            <h2 style="margin-bottom: 20px; color: #2c3e50;">📂 静态网页列表</h2>
            {page_items}
        </div>
        
        <div class="footer">''')
            
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


def start_static_page_server(port: int = 3004, static_page_manager=None) -> bool:
    """
    启动静态网页HTTP服务器
    
    Args:
        port: 服务端口
        static_page_manager: 静态页面管理器实例
        
    Returns:
        是否启动成功
    """
    global _static_page_server
    
    # 使用与静态页面管理器相同的pages_dir路径
    pages_dir = "data/static_pages"
    if static_page_manager and hasattr(static_page_manager, 'storage_dir'):
        pages_dir = str(static_page_manager.storage_dir)
    
    # 使用集成版本的服务器以支持聊天和微信功能
    _static_page_server = IntegratedStaticPageServer(pages_dir=pages_dir, port=port, static_page_manager=static_page_manager)
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


class IntegratedStaticPageHandler(StaticPageHandler):
    """集成静态网页处理器，支持微信消息处理和聊天界面"""
    
    def __init__(self, *args, static_page_manager=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.static_page_manager = static_page_manager
    
    def do_GET(self):
        """处理GET请求 - 集成版本"""
        try:
            # 规范化路径：移除重复斜杠，处理Nginx代理可能带来的路径问题
            self.path = re.sub(r'/+', '/', self.path)
            
            # 首先检查精确匹配
            if self.path == '/chat/api/config':
                # 返回AI配置信息
                self._handle_config_api()
            elif self.path == '/favicon.ico':
                # 处理favicon请求
                self._handle_favicon()
            elif self.path.startswith('/chat'):
                # 聊天界面路由 (优先处理精确匹配)
                self._handle_chat_interface()
            elif self.path.startswith('/pages/'):
                # 访问静态网页
                super().do_GET()
            elif self.path.startswith('/wechat/verify'):
                # 微信服务器验证
                self._handle_wechat_verify()
            elif self.path == '/':
                # 首页：集成显示
                self._handle_integrated_index()
            else:
                self.send_error(404, "Page not found")
                
        except Exception as e:
            logger.error(f"处理请求失败: {e}")
            self.send_error(500, "Internal server error")
    
    def do_POST(self):
        """处理POST请求"""
        try:
            # 规范化路径：移除重复斜杠，处理Nginx代理可能带来的路径问题
            self.path = re.sub(r'/+', '/', self.path)
            
            if self.path == '/chat/api/send':
                # 聊天API接口 (精确匹配)
                self._handle_chat_api()
            elif self.path == '/chat/api/config':
                # 处理配置保存
                self._handle_config_post()
            elif self.path == '/api/validate-password':
                # 密码验证API
                self._handle_validate_password()
            elif self.path.startswith('/wechat/verify'):
                # 微信消息处理
                self._handle_wechat_message()
            elif self.path.startswith('/chat/api/'):
                # 其他聊天API接口
                self._handle_chat_api()
            else:
                self.send_error(404, "Page not found")
                
        except Exception as e:
            logger.error(f"处理POST请求失败: {e}")
            self.send_error(500, "Internal server error")
    
    def _handle_wechat_verify(self):
        """处理微信服务器验证"""
        try:
            # 获取查询参数
            query_params = {}
            if '?' in self.path:
                query_string = self.path.split('?', 1)[1]
                for param in query_string.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        query_params[key] = value
            
            signature = query_params.get('signature', '')
            timestamp = query_params.get('timestamp', '')
            nonce = query_params.get('nonce', '')
            echostr = query_params.get('echostr', '')
            
            # 从环境变量获取token
            token = os.getenv('WECHAT_TOKEN', 'default_token')
            
            # 验证签名
            temp_list = [token, timestamp, nonce]
            temp_list.sort()
            temp_str = ''.join(temp_list)
            sha1_hash = hashlib.sha1(temp_str.encode('utf-8')).hexdigest()
            
            if sha1_hash == signature:
                # 验证成功，返回echostr
                self.send_response(200)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(echostr.encode('utf-8'))
                logger.info("微信服务器验证成功")
            else:
                # 验证失败
                self.send_error(403, "Signature verification failed")
                logger.warning("微信服务器验证失败")
                
        except Exception as e:
            logger.error(f"处理微信验证失败: {e}")
            self.send_error(500, "Internal server error")
    
    def _handle_wechat_message(self):
        """处理微信消息"""
        try:
            # 获取POST数据
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "No content")
                return
            
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # 解析XML消息
            root = ET.fromstring(post_data)
            message_data = {child.tag: child.text for child in root}
            
            # 获取消息类型和内容
            msg_type = message_data.get('MsgType', '')
            from_user = message_data.get('FromUserName', '')
            to_user = message_data.get('ToUserName', '')
            timestamp = message_data.get('CreateTime', '')
            
            # 处理不同类型的消息
            if msg_type == 'text':
                content = message_data.get('Content', '')
                reply_content = self._get_ai_reply(content)
            else:
                reply_content = "感谢您的消息，我已收到并正在处理中。"
            
            # 构建回复XML
            reply_xml = self._build_reply_xml(from_user, to_user, reply_content)
            
            # 发送回复
            self.send_response(200)
            self.send_header('Content-type', 'text/xml; charset=utf-8')
            self.end_headers()
            self.wfile.write(reply_xml.encode('utf-8'))
            
            # 保存消息到存储
            if self.static_page_manager:
                try:
                    from tools.wechat_handler import WechatMessageHandler
                    wechat_handler = WechatMessageHandler()
                    message_info = {
                        'from_user': from_user,
                        'to_user': to_user,
                        'msg_type': msg_type,
                        'content': message_data.get('Content', ''),
                        'reply': reply_content,
                        'timestamp': timestamp,
                        'xml_data': post_data
                    }
                    wechat_handler.save_message(message_info)
                except Exception as e:
                    logger.error(f"保存微信消息失败: {e}")
            
            logger.info(f"处理微信消息: {msg_type} from {from_user}")
            
        except Exception as e:
            logger.error(f"处理微信消息失败: {e}")
            self.send_error(500, "Internal server error")
    
    def _handle_chat_interface(self):
        """处理聊天界面"""
        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_content = self._generate_chat_interface()
            self.wfile.write(html_content.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"生成聊天界面失败: {e}")
            self.send_error(500, "Internal server error")
    
    def _handle_chat_api(self):
        """处理聊天API接口"""
        try:
            if self.path == '/chat/api/send':
                # 发送消息
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    self.send_error(400, "No content")
                    return
                
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(post_data)
                message = data.get('message', '')
                
                if not message:
                    self.send_error(400, "Message is required")
                    return
                
                # 设置SSE响应头
                self.send_response(200)
                self.send_header('Content-type', 'text/event-stream; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Connection', 'keep-alive')
                self.send_header('X-Accel-Buffering', 'no')  # 禁用Nginx缓冲
                self.end_headers()
                
                # 定义发送SSE消息的函数
                def send_sse_message(message_content, is_final=False):
                    try:
                        if is_final:
                            self.wfile.write(b"data: [DONE]\n\n")
                        else:
                            # 确保message_content是字符串
                            if not isinstance(message_content, str):
                                # 对于复杂对象，使用json.dumps转换
                                if isinstance(message_content, (dict, list)):
                                    message_content = json.dumps(message_content)
                                else:
                                    # 对于简单类型，使用str转换
                                    message_content = str(message_content)
                            sse_data = f"data: {message_content}\n\n"
                            self.wfile.write(sse_data.encode('utf-8'))
                        self.wfile.flush()
                        return True
                    except Exception as e:
                        logger.error(f"发送SSE消息失败: {e}")
                        return False
                
                # 获取AI回复（使用生成器方式）
                try:
                    # 导入AI服务
                    import asyncio
                    import os
                    from shared.utils.ai_service import get_ai_service
                    ai_service = get_ai_service()
                    
                    # 从环境变量获取交互模式，默认为stream
                    interaction_mode = os.getenv('AI_INTERACTION_MODE', 'stream')
                    
                    # 使用asyncio运行异步处理
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # 定义流式回调函数
                    async def stream_callback(chunk):
                        if chunk:
                            return send_sse_message(chunk, is_final=False)
                        return True
                    
                    # 修改的流式调用逻辑
                    async def stream_chat():
                        messages = [{"role": "user", "content": message}]
                        
                        # 直接调用内部方法来处理流式响应
                        try:
                            import httpx
                            import json
                            
                            # 构建请求参数
                            request_params = {
                                "model": ai_service.model,
                                "messages": messages,
                                "temperature": ai_service.temperature,
                                "max_tokens": ai_service.max_tokens,
                                "stream": True
                            }
                            
                            # 发起流式请求
                            async with httpx.AsyncClient(timeout=None) as client:
                                async with client.stream(
                                    "POST",
                                    f"{ai_service.api_url.rstrip('/')}/chat/completions",
                                    headers={
                                        "Authorization": f"Bearer {ai_service.api_key}",
                                        "Content-Type": "application/json"
                                    },
                                    json=request_params
                                ) as response:
                                    
                                    if response.status_code != 200:
                                        error_text = await response.text()
                                        await stream_callback(f"AI服务暂时不可用: {response.status_code} - {error_text}")
                                        # 非200状态码时也要发送结束标记
                                        send_sse_message("", is_final=True)
                                        return
                                    
                                    # 处理流式响应
                                    try:
                                        async for line in response.aiter_lines():
                                            if line.startswith('data: ') and line != 'data: [DONE]':
                                                # 解析JSON数据
                                                try:
                                                    data = json.loads(line[6:])  # 去掉 'data: ' 前缀
                                                    if 'choices' in data and data['choices']:
                                                        delta = data['choices'][0].get('delta', {})
                                                        if 'content' in delta:
                                                            content = delta['content']
                                                            # 确保content是字符串
                                                            if isinstance(content, str):
                                                                await stream_callback(content)
                                                            else:
                                                                # 如果不是字符串，转换为字符串
                                                                await stream_callback(str(content))
                                                except json.JSONDecodeError as json_error:
                                                    logger.warning(f"JSON解析失败: {json_error}, line: {line}")
                                                    continue
                                                except Exception as parse_error:
                                                    logger.warning(f"数据解析失败: {parse_error}")
                                                    continue
                                    except Exception as stream_error:
                                        logger.error(f"处理流式响应失败: {stream_error}")
                                        await stream_callback("处理流式响应时出现错误")
                                    finally:
                                        # 确保总是发送流结束标记
                                        send_sse_message("", is_final=True)
                            
                        except Exception as e:
                            logger.error(f"流式聊天时发生错误: {e}")
                            await stream_callback(f"对话失败: {str(e)}")
                            # 发生错误时也发送结束标记
                            send_sse_message("", is_final=True)
                    
                    try:
                        loop.run_until_complete(stream_chat())
                    except Exception as loop_error:
                        logger.error(f"执行聊天循环失败: {loop_error}")
                        send_sse_message("执行聊天时出现错误，请稍后重试")
                        send_sse_message("", is_final=True)
                    finally:
                        loop.close()
                        
                except Exception as e:
                    logger.error(f"获取AI回复失败: {e}")
                    # 发送错误信息
                    send_sse_message("抱歉，处理您的消息时出现错误，请稍后重试")
                    send_sse_message("", is_final=True)
                    
            elif self.path == '/chat/api/config':
                self._handle_config_api()
            elif self.path == '/api/validate-password':
                self._handle_validate_password()
            else:
                self.send_error(404, "API endpoint not found")
                
        except Exception as e:
            logger.error(f"处理聊天API失败: {e}")
            # 尝试使用SSE格式发送错误信息和结束标记
            try:
                # 检查是否已经发送了响应头
                if not hasattr(self, '_response_sent'):
                    self.send_response(200)
                    self.send_header('Content-type', 'text/event-stream; charset=utf-8')
                    self.send_header('Cache-Control', 'no-cache')
                    self.send_header('Connection', 'keep-alive')
                    self.send_header('X-Accel-Buffering', 'no')  # 禁用Nginx缓冲
                    self.end_headers()
                    self._response_sent = True
                
                # 发送错误信息和结束标记
                error_data = f"data: 服务器内部错误: {str(e)}\n\n"
                self.wfile.write(error_data.encode('utf-8'))
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
            except Exception as write_error:
                # 如果写入失败，可能是因为还没有发送响应头
                logger.error(f"发送SSE错误响应失败: {write_error}")
                # 尝试发送普通错误响应
                try:
                    self.send_error(500, "Internal server error")
                except Exception as send_error:
                    logger.error(f"发送错误响应失败: {send_error}")
    
    def _handle_integrated_index(self):
        """处理集成首页"""
        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # 生成集成首页
            html_content = self._generate_integrated_index_page()
            self.wfile.write(html_content.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"生成集成首页失败: {e}")
            self.send_error(500, "Internal server error")
    
    def _handle_favicon(self):
        """处理favicon请求"""
        try:
            # 获取项目根目录中的favicon.ico文件
            favicon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'favicon.ico')
            
            if not os.path.exists(favicon_path):
                self.send_error(404, "Favicon not found")
                return
            
            # 读取favicon文件
            with open(favicon_path, 'rb') as f:
                favicon_data = f.read()
            
            # 发送响应
            self.send_response(200)
            self.send_header('Content-type', 'image/x-icon')
            self.send_header('Content-Length', str(len(favicon_data)))
            self.send_header('Cache-Control', 'max-age=31536000')  # 缓存一年
            self.end_headers()
            self.wfile.write(favicon_data)
            
            logger.debug("Favicon请求已处理")
            
        except Exception as e:
            logger.error(f"处理favicon请求失败: {e}")
            self.send_error(500, "Internal server error")

    def _handle_config_api(self):
        """处理AI配置API请求"""
        try:
            if self.command == 'GET':
                # 获取配置
                import json
                from shared.utils.ai_service import get_ai_service
                ai_service = get_ai_service()
                config_info = ai_service.get_config_info()
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(config_info, ensure_ascii=False).encode('utf-8'))
            elif self.command == 'POST':
                # 保存配置
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(post_data)
                
                from shared.utils.ai_service import get_ai_service
                ai_service = get_ai_service()
                
                success = ai_service.save_config(
                    data.get('api_url', ''),
                    data.get('api_key', ''),
                    data.get('model', ''),
                    data.get('system_prompt', '')
                )
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                if success:
                    self.wfile.write(json.dumps({'success': True}, ensure_ascii=False).encode('utf-8'))
                else:
                    self.wfile.write(json.dumps({'success': False, 'error': '保存配置失败'}, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_error(405, "Method Not Allowed")
                
        except Exception as e:
            logger.error(f"处理配置API失败: {e}")
            import json
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({
                "api_url": "",
                "api_key_configured": False,
                "model": "",
                "system_prompt": "",
                "is_configured": False
            }, ensure_ascii=False).encode('utf-8'))
    
    def _handle_validate_password(self):
        """处理密码验证请求"""
        try:
            if self.command == 'POST':
                import json
                import os
                from dotenv import load_dotenv
                
                # 重新加载环境变量，确保使用最新的.env文件
                script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                env_file = os.path.join(script_dir, '.env')
                if os.path.exists(env_file):
                    load_dotenv(env_file)
                    logger.info(f"重新加载环境变量文件: {env_file}")
                
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(post_data)
                
                # 从环境变量获取配置密码
                config_password = os.getenv('CONFIG_PASSWORD', '')
                logger.info(f"从环境变量获取的CONFIG_PASSWORD: '{config_password}'")
                
                # 验证密码
                input_password = data.get('password', '').strip()
                logger.info(f"输入的密码: '{input_password}'")
                is_valid = input_password == config_password and config_password != ''
                logger.info(f"密码验证结果: {is_valid}")
                
                # 发送响应
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                if is_valid:
                    self.wfile.write(json.dumps({'success': True}, ensure_ascii=False).encode('utf-8'))
                else:
                    self.wfile.write(json.dumps({'success': False, 'error': '密码错误'}, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_error(405, "Method Not Allowed")
                
        except Exception as e:
            logger.error(f"处理密码验证失败: {e}")
            import json
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': '服务器内部错误'}, ensure_ascii=False).encode('utf-8'))
    
    def _handle_config_post(self):
        """处理保存AI配置请求"""
        try:
            import json
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            config_data = json.loads(post_data)
            
            from shared.utils.ai_service import get_ai_service
            ai_service = get_ai_service()
            
            # 保存配置
            success = ai_service.save_config(
                api_url=config_data.get('api_url'),
                api_key=config_data.get('api_key'),
                model=config_data.get('model'),
                system_prompt=config_data.get('system_prompt')
            )
            
            response = {"success": success}
            if not success:
                response["error"] = "保存配置失败"
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            logger.error(f"保存AI配置失败: {e}")
            import json
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False).encode('utf-8'))
    
    def _get_ai_reply(self, message: str) -> str:
        """获取AI回复"""
        try:
            # 导入AI服务
            try:
                import asyncio
                import os
                from shared.utils.ai_service import get_ai_service
                ai_service = get_ai_service()
                
                # 从环境变量获取交互模式，默认为stream
                interaction_mode = os.getenv('AI_INTERACTION_MODE', 'stream')
                
                # 使用asyncio运行异步处理
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    if interaction_mode == 'stream':
                        reply = loop.run_until_complete(ai_service.simple_chat(message, stream=True, timeout=4.5, source="page"))
                    else:
                        reply = loop.run_until_complete(ai_service.simple_chat(message, stream=False, source="page"))
                    return reply
                finally:
                    loop.close()
            except ImportError as e:
                logger.error(f"导入AI服务失败: {e}")
                return "抱歉，AI服务暂不可用，请稍后重试。"
        except Exception as e:
            logger.error(f"获取AI回复失败: {e}")
            return "抱歉，处理您的消息时出现错误，请稍后重试。"
    
    def _build_reply_xml(self, from_user: str, to_user: str, content: str) -> str:
        """构建回复XML"""
        import time
        timestamp = int(time.time())
        
        return f"""<xml>
<ToUserName><![CDATA[{from_user}]]></ToUserName>
<FromUserName><![CDATA[{to_user}]]></FromUserName>
<CreateTime>{timestamp}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""
    
    def _generate_chat_interface(self) -> str:
        """生成聊天界面HTML"""
        # 从templates文件夹读取HTML内容
        try:
            template_path = Path(__file__).parent.parent.parent / 'templates' / 'chat_template.html'
            with open(template_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 获取当前AI配置信息
            ai_config_info = "{}"
            try:
                import json
                from shared.utils.ai_service import get_ai_service
                ai_service = get_ai_service()
                ai_config_info = json.dumps(ai_service.get_config_info())
            except Exception as e:
                logger.error(f"获取AI配置信息失败: {e}")
            
            # 替换模板中的占位符（如果有的话）
            html_content = html_content.replace('{{ai_config_info}}', ai_config_info)
            
            return html_content
            
        except Exception as e:
            logger.error(f"读取聊天界面模板失败: {e}")
            # 返回简单的错误页面
            return f"<!DOCTYPE html><html><body><h1>错误</h1><p>无法加载聊天界面模板: {str(e)}</p></body></html>"
    
    def _generate_integrated_index_page(self) -> str:
        """生成集成首页"""
        try:
            # 获取静态页面列表
            pages_info = []
            # 检查self.static_page_manager是否存在且有list_pages方法
            if hasattr(self, 'static_page_manager') and self.static_page_manager and hasattr(self.static_page_manager, 'list_pages'):
                try:
                    # 调用list_pages方法
                    result = self.static_page_manager.list_pages()
                    
                    # 处理结果
                    if isinstance(result, dict):
                        if result.get('success', False):
                            pages_info = result.get('pages', [])
                        else:
                            pages_info = result.get('pages', [])
                    elif isinstance(result, list):
                        pages_info = result
                    else:
                        logger.warning(f"list_pages返回意外格式: {type(result)}")
                        pages_info = []
                except Exception as e:
                    logger.error(f"获取页面列表失败: {e}")
                    pages_info = []
            else:
                # static_page_manager不存在或没有list_pages方法，使用空列表
                pages_info = []
            
            # 按创建时间排序
            pages_info.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # 获取模板路径
            template_path = Path(__file__).parent.parent.parent / "templates" / "integrated_index_template.html"
            
            # 准备模板变量
            template_vars = {
                'title': '集成HTTP服务器',
                'wechat_verify_url': 'http://localhost:3004/wechat/verify',
                'pages_info': pages_info
            }
            
            # 使用模板渲染
            html = render_template(str(template_path), template_vars)
            
            return html
            
        except Exception as e:
            logger.error(f"生成集成首页失败: {e}")
            return "<h1>错误</h1><p>无法加载页面列表</p>"


class IntegratedStaticPageServer(StaticPageServer):
    """集成静态网页服务器，支持微信消息处理和聊天界面"""
    
    def __init__(self, pages_dir: str = "data/static_pages", port: int = 3004, static_page_manager=None):
        """
        初始化集成HTTP服务器
        
        Args:
            pages_dir: 静态网页存储目录
            port: 服务端口
            static_page_manager: 静态页面管理器实例
        """
        super().__init__(pages_dir, port)
        self.static_page_manager = static_page_manager
    
    def _create_handler(self, *args, **kwargs):
        """创建集成请求处理器"""
        return IntegratedStaticPageHandler(*args, static_page_manager=self.static_page_manager, **kwargs)