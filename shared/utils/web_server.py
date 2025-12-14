"""
Web 服务器 - Flask版本
提供静态网页的HTTP访问服务，集成微信消息处理和聊天界面
"""
import logging
import os
import threading
import json
import hashlib
import re
import asyncio
import time
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from xml.etree import ElementTree as ET

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
        
        # 处理带默认值的变量替换
        # 正则表达式匹配 {{ variable or 'default' }} 或 {{ variable or "default" }}
        # 注意：使用负断言确保 or 前后不是单词字符或点号，避免匹配到其他单词的一部分（如 formatted 中的 or）
        def replace_default_var(match):
            var_name = match.group(1).strip()
            default_value = match.group(2).strip()
            # 移除默认值的引号
            if (default_value.startswith("'") and default_value.endswith("'") or \
               (default_value.startswith('"') and default_value.endswith('"'))):
                default_value = default_value[1:-1]
            # 处理点表示法，支持嵌套dict和对象属性
            try:
                value = variables
                for part in var_name.split('.'):
                    if isinstance(value, dict):
                        value = value.get(part)
                    elif hasattr(value, part):
                        value = getattr(value, part)
                    else:
                        value = None
                        break
                    if value is None:
                        break
                return str(value) if value is not None else default_value
            except (AttributeError, TypeError):
                return default_value
        
        # 处理普通变量替换（包括点表示法）
        def replace_regular_var(match):
            var_name = match.group(1).strip()
            # 处理点表示法，如 page.filename，支持嵌套dict和对象属性
            try:
                value = variables
                for part in var_name.split('.'):
                    if isinstance(value, dict):
                        value = value.get(part)
                    elif hasattr(value, part):
                        value = getattr(value, part)
                    else:
                        value = None
                        break
                    if value is None:
                        break
                return str(value) if value is not None else ''
            except (AttributeError, TypeError):
                return ''
        
        # 简单的条件判断处理，支持点表示法
        def replace_if(match):
            condition = match.group(1).strip()
            if_content = match.group(2)
            
            # 处理点表示法的条件变量，例如 pagination_html
            try:
                value = variables
                for part in condition.split('.'):
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        value = getattr(value, part, None)
                    if value is None:
                        break
                
                # 检查值是否为真（非None、非空字符串、非空列表等）
                if value:
                    return if_content
                return ""
            except (AttributeError, TypeError):
                return ""
        
        # 简单的循环处理（for page in pages_info）
        def replace_for_loop(match):
            loop_var = match.group(1)
            list_var = match.group(2)
            loop_content = match.group(3)
            
            # 获取循环数据
            try:
                items = variables
                for part in list_var.split('.'):
                    if isinstance(items, dict):
                        items = items.get(part)
                    else:
                        items = getattr(items, part, None)
                    if items is None:
                        break
                items = items or []
            except (AttributeError, TypeError):
                items = []
            
            result = ""
            for item in items:
                # 为每个item创建上下文
                item_context = variables.copy()
                item_context[loop_var] = item
                
                # 替换item中的变量
                item_html = loop_content
                
                # 先处理item中的带默认值变量
                # 注意：使用负断言确保 or 前后不是单词字符或点号，避免匹配到其他单词的一部分（如 formatted 中的 or）
                def replace_item_default_var(match):
                    var_name = match.group(1).strip()
                    default_value = match.group(2).strip()
                    # 移除默认值的引号
                    if (default_value.startswith("'") and default_value.endswith("'") or \
                       (default_value.startswith('"') and default_value.endswith('"'))):
                        default_value = default_value[1:-1]
                    # 从item_context中获取值
                    try:
                        value = item_context
                        for part in var_name.split('.'):
                            if isinstance(value, dict):
                                value = value.get(part)
                            elif hasattr(value, part):
                                value = getattr(value, part)
                            else:
                                value = None
                                break
                            if value is None:
                                break
                        return str(value) if value is not None else default_value
                    except (AttributeError, TypeError):
                        return default_value
                
                item_html = re.sub(r'\{\{\s*([\w.]+)\s*(?<![\w.])or(?![\w.])\s*([^}]+)\s*\}\}', replace_item_default_var, item_html)
                
                # 然后处理item中的普通变量（包括点表示法）
                def replace_item_var(match):
                    var_name = match.group(1).strip()
                    try:
                        value = item_context
                        for part in var_name.split('.'):
                            if isinstance(value, dict):
                                value = value.get(part)
                            elif hasattr(value, part):
                                value = getattr(value, part)
                            else:
                                value = None
                                break
                            if value is None:
                                break
                        return str(value) if value is not None else ''
                    except (AttributeError, TypeError):
                        return ''
                
                item_html = re.sub(r'\{\{\s*([\w.]+)\s*\}\}', replace_item_var, item_html)
                
                result += item_html
            
            return result
        
        # 渲染顺序：先处理循环，再处理变量替换，最后处理条件判断
        # 1. 先处理循环
        html = re.sub(r'\{\%\s*for\s+(\w+)\s+in\s+([\w.]+)\s*\%\}(.*?)\{\%\s*endfor\s*\%\}', 
                     replace_for_loop, template, flags=re.DOTALL)
        
        # 2. 处理模板级别的变量（非循环内的）
        html = re.sub(r'\{\{\s*([\w.]+)\s*(?<![\w.])or(?![\w.])\s*([^}]+)\s*\}\}', replace_default_var, html)
        html = re.sub(r'\{\{\s*([\w.]+)\s*\}\}', replace_regular_var, html)
        
        # 3. 处理条件判断（支持点表示法）
        # 先处理有else的情况
        def replace_if_with_else(match):
            condition = match.group(1).strip()
            if_content = match.group(2)
            else_content = match.group(3)
            
            # 处理点表示法的条件变量，例如 pagination_html
            try:
                value = variables
                for part in condition.split('.'):
                    if isinstance(value, dict):
                        value = value.get(part)
                    elif hasattr(value, part):
                        value = getattr(value, part)
                    else:
                        value = None
                        break
                    if value is None:
                        break
                
                # 检查值是否为真（非None、非空字符串、非空列表等）
                if value:
                    return if_content
                return else_content
            except (AttributeError, TypeError):
                return else_content
        
        # 处理有else的条件判断
        html = re.sub(r'\{\%\s*if\s+([\w.]+)\s*\%\}(.*?)\{\%\s*else\s*\%\}(.*?)\{\%\s*endif\s*\%\}', 
                     replace_if_with_else, html, flags=re.DOTALL)
        
        # 处理没有else的条件判断
        html = re.sub(r'\{\%\s*if\s+([\w.]+)\s*\%\}(.*?)\{\%\s*endif\s*\%\}', 
                     replace_if, html, flags=re.DOTALL)
        
        return html
        
    except Exception as e:
        logger.error(f"模板渲染失败 {template_path}: {e}")
        return f"<h1>模板渲染失败</h1><p>错误: {e}</p>"


class StaticPageServer:
    """Web 服务器 - Flask版本"""
    
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
        self.context_path = os.environ.get('WECHAT_MSG_CONTEXT_PATH', '').strip()
        # 确保contextPath以/开头，不以/结尾
        if self.context_path:
            if not self.context_path.startswith('/'):
                self.context_path = f'/{self.context_path}'
            if self.context_path.endswith('/'):
                self.context_path = self.context_path[:-1]
        
        # 获取监听地址和端口
        self.host = os.getenv('WECHAT_MSG_SERVER_HOST', '0.0.0.0')
        # 使用WECHAT_MSG_SERVER_PORT作为统一端口
        self.port = int(os.getenv('WECHAT_MSG_SERVER_PORT', str(port)))
        
        # 确保页面目录存在
        Path(self.pages_dir).mkdir(parents=True, exist_ok=True)
        
        # 创建Flask应用实例
        self.app = Flask(__name__)
        
        # 微信消息处理相关配置
        # 微信消息AI响应缓存时间（秒）
        self.wechat_msg_ai_cache_time = int(os.getenv('WECHAT_MSG_AI_CACHE_TIME', '60'))
        # 微信消息AI处理超时时间（秒）
        self.wechat_msg_ai_timeout = float(os.getenv('WECHAT_MSG_AI_TIMEOUT', '15'))
        # 微信消息AI响应长度限制
        self.wechat_msg_ai_len_limit = int(os.getenv('WECHAT_MSG_AI_LEN_LIMIT', '600'))
        # 微信消息AI超时提示
        self.wechat_msg_ai_timeout_prompt = os.getenv('WECHAT_MSG_AI_TIMEOUT_PROMPT', '100')
        # 微信消息AI缓存大小限制
        self.wechat_msg_ai_cache_size = int(os.getenv('WECHAT_MSG_AI_CACHE_SIZE', '100'))
        
        # 微信消息缓存结构: {msg_id: {"content": "响应内容", "expire_time": "过期时间"}}
        self.wechat_msg_cache = {}
        # 微信消息锁结构: {msg_id: threading.Lock()}
        self.wechat_msg_locks = {}
        # 锁的锁，用于保护wechat_msg_locks的访问
        self.wechat_msg_locks_lock = threading.Lock()
        
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
                # 首页：显示静态存储信息
                return self._generate_index_page()
            elif path == '/static-pages/':
                # 静态网页列表页面
                return self._generate_static_pages_list()
            elif path.startswith('/pages/'):
                # 访问静态网页：/pages/filename.html
                return self._handle_static_page(path)
            elif path == '/chat/':
                # 聊天界面
                return self._handle_chat_interface()
            elif path == '/api/config' or path == '/chat/api/config':
                # 配置API（支持直接访问和chat下访问）
                return self._handle_config_api()
            elif path == '/favicon.ico':
                # 网站图标
                return self._handle_favicon()
            elif path == '/wechat/reply':
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
                # 配置API，由_handle_config_api统一处理GET和POST
                return self._handle_config_api()
            elif path == '/api/validate-password':
                # 密码验证请求
                return self._handle_validate_password()
            elif path == '/wechat/reply':
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
            
            # 获取存储统计信息
            stats = {
                'total_files': len(pages),
                'total_size': sum(page.get('file_size', 0) for page in pages),
                'earliest_created': None,
                'latest_created': None
            }
            
            if pages:
                created_times = [page.get('created_at', '') for page in pages if page.get('created_at')]
                created_times.sort()
                if created_times:
                    stats['earliest_created'] = created_times[0]
                    stats['latest_created'] = created_times[-1]
            
            # 格式化文件大小
            def format_file_size(size_bytes):
                if size_bytes == 0:
                    return "0 B"
                units = ['B', 'KB', 'MB', 'GB']
                unit_index = 0
                size = float(size_bytes)
                
                while size >= 1024 and unit_index < len(units) - 1:
                    size /= 1024
                    unit_index += 1
                
                return f"{size:.2f} {units[unit_index]}"
            
            # 获取模板路径
            template_path = Path(__file__).parent.parent.parent / "templates" / "index_template.html"
            
            # 准备模板变量
            template_vars = {
                'title': '静态网页服务',
                'subtitle': '生成和管理静态HTML网页的HTTP访问服务',
                'pages_url': f'{self.context_path}/pages/',
                'chat_url': f'{self.context_path}/chat',
                'total_files': stats['total_files'],
                'total_size': format_file_size(stats['total_size']),
                'earliest_created': stats['earliest_created'],
                'latest_created': stats['latest_created']
            }
            
            # 使用模板渲染 - 传递字典参数
            html = my_render_template(str(template_path), template_vars)
            
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
        """处理配置API请求，支持GET获取配置和POST保存配置"""
        try:
            if request.method == 'POST':
                # 处理配置保存请求
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
            else:  # GET请求
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
    
    def _verify_wechat_signature(self):
        """验证微信签名"""
        try:
            # 获取参数（GET请求从args获取，POST请求从args获取）
            signature = request.args.get('signature', '')
            timestamp = request.args.get('timestamp', '')
            nonce = request.args.get('nonce', '')
            
            # 从环境变量获取token
            token = os.getenv('WECHAT_TOKEN')
            if not token:
                logger.error("WECHAT_TOKEN环境变量未配置")
                return False
            
            # 验证签名
            temp_list = [token, timestamp, nonce]
            temp_list.sort()
            temp_str = ''.join(temp_list)
            sha1_hash = hashlib.sha1(temp_str.encode('utf-8')).hexdigest()
            
            return sha1_hash == signature
            
        except Exception as e:
            logger.error(f"验证微信签名失败: {e}")
            return False
    
    def _handle_wechat_verify(self):
        """处理微信服务器验证"""
        try:
            # 验证签名
            if self._verify_wechat_signature():
                # 获取echostr并返回
                echostr = request.args.get('echostr', '')
                return echostr, 200, {'Content-Type': 'text/plain; charset=utf-8'}
            else:
                return "Signature verification failed", 403
                
        except Exception as e:
            logger.error(f"处理微信验证失败: {e}")
            return "Internal server error", 500
    
    def _handle_chat_api(self):
        """处理聊天API请求"""
        import time
        start_time = time.time()
        
        try:
            # 获取请求数据 - 这是第一个瓶颈点
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
            
            # 获取AI服务实例 - 全局单例，避免重复创建
            ai_service = get_ai_service()
                        
            if interaction_mode == 'stream':
                # 流式响应处理 - 优化事件循环管理
                def generate():
                    # 确保每个线程都有自己的事件循环
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                                        
                    # 直接调用ai_service.stream_chat，减少中间层嵌套
                    async def stream_wrapper():
                        try:
                            async for chunk in ai_service.stream_chat(
                                user_message=user_message,
                                conversation_history=conversation_history
                            ):
                                yield f"data: {json.dumps({'success': True, 'message': chunk, 'interaction_mode': 'stream'})}\n\n"
                        except Exception as e:
                            logger.error(f"流式响应异常: {e}")
                            yield f"data: {json.dumps({'error': str(e), 'success': False})}\n\n"
                    
                    # 运行异步生成器
                    async_gen = stream_wrapper()
                    
                    while True:
                        try:
                            chunk = loop.run_until_complete(async_gen.__anext__())
                            yield chunk
                        except StopAsyncIteration:
                            break
                        except Exception as e:
                            logger.error(f"流式响应迭代异常: {e}")
                            break
                
                # 返回SSE响应
                return Response(generate(), mimetype='text/event-stream')
            else:
                # 阻塞模式处理 - 确保每个线程都有自己的事件循环
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                try:
                    # 调用AI服务获取回复
                    ai_reply = loop.run_until_complete(
                        ai_service.simple_chat(
                            user_message=user_message,
                            conversation_history=conversation_history,
                            stream=False  # 阻塞模式
                        )
                    )
                except Exception as e:
                    logger.error(f"阻塞模式调用异常: {e}")
                    return json.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'}
                
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
            # 从环境变量获取配置密码
            openai_config_password = os.getenv('OPENAI_CONFIG_PASSWORD')
            
            # 验证密码
            if openai_config_password and password == openai_config_password:
                return json.dumps({'success': True, 'message': 'Password validated'}), 200, {'Content-Type': 'application/json'}
            else:
                return json.dumps({'success': False, 'message': 'Invalid password'}), 401, {'Content-Type': 'application/json'}
            
        except Exception as e:
            logger.error(f"处理密码验证请求失败: {e}")
            return json.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'}
    
    def _clean_expired_cache(self):
        """清理过期的缓存项"""
        current_time = time.time()
        expired_keys = [msg_id for msg_id, cache_item in self.wechat_msg_cache.items() 
                      if cache_item['expire_time'] < current_time]
        for msg_id in expired_keys:
            del self.wechat_msg_cache[msg_id]
    
    def _get_cache_item(self, msg_id):
        """获取缓存项，如果不存在或已过期返回None"""
        self._clean_expired_cache()  # 先清理过期缓存
        cache_item = self.wechat_msg_cache.get(msg_id)
        if cache_item and cache_item['expire_time'] > time.time():
            return cache_item['content']
        return None
    
    def _set_cache_item(self, msg_id, content):
        """设置缓存项"""
        # 先清理过期缓存
        self._clean_expired_cache()
        
        # 如果缓存项已存在，先删除它（这样会将其移到字典末尾，相当于更新访问时间）
        if msg_id in self.wechat_msg_cache:
            del self.wechat_msg_cache[msg_id]
        
        # 检查缓存大小是否超过限制
        if len(self.wechat_msg_cache) >= self.wechat_msg_ai_cache_size:
            # 删除最早添加的缓存项（字典保持插入顺序）
            oldest_msg_id = next(iter(self.wechat_msg_cache))
            del self.wechat_msg_cache[oldest_msg_id]
        
        # 添加新的缓存项
        expire_time = time.time() + self.wechat_msg_ai_cache_time
        self.wechat_msg_cache[msg_id] = {
            "content": content,
            "expire_time": expire_time
        }
    
    def _get_or_create_lock(self, msg_id):
        """获取或创建消息锁"""
        with self.wechat_msg_locks_lock:
            if msg_id not in self.wechat_msg_locks:
                self.wechat_msg_locks[msg_id] = threading.Lock()
            return self.wechat_msg_locks[msg_id]
    
    def _build_wechat_response_xml(self, from_user: str, to_user: str, content: str) -> str:
        """
        构建微信文本消息响应的XML格式
        
        Args:
            from_user: 消息来源用户（微信用户的OpenID）
            to_user: 消息目标用户（公众号的原始ID）
            content: 回复内容
            
        Returns:
            格式化的XML响应字符串
        """
        return f"""<?xml version="1.0" encoding="UTF-8"?>
                    <xml>
                        <ToUserName><![CDATA[{from_user}]]></ToUserName>
                        <FromUserName><![CDATA[{to_user}]]></FromUserName>
                        <CreateTime>{int(time.time())}</CreateTime>
                        <MsgType><![CDATA[text]]></MsgType>
                        <Content><![CDATA[{content}]]></Content>
                    </xml>"""
    
    def _handle_wechat_message(self):
        """处理微信消息，调用AI服务自动回复"""
        try:
            # 1. 验证微信签名
            if not self._verify_wechat_signature():
                return "Signature verification failed", 403
            
            # 2. 解析微信发来的XML消息
            xml_data = request.data.decode('utf-8')
            
            # 解析XML
            root = ET.fromstring(xml_data)
            
            # 提取消息类型
            msg_type = root.find('MsgType').text if root.find('MsgType') is not None else ''
            
            # 3. 只处理文本消息
            if msg_type == 'text':
                # 提取消息内容和其他必要信息
                to_user = root.find('ToUserName').text if root.find('ToUserName') is not None else ''
                from_user = root.find('FromUserName').text if root.find('FromUserName') is not None else ''
                create_time = root.find('CreateTime').text if root.find('CreateTime') is not None else ''
                content = root.find('Content').text if root.find('Content') is not None else ''
                msg_id = root.find('MsgId').text if root.find('MsgId') is not None else ''
                
                logger.info(f"收到微信消息: 来自{from_user}, 内容: {content}, MsgId: {msg_id}")
                
                # 4. 检查缓存
                cached_response = self._get_cache_item(msg_id)
                if cached_response:
                    logger.info(f"使用缓存的微信消息响应: MsgId={msg_id}")
                    # 5. 生成微信响应XML
                    response_xml = self._build_wechat_response_xml(from_user, to_user, cached_response)
                    return response_xml, 200, {'Content-Type': 'application/xml; charset=utf-8'}
                
                # 5. 获取或创建消息锁
                msg_lock = self._get_or_create_lock(msg_id)
                
                # 6. 尝试获取锁，处理超时情况
                if not msg_lock.acquire(timeout=self.wechat_msg_ai_timeout):
                    logger.warning(f"获取微信消息锁超时: MsgId={msg_id}")
                    # 锁超时，返回默认回复
                    default_response = "抱歉，当前请求量较大，请稍后再试"
                    # 缓存默认回复
                    self._set_cache_item(msg_id, default_response)
                    response_xml = self._build_wechat_response_xml(from_user, to_user, default_response)
                    return response_xml, 200, {'Content-Type': 'application/xml; charset=utf-8'}
                
                try:
                    # 再次检查缓存，防止在获取锁的过程中其他线程已经处理了该消息
                    cached_response = self._get_cache_item(msg_id)
                    if cached_response:
                        logger.info(f"使用缓存的微信消息响应: MsgId={msg_id}")
                        response_xml = self._build_wechat_response_xml(from_user, to_user, cached_response)
                        return response_xml, 200, {'Content-Type': 'application/xml; charset=utf-8'}
                    
                    # 7. 调用AI服务获取回复
                    ai_service = get_ai_service()
                    
                    # 确保每个线程都有自己的事件循环
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # 从环境变量获取交互模式，默认为stream
                    interaction_mode = os.getenv('OPENAI_INTERACTION_MODE', 'stream').strip().lower()
                    # 验证交互模式
                    if interaction_mode not in ['stream', 'block']:
                        interaction_mode = 'block'  # 默认使用阻塞模式
                    
                    # 根据交互模式调用不同的AI服务方法
                    if interaction_mode == 'stream':
                        # stream模式：使用stream_chat方法
                        def stream_wrapper():
                            async def collect_stream():
                                collected = []
                                try:
                                    # 使用asyncio.wait_for设置超时
                                    async def collect_with_timeout():
                                        async for chunk in ai_service.stream_chat(
                                            user_message=content,
                                            conversation_history=[]  # 微信公众号暂时不支持上下文
                                        ):
                                            collected.append(chunk)
                                            # 检查是否超过长度限制
                                            if len(''.join(collected)) >= self.wechat_msg_ai_len_limit:
                                                collected.append("..." + self.wechat_msg_ai_timeout_prompt)
                                                break
                                    
                                    await asyncio.wait_for(collect_with_timeout(), timeout=self.wechat_msg_ai_timeout)
                                except asyncio.TimeoutError:
                                    logger.warning(f"微信消息AI响应超时: MsgId={msg_id}")
                                    # 添加超时提示
                                    if len(''.join(collected)) < self.wechat_msg_ai_len_limit:
                                        collected.append(self.wechat_msg_ai_timeout_prompt)
                                except Exception as e:
                                    logger.error(f"微信消息AI响应异常: {e}")
                                    collected.append(f"\n\n[响应异常: {str(e)}]")
                                
                                return ''.join(collected)
                            return collect_stream()
                        
                        ai_reply = loop.run_until_complete(stream_wrapper())
                    else:
                        # block模式：使用simple_chat方法
                        try:
                            # 使用asyncio.wait_for设置超时
                            ai_reply = loop.run_until_complete(asyncio.wait_for(
                                ai_service.simple_chat(
                                    user_message=content,
                                    conversation_history=[]  # 微信公众号暂时不支持上下文
                                ),
                                timeout=self.wechat_msg_ai_timeout
                            ))
                        except asyncio.TimeoutError:
                            logger.warning(f"微信消息AI响应超时: MsgId={msg_id}")
                            ai_reply = "抱歉，当前AI服务响应超时，请稍后再试"
                        except Exception as e:
                            logger.error(f"微信消息AI响应异常: {e}")
                            ai_reply = f"抱歉，当前AI服务响应异常: {str(e)}"
                    
                    # 8. 处理响应长度限制
                    if len(ai_reply) > self.wechat_msg_ai_len_limit:
                        ai_reply = ai_reply[:self.wechat_msg_ai_len_limit] + "..." + self.wechat_msg_ai_timeout_prompt
                    
                    # 9. 缓存响应
                    self._set_cache_item(msg_id, ai_reply)
                    
                    # 10. 生成微信响应XML
                    response_xml = self._build_wechat_response_xml(from_user, to_user, ai_reply)
                    
                    return response_xml, 200, {'Content-Type': 'application/xml; charset=utf-8'}
                finally:
                    # 释放锁
                    msg_lock.release()
            else:
                # 非文本消息，返回空响应
                return "success", 200, {'Content-Type': 'text/plain; charset=utf-8'}
            
        except Exception as e:
            logger.error(f"处理微信消息失败: {e}")
            # 微信服务器要求即使出错也返回success，否则会重试
            return "success", 200, {'Content-Type': 'text/plain; charset=utf-8'}
    
    def start(self):
        """启动Flask服务器"""
        try:
            if self.is_running:
                logger.warning("服务器已经在运行中")
                return False
            
            # 在单独的线程中启动服务器
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            logger.info(f"Web 服务器启动成功")
            logger.info(f"服务地址: http://{self.host}:{self.port}{self.context_path}/")
            logger.info(f"静态网页目录: {self.pages_dir}")
            logger.info(f"页面访问格式: http://{self.host}:{self.port}{self.context_path}/pages/文件名.html")
            
            self.is_running = True
            return True
            
        except Exception as e:
            logger.error(f"启动Web服务器失败: {e}")
            self.is_running = False
            return False
    
    def _run_server(self):
        """在独立线程中运行服务器"""
        try:
            logger.info(f"Web服务器线程启动，监听地址 {self.host}，端口 {self.port}")
            
            # 使用pywsgi WSGI服务器运行Flask应用
            try:
                from gevent.pywsgi import WSGIServer
                # 创建WSGI服务器实例
                http_server = WSGIServer((self.host, self.port), self.app)
                # 启动服务器
                http_server.serve_forever()
            except ImportError:
                # 如果pywsgi不可用，回退到Flask开发服务器
                logger.warning("gevent.pywsgi未安装，回退到Flask开发服务器")
                # 禁用Werkzeug的开发服务器警告
                import logging
                werkzeug_logger = logging.getLogger('werkzeug')
                werkzeug_logger.setLevel(logging.ERROR)
                # 启动Flask服务器
                self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
        except Exception as e:
            logger.error(f"Web服务器运行异常: {e}")
        finally:
            self.is_running = False
    
    def stop(self):
        """停止Web服务器"""
        try:
            if not self.is_running:
                logger.warning("服务器未在运行中")
                return False
            
            # Flask开发服务器无法优雅停止，这里只能设置状态为停止
            self.is_running = False
            logger.info("Web 服务器已停止")
            return True
        except Exception as e:
            logger.error(f"停止Web服务器失败: {e}")
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
    """集成Web服务器，支持微信消息处理和聊天界面"""
    
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
    
    def _generate_static_pages_list(self):
        """生成静态网页列表页面，包含页面头、分页显示和美化列表"""
        try:
            from pathlib import Path
            
            # 默认分页参数
            page = 1
            per_page = 10
            
            # 获取页面列表
            pages = []
            if self.static_page_manager:
                pages_info = self.static_page_manager.list_pages()
                pages = pages_info.get('pages', [])
            
            # 按创建时间倒序排序
            pages.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # 计算总页数
            total_pages = (len(pages) + per_page - 1) // per_page
            
            # 获取当前页的数据
            start = (page - 1) * per_page
            end = start + per_page
            current_pages = pages[start:end]
            
            # 格式化文件大小的辅助函数
            def format_file_size(size_bytes):
                if size_bytes == 0:
                    return "0 B"
                units = ['B', 'KB', 'MB', 'GB']
                unit_index = 0
                size = float(size_bytes)
                
                while size >= 1024 and unit_index < len(units) - 1:
                    size /= 1024
                    unit_index += 1
                
                return f"{size:.2f} {units[unit_index]}"
            
            # 计算总文件大小 - 使用 current_size 优先，如果为0则使用 file_size
            total_file_size = sum(page.get('current_size', page.get('file_size', 0)) for page in pages)
            total_size_formatted = format_file_size(total_file_size)
            
            # 格式化每个页面的文件大小 - 使用 current_size 优先，如果为0则使用 file_size
            for page in current_pages:
                file_size = page.get('current_size', page.get('file_size', 0))
                page['file_size_formatted'] = format_file_size(file_size)
            
            # 生成分页HTML
            pagination_html = ""
            if total_pages > 1:
                pagination_html = "<div class='pagination'>"
                
                # 上一页
                if page > 1:
                    pagination_html += f"<a href='{self.context_path}/static-pages/?page={page-1}' class='page-btn prev'>上一页</a>"
                else:
                    pagination_html += "<span class='page-btn prev disabled'>上一页</span>"
                
                # 页码按钮
                for i in range(1, total_pages + 1):
                    if i == page:
                        pagination_html += f"<span class='page-btn current'>{i}</span>"
                    else:
                        pagination_html += f"<a href='{self.context_path}/static-pages/?page={i}' class='page-btn'>{i}</a>"
                
                # 下一页
                if page < total_pages:
                    pagination_html += f"<a href='{self.context_path}/static-pages/?page={page+1}' class='page-btn next'>下一页</a>"
                else:
                    pagination_html += "<span class='page-btn next disabled'>下一页</span>"
                
                pagination_html += "</div>"
            
            # 获取模板路径
            template_path = Path(__file__).parent.parent.parent / "templates" / "static_pages_template.html"
            
            # 准备模板变量，确保所有变量都有值
            template_vars = {
                'context_path': self.context_path,
                'total_files': len(pages),
                'total_size': total_size_formatted,
                'pages_info': current_pages,
                'pagination_html': pagination_html
            }
            logger.debug(f"静态网页列表模板变量: {template_vars}")
            
            # 使用模板渲染
            html = my_render_template(str(template_path), template_vars)
            
            return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
            
        except Exception as e:
            logger.error(f"生成静态网页列表页面失败: {e}")
            return "<h1>错误</h1><p>无法加载静态网页列表</p>", 500
            
    def _generate_index_page(self):
        """生成索引页面 - 集成版本"""
        try:
            # 使用静态页面管理器获取存储统计信息
            stats = {
                'total_files': 0,
                'total_size': '0 B',
                'earliest_created': None,
                'latest_created': None
            }
            
            if self.static_page_manager:
                # 尝试使用静态页面管理器的统计信息方法
                try:
                    stats = self.static_page_manager.get_storage_stats()
                except AttributeError:
                    # 回退方案：如果没有get_storage_stats方法，手动计算
                    pages_info = self.static_page_manager.list_pages()
                    pages = pages_info.get('pages', [])
                    stats = {
                        'total_files': len(pages),
                        'total_size': sum(page.get('current_size', 0) for page in pages),
                        'earliest_created': None,
                        'latest_created': None
                    }
                    
                    if pages:
                        created_times = [page.get('created_at', '') for page in pages if page.get('created_at')]
                        created_times.sort()
                        if created_times:
                            stats['earliest_created'] = created_times[0]
                            stats['latest_created'] = created_times[-1]
                        
                    # 格式化文件大小
                    def format_file_size(size_bytes):
                        if size_bytes == 0:
                            return "0 B"
                        units = ['B', 'KB', 'MB', 'GB']
                        unit_index = 0
                        size = float(size_bytes)
                        
                        while size >= 1024 and unit_index < len(units) - 1:
                            size /= 1024
                            unit_index += 1
                        
                        return f"{size:.2f} {units[unit_index]}"
                    
                    stats['total_size'] = format_file_size(stats['total_size'])
            
            # 获取模板路径
            template_path = Path(__file__).parent.parent.parent / "templates" / "index_template.html"
            
            # 准备模板变量，处理默认值
            template_vars = {
                'title': '静态网页服务',
                'subtitle': '生成和管理静态HTML网页的HTTP访问服务',
                'pages_url': f'{self.context_path}/static-pages/',
                'chat_url': f'{self.context_path}/chat/',
                'total_files': stats['total_files'] if stats['total_files'] is not None else '无',
                'total_size': stats['total_size'] if stats['total_size'] is not None else '无',
                'earliest_created': stats['earliest_created'] if stats['earliest_created'] is not None else '无',
                'latest_created': stats['latest_created'] if stats['latest_created'] is not None else '无'
            }
            
            # 使用模板渲染 - 传递字典参数
            html = my_render_template(str(template_path), template_vars)
            
            return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
            
        except Exception as e:
            logger.error(f"生成索引页面失败: {e}")
            return "<h1>错误</h1><p>无法加载页面列表</p>", 500


# 全局Web服务器实例
_static_page_server = None


def get_static_page_server() -> StaticPageServer:
    """获取全局Web服务器实例"""
    global _static_page_server
    if _static_page_server is None:
        _static_page_server = StaticPageServer()
    return _static_page_server


def start_static_page_server(port: int = 3004, static_page_manager=None) -> bool:
    """
    启动Web 服务器
    
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