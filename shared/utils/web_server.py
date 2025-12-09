"""
静态网页HTTP服务器 - Flask版本
提供静态网页的HTTP访问服务，集成微信消息处理和聊天界面
"""
import logging
import os
import threading
import json
import hashlib
import re
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Any, Union

from flask import Flask, request, Response
from shared.utils.ai_service import get_ai_service

logger = logging.getLogger(__name__)


def my_render_template(template_path: str, variables: Dict[str, Any]) -> str:
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


class StaticPageServer:
    """静态网页HTTP服务器 - Flask版本"""
    
    def __init__(self, pages_dir: str = "data/static_pages", port: int = 3004):
        """
        初始化Flask服务器
        
        Args:
            pages_dir: 静态网页存储目录
            port: 服务端口
        """
        self.pages_dir = pages_dir
        self.port = port
        self.is_running = False
        self.server_thread = None
        
        # 从环境变量读取配置
        self.context_path = os.environ.get('CONTEXT_PATH', '').strip()
        # 确保contextPath以/开头，不以/结尾
        if self.context_path:
            if not self.context_path.startswith('/'):
                self.context_path = f'/{self.context_path}'
            if self.context_path.endswith('/'):
                self.context_path = self.context_path[:-1]
        
        # 获取监听地址和端口
        self.host = os.getenv('WECHAT_SERVER_HOST', '0.0.0.0')
        # 使用WECHAT_SERVER_PORT作为统一端口
        self.port = int(os.getenv('WECHAT_SERVER_PORT', str(port)))
        
        # 确保页面目录存在
        Path(self.pages_dir).mkdir(parents=True, exist_ok=True)
        
        # 创建Flask应用实例
        self.app = Flask(__name__)
        
        # 注册路由
        self._setup_routes()
    
    def _setup_routes(self):
        """设置Flask路由"""
        # 路由处理函数 - 接受可变参数以处理Flask路由匹配
        def handle_all_requests(**kwargs):
            """处理所有请求的统一入口"""
            # 始终从request.path获取完整请求路径
            full_path = request.path
            
            # 处理contextPath：如果设置了contextPath，则请求必须包含它
            if self.context_path:
                if not full_path.startswith(self.context_path):
                    return "Page not found", 404
                # 移除contextPath前缀
                path = full_path[len(self.context_path):]
                if not path:
                    path = '/'
            else:
                # 没有contextPath时，直接使用完整路径
                path = full_path
            
            # 根据请求方法分发处理
            if request.method == 'GET':
                return self._handle_get_request(path)
            elif request.method == 'POST':
                return self._handle_post_request(path)
            else:
                return "Method not allowed", 405
        
        # 注册路由：使用带contextPath的路由规则
        if self.context_path:
            # 如果设置了contextPath，则只注册带contextPath前缀的路由
            # 注意：Flask的路由会自动处理contextPath，我们只需要确保请求包含它
            # 我们不需要为每个路由单独添加contextPath前缀，因为handle_all_requests会处理
            self.app.add_url_rule(f'{self.context_path}/', methods=['GET', 'POST'], view_func=handle_all_requests)
            self.app.add_url_rule(f'{self.context_path}/<path:path>', methods=['GET', 'POST'], view_func=handle_all_requests)
        else:
            # 如果没有设置contextPath，则注册默认路由
            self.app.add_url_rule('/', methods=['GET', 'POST'], view_func=handle_all_requests)
            self.app.add_url_rule('/<path:path>', methods=['GET', 'POST'], view_func=handle_all_requests)
    
    def _handle_get_request(self, path):
        """处理GET请求"""
        try:
            # 路由处理
            if path == '/':
                # 首页：列出所有可用页面
                return self._generate_index_page()
            elif path.startswith('/pages/'):
                # 访问静态网页：/pages/filename.html
                return self._handle_static_page(path)
            elif path == '/chat':
                # 聊天界面
                return self._handle_chat_interface()
            elif path == '/api/config' or path == '/chat/api/config':
                # 配置API（支持直接访问和chat下访问）
                return self._handle_config_api()
            elif path == '/favicon.ico':
                # 网站图标
                return self._handle_favicon()
            elif path == '/wechat/verify':
                # 微信服务器验证
                return self._handle_wechat_verify()
            else:
                return "Page not found", 404
                
        except Exception as e:
            logger.error(f"处理GET请求失败: {e}")
            return "Internal server error", 500
    
    def _handle_post_request(self, path):
        """处理POST请求"""
        try:
            # 路由处理
            if path == '/api/chat' or path == '/chat/api/send':
                # 聊天API（支持直接访问和chat下访问）
                return self._handle_chat_api()
            elif path == '/api/config':
                # 配置保存API
                return self._handle_config_post()
            elif path == '/api/validate_password':
                # 密码验证API
                return self._handle_validate_password()
            elif path == '/wechat/verify':
                # 微信消息接收
                return self._handle_wechat_message()
            else:
                return "Method not allowed", 405
                
        except Exception as e:
            logger.error(f"处理POST请求失败: {e}")
            return "Internal server error", 500
    
    def _handle_static_page(self, request_path):
        """处理静态页面请求"""
        try:
            filename = request_path[7:]  # 去掉 '/pages/' 前缀
            
            # 安全检查：防止路径遍历攻击
            if '..' in filename or filename.startswith('/'):
                return "Forbidden", 403
            
            file_path = Path(self.pages_dir) / filename
            
            if not file_path.exists() or not file_path.is_file():
                return "File not found", 404
            
            # 设置内容类型
            if filename.endswith('.html'):
                # 读取并返回文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
            else:
                return "Only HTML files are supported", 400
                
        except Exception as e:
            logger.error(f"处理静态页面请求失败: {e}")
            return "Internal server error", 500
    
    def _generate_index_page(self):
        """生成索引页面"""
        try:
            # 读取元数据
            metadata_file = Path(self.pages_dir) / "metadata.json"
            pages = []
            
            if metadata_file.exists():
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
                'pages_url': f'{self.context_path}/pages/',
                'chat_url': f'{self.context_path}/chat'
            }
            
            # 使用模板渲染 - 传递字典参数
            html = my_render_template(str(template_path), template_vars)
            
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
                    <a href="{self.context_path}/pages/{filename}" class="page-link" target="_blank">访问页面</a>
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
            
            return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
            
        except Exception as e:
            logger.error(f"生成索引页面失败: {e}")
            return "<h1>错误</h1><p>无法加载页面列表</p>", 500
    
    def _handle_chat_interface(self):
        """处理聊天界面请求"""
        try:
            # 获取聊天模板路径
            template_path = Path(__file__).parent.parent.parent / "templates" / "chat_template.html"
            
            # 准备模板变量
            template_vars = {
                'context_path': self.context_path
            }
            
            # 使用模板渲染 - 传递字典参数
            html = my_render_template(str(template_path), template_vars)
            
            # 返回渲染后的内容
            return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
            
        except Exception as e:
            logger.error(f"处理聊天界面失败: {e}")
            return "<h1>错误</h1><p>无法加载聊天界面</p>", 500
    
    def _handle_config_api(self):
        """处理配置API请求"""
        try:
            # 从环境变量读取交互模式
            interaction_mode = os.getenv('OPENAI_INTERACTION_MODE', 'block').strip().lower()
            # 验证交互模式
            if interaction_mode not in ['stream', 'block']:
                interaction_mode = 'block'  # 默认使用阻塞模式
            
            # 获取AI服务实例和配置信息
            ai_service = get_ai_service()
            ai_config = ai_service.get_config_info()
            
            # 返回配置信息
            config = {
                'aiService': 'openai',
                'model': ai_config.get('model', 'gpt-3.5-turbo'),
                'interactionMode': interaction_mode
            }
            return json.dumps(config), 200, {'Content-Type': 'application/json'}
            
        except Exception as e:
            logger.error(f"处理配置API失败: {e}")
            return json.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'}
    
    def _handle_favicon(self):
        """处理favicon请求"""
        # 返回空响应
        return "", 200, {'Content-Type': 'image/x-icon'}
    
    def _handle_wechat_verify(self):
        """处理微信服务器验证"""
        try:
            # 获取查询参数
            signature = request.args.get('signature', '')
            timestamp = request.args.get('timestamp', '')
            nonce = request.args.get('nonce', '')
            echostr = request.args.get('echostr', '')
            
            # 从环境变量获取token
            token = os.getenv('WECHAT_TOKEN', 'default_token')
            
            # 验证签名
            temp_list = [token, timestamp, nonce]
            temp_list.sort()
            temp_str = ''.join(temp_list)
            sha1_hash = hashlib.sha1(temp_str.encode('utf-8')).hexdigest()
            
            if sha1_hash == signature:
                return echostr, 200, {'Content-Type': 'text/plain; charset=utf-8'}
            else:
                return "Signature verification failed", 403
                
        except Exception as e:
            logger.error(f"处理微信验证失败: {e}")
            return "Internal server error", 500
    
    def _handle_chat_api(self):
        """处理聊天API请求"""
        try:
            # 获取请求数据
            data = request.get_json()
            if not data:
                return json.dumps({'error': '无效的请求数据'}), 400, {'Content-Type': 'application/json'}
            
            # 获取用户消息
            user_message = data.get('message')
            if not user_message:
                return json.dumps({'error': '请提供消息内容'}), 400, {'Content-Type': 'application/json'}
            
            # 获取对话历史（可选）
            conversation_history = data.get('history', [])
            
            # 从环境变量读取交互模式
            interaction_mode = os.getenv('OPENAI_INTERACTION_MODE', 'block').strip().lower()
            # 验证交互模式
            if interaction_mode not in ['stream', 'block']:
                interaction_mode = 'block'  # 默认使用阻塞模式
            
            # 获取AI服务实例
            ai_service = get_ai_service()
            
            if interaction_mode == 'stream':
                # 流式响应处理 - 将异步生成器转换为同步可迭代对象
                def generate():
                    loop = None
                    try:
                        # 1. 创建事件循环
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        # 2. 定义异步函数来处理流式响应
                        async def fetch_stream():
                            try:
                                async for chunk in ai_service.stream_chat(
                                    user_message=user_message,
                                    conversation_history=conversation_history,
                                    source="page"  # 来源标记为页面访问
                                ):
                                    yield chunk
                            except Exception as e:
                                logger.error(f"流式响应异常: {e}")
                                raise
                        
                        # 3. 创建异步生成器
                        async_gen = fetch_stream()
                        
                        # 4. 手动迭代异步生成器
                        while True:
                            try:
                                # 使用事件循环运行单个异步操作
                                chunk = loop.run_until_complete(async_gen.__anext__())
                                # SSE格式: data: {chunk}
                                yield f"data: {json.dumps({'success': True, 'message': chunk, 'interaction_mode': 'stream'})}\n\n"
                            except StopAsyncIteration:
                                # 数据传输完成
                                break
                            except Exception as e:
                                logger.error(f"流式响应异常: {e}")
                                # 发送错误信息
                                yield f"data: {json.dumps({'error': str(e), 'success': False})}\n\n"
                                break
                    except Exception as e:
                        logger.error(f"流式响应初始化异常: {e}")
                        yield f"data: {json.dumps({'error': str(e), 'success': False})}\n\n"
                    finally:
                        # 确保事件循环被正确关闭
                        if loop is not None:
                            loop.close()
                
                # 返回SSE响应
                return Response(generate(), mimetype='text/event-stream')
            else:
                # 阻塞模式处理
                # 使用asyncio运行异步方法
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # 调用AI服务获取回复
                    ai_reply = loop.run_until_complete(
                        ai_service.simple_chat(
                            user_message=user_message,
                            conversation_history=conversation_history,
                            source="page",  # 来源标记为页面访问
                            stream=False  # 阻塞模式
                        )
                    )
                finally:
                    loop.close()
                
                # 返回AI回复
                return json.dumps({
                    'success': True,
                    'message': ai_reply,
                    'interaction_mode': interaction_mode
                }), 200, {'Content-Type': 'application/json'}
            
        except Exception as e:
            logger.error(f"处理聊天API失败: {e}")
            return json.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'}
    
    def _handle_config_post(self):
        """处理配置保存请求"""
        try:
            # 获取请求数据
            data = request.get_json()
            if not data:
                return json.dumps({'error': '无效的请求数据'}), 400, {'Content-Type': 'application/json'}
            
            # 从请求数据中提取配置参数
            api_url = data.get('api_url', '')
            api_key = data.get('api_key', '')
            model = data.get('model', '')
            system_prompt = data.get('system_prompt', '')
            
            # 验证必要参数
            if not all([api_url, api_key, model]):
                return json.dumps({'error': '缺少必要的配置参数'}), 400, {'Content-Type': 'application/json'}
            
            # 获取AI服务实例并保存配置
            ai_service = get_ai_service()
            success = ai_service.save_config(api_url, api_key, model, system_prompt)
            
            if success:
                return json.dumps({'success': True, 'message': '配置保存成功'}), 200, {'Content-Type': 'application/json'}
            else:
                return json.dumps({'error': '配置保存失败'}), 500, {'Content-Type': 'application/json'}
            
        except Exception as e:
            logger.error(f"处理配置保存请求失败: {e}")
            return json.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'}
    
    def _handle_validate_password(self):
        """处理密码验证请求"""
        try:
            # 获取请求数据
            data = request.get_json()
            password = data.get('password', '')
            # 示例实现，仅返回成功响应
            return json.dumps({'success': True, 'message': 'Password validated'}), 200, {'Content-Type': 'application/json'}
            
        except Exception as e:
            logger.error(f"处理密码验证请求失败: {e}")
            return json.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'}
    
    def _handle_wechat_message(self):
        """处理微信消息"""
        try:
            # 获取请求数据
            xml_data = request.data
            # 示例实现，仅返回成功响应
            return "success", 200, {'Content-Type': 'text/plain; charset=utf-8'}
            
        except Exception as e:
            logger.error(f"处理微信消息失败: {e}")
            return "Internal server error", 500
    
    def start(self):
        """启动Flask服务器"""
        try:
            if self.is_running:
                logger.warning("服务器已经在运行中")
                return False
            
            # 在单独的线程中启动服务器
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            logger.info(f"静态网页HTTP服务器启动成功")
            logger.info(f"服务地址: http://{self.host}:{self.port}")
            logger.info(f"静态网页目录: {self.pages_dir}")
            logger.info(f"页面访问格式: http://{self.host}:{self.port}{self.context_path}/pages/文件名.html")
            
            self.is_running = True
            return True
            
        except Exception as e:
            logger.error(f"启动HTTP服务器失败: {e}")
            self.is_running = False
            return False
    
    def _run_server(self):
        """在独立线程中运行服务器"""
        try:
            logger.info(f"HTTP服务器线程启动，监听地址 {self.host}，端口 {self.port}")
            # 启动Flask服务器
            self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
        except Exception as e:
            logger.error(f"HTTP服务器运行异常: {e}")
        finally:
            self.is_running = False
    
    def stop(self):
        """停止HTTP服务器"""
        try:
            if not self.is_running:
                logger.warning("服务器未在运行中")
                return False
            
            # Flask开发服务器无法优雅停止，这里只能设置状态为停止
            self.is_running = False
            logger.info("静态网页HTTP服务器已停止")
            return True
        except Exception as e:
            logger.error(f"停止HTTP服务器失败: {e}")
            return False
    
    def get_status(self) -> dict:
        """获取服务器状态"""
        return {
            "is_running": self.is_running,
            "port": self.port,
            "pages_dir": self.pages_dir,
            "server_url": f"http://{self.host}:{self.port}{self.context_path}" if self.is_running else None
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
        
        return f"http://{self.host}:{self.port}{self.context_path}/pages/{filename}"


class IntegratedStaticPageServer(StaticPageServer):
    """集成静态网页服务器，支持微信消息处理和聊天界面"""
    
    def __init__(self, pages_dir: str = "data/static_pages", port: int = 3004, static_page_manager=None):
        """
        初始化集成服务器
        
        Args:
            pages_dir: 静态网页存储目录
            port: 服务端口
            static_page_manager: 静态页面管理器实例
        """
        super().__init__(pages_dir=pages_dir, port=port)
        self.static_page_manager = static_page_manager
    
    def _generate_index_page(self):
        """生成索引页面 - 集成版本"""
        try:
            # 使用静态页面管理器获取页面列表
            pages = []
            if self.static_page_manager:
                pages_info = self.static_page_manager.list_pages()
                pages = pages_info.get('pages', [])
            
            # 按创建时间排序
            pages.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # 获取模板路径
            template_path = Path(__file__).parent.parent.parent / "templates" / "index_template.html"
            
            # 准备模板变量
            template_vars = {
                'title': '静态网页服务',
                'subtitle': '生成和管理静态HTML网页的HTTP访问服务',
                'pages_url': f'{self.context_path}/pages/',
                'chat_url': f'{self.context_path}/chat'
            }
            
            # 使用模板渲染 - 传递字典参数
            html = my_render_template(str(template_path), template_vars)
            
            # 生成页面列表
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
                    <a href="{self.context_path}/pages/{filename}" class="page-link" target="_blank">访问页面</a>
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
            
            return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
            
        except Exception as e:
            logger.error(f"生成索引页面失败: {e}")
            return "<h1>错误</h1><p>无法加载页面列表</p>", 500


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