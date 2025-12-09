"""
OpenAI API 服务模块
处理与 OpenAI API 的通信和消息回复
"""
import os
import json
import logging
import asyncio
import httpx
from typing import Dict, Any, List, Optional

# 加载环境变量
from dotenv import load_dotenv
env_file = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if os.path.exists(env_file):
    load_dotenv(env_file)
    logging.info(f"已加载环境变量文件: {env_file}")
else:
    logging.warning(f"未找到环境变量文件: {env_file}")

logger = logging.getLogger(__name__)


class AIService:
    """OpenAI API 服务类"""
    
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None, 
                 model: Optional[str] = None, system_prompt: Optional[str] = None):
        """
        初始化AI服务
        
        Args:
            api_url: API基础URL，默认为环境变量 OPENAI_API_URL 或 AI_API_URL
            api_key: API密钥，默认为环境变量 OPENAI_API_KEY 或 AI_API_KEY
            model: 模型名称，默认为环境变量 OPENAI_MODEL 或 AI_MODEL
            system_prompt: 系统提示词，默认为环境变量 OPENAI_PROMPT 或 AI_PROMPT
        """
        # 优先使用OPENAI_前缀的环境变量，兼容AI_前缀的变量
        self.api_url = api_url or os.getenv('AI_API_URL') or os.getenv('OPENAI_API_URL') 
        self.api_key = api_key or os.getenv('AI_API_KEY') or os.getenv('OPENAI_API_KEY') 
        self.model = model or os.getenv('AI_MODEL') or os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo') 
        self.system_prompt = system_prompt or os.getenv('AI_PROMPT') or os.getenv('OPENAI_PROMPT', '你是一个专业的热点资讯分析师，专注于实时追踪、深度解析和前瞻预测全球范围内的热点新闻事件。') 
        
        # 默认设置
        self.max_tokens = int(os.getenv('AI_MAX_TOKENS') or os.getenv('OPENAI_MAX_TOKENS', '1000'))
        self.temperature = float(os.getenv('AI_TEMPERATURE') or os.getenv('OPENAI_TEMPERATURE', '0.7'))
        self.timeout = float(os.getenv('AI_TIMEOUT') or os.getenv('OPENAI_TIMEOUT', '30.0'))
        
        # 尝试从配置文件加载
        self._load_config_from_file()
    
    def is_configured(self) -> bool:
        """
        检查AI服务是否已正确配置
        
        Returns:
            是否已配置
        """
        return bool(self.api_url and self.api_key)
    
    async def get_reply(self, messages: List[Dict[str, str]], stream: bool = False, timeout: float = 4.5, source: str = "unknown") -> str:
        """
        获取AI回复
        
        Args:
            messages: 消息列表，包含 role 和 content
            stream: 是否使用流式调用
            timeout: 流式调用时的默认超时时间（秒）
            source: 请求来源，可选值："wechat"（公众号）、"page"（页面访问）、"unknown"（未知）
            
        Returns:
            AI回复内容
        """
        try:
            if not self.is_configured():
                return "AI服务未配置，无法提供智能回复"
            
            # 构建完整的消息列表
            full_messages = [
                {"role": "system", "content": self.system_prompt}
            ] + messages
            
            # 验证消息格式
            for msg in full_messages:
                if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                    logger.error(f"无效的消息格式: {msg}")
                    return "消息格式错误"
            
            # 调用OpenAI API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 构建请求参数
                request_params = {
                    "model": self.model,
                    "messages": full_messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature
                }
                
                if stream:
                    request_params["stream"] = True
                    
                    # 流式调用 - 使用client.stream()方法并配合async with上下文管理器
                    async with client.stream(
                        "POST",
                        f"{self.api_url.rstrip('/')}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json=request_params
                    ) as response:
                        
                        if response.status_code != 200:
                            logger.error(f"AI API调用失败: {response.status_code} - {response.text}")
                            return f"AI服务暂时不可用: {response.status_code}"
                        
                        # 处理流式响应
                        collected_content = []
                        complete = False
                        
                        async def collect_stream():
                            nonlocal collected_content, complete
                            try:
                                async for line in response.aiter_lines():
                                    if line.startswith('data: ') and line != 'data: [DONE]':
                                        # 解析JSON数据
                                        import json
                                        try:
                                            data = json.loads(line[6:])  # 去掉 'data: ' 前缀
                                            if 'choices' in data and data['choices']:
                                                delta = data['choices'][0].get('delta', {})
                                                if 'content' in delta:
                                                    collected_content.append(delta['content'])
                                        except json.JSONDecodeError:
                                            continue
                                    elif line == 'data: [DONE]':
                                        complete = True
                                        break
                            except Exception as e:
                                logger.error(f"处理流式响应时发生错误: {e}")
                        
                        # 根据来源和配置决定超时策略
                        final_timeout = timeout
                        
                        if source == "wechat":
                            # 公众号接口：使用配置的超时时间
                            wechat_timeout = os.getenv('WECHAT_AI_TIMEOUT')
                            if wechat_timeout:
                                try:
                                    final_timeout = float(wechat_timeout)
                                except ValueError:
                                    logger.warning(f"WECHAT_AI_TIMEOUT 配置值无效: {wechat_timeout}，使用默认值 {timeout}秒")
                        elif source == "page":
                            # 页面访问：不设置超时
                            final_timeout = None  # None 表示不超时
                        
                        # 使用超时机制
                        try:
                            if final_timeout is None:
                                await collect_stream()
                            else:
                                await asyncio.wait_for(collect_stream(), timeout=final_timeout)
                        except asyncio.TimeoutError:
                            logger.warning(f"流式响应超时（{final_timeout}秒），返回已接收内容")
                        
                        # 构建最终回复
                        reply_content = ''.join(collected_content)
                        
                        # 如果回复未完成且有内容，添加提示话语
                        if not complete and reply_content:
                            # 从环境变量获取提示话语
                            prompt_text = os.getenv('OPENAI_STREAM_TIMEOUT_PROMPT', '\n\n（内容未完全生成，后续回复将继续完善）')
                            reply_content += prompt_text
                        
                        return reply_content
                else:
                    # 阻塞式调用
                    response = await client.post(
                        f"{self.api_url.rstrip('/')}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json=request_params
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if 'choices' in result and len(result['choices']) > 0:
                            return result['choices'][0]['message']['content']
                        else:
                            logger.error(f"API返回格式异常: {result}")
                            return "AI服务返回格式异常"
                    else:
                        logger.error(f"AI API调用失败: {response.status_code} - {response.text}")
                        return f"AI服务暂时不可用: {response.status_code}"
                    
        except asyncio.TimeoutError:
            logger.error("AI API调用超时")
            return "AI服务响应超时，请稍后重试"
        except Exception as e:
            logger.error(f"获取AI回复时发生错误: {e}")
            return f"服务器开小差了: {str(e)}"
    
    async def simple_chat(self, user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None, stream: bool = False, timeout: float = 4.5, source: str = "unknown") -> str:
        """
        简单对话模式
        
        Args:
            user_message: 用户消息
            conversation_history: 对话历史（可选）
            stream: 是否使用流式调用
            timeout: 流式调用时的超时时间（秒）
            source: 请求来源，可选值："wechat"（公众号）、"page"（页面访问）、"unknown"（未知）
            
        Returns:
            AI回复内容
        """
        try:
            messages = conversation_history or []
            messages.append({"role": "user", "content": user_message})
            
            return await self.get_reply(messages, stream=stream, timeout=timeout, source=source)
            
        except Exception as e:
            logger.error(f"简单对话时发生错误: {e}")
            return f"对话失败: {str(e)}"
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        获取AI服务配置信息
        
        Returns:
            配置信息字典
        """
        return {
            'api_url': self.api_url,
            'api_key_configured': bool(self.api_key),
            'model': self.model,
            'system_prompt': self.system_prompt,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'timeout': self.timeout,
            'is_configured': self.is_configured()
        }
    
    def save_config(self, api_url: str, api_key: str, model: str, system_prompt: str) -> bool:
        """
        保存配置到环境变量和文件
        
        Args:
            api_url: API基础URL
            api_key: API密钥
            model: 模型名称
            system_prompt: 系统提示词
            
        Returns:
            是否保存成功
        """
        try:
            # 更新实例属性
            if api_url:
                self.api_url = api_url
            if api_key:
                self.api_key = api_key
            if model:
                self.model = model
            if system_prompt:
                self.system_prompt = system_prompt
            
            # 保存到环境变量（同时保存OPENAI_前缀和AI_前缀，保持兼容性）
            os.environ['OPENAI_API_URL'] = self.api_url
            os.environ['OPENAI_API_KEY'] = self.api_key
            os.environ['OPENAI_MODEL'] = self.model
            os.environ['OPENAI_PROMPT'] = self.system_prompt
            os.environ['OPENAI_MAX_TOKENS'] = str(self.max_tokens)
            os.environ['OPENAI_TEMPERATURE'] = str(self.temperature)
            os.environ['OPENAI_TIMEOUT'] = str(self.timeout)
            
            # 兼容旧的AI_前缀
            os.environ['AI_API_URL'] = self.api_url
            os.environ['AI_API_KEY'] = self.api_key
            os.environ['AI_MODEL'] = self.model
            os.environ['AI_PROMPT'] = self.system_prompt
            os.environ['AI_MAX_TOKENS'] = str(self.max_tokens)
            os.environ['AI_TEMPERATURE'] = str(self.temperature)
            os.environ['AI_TIMEOUT'] = str(self.timeout)
            
            # 保存到配置文件
            self._save_config_to_file()
            
            logger.info("AI配置已保存")
            return True
        except Exception as e:
            logger.error(f"保存AI配置失败: {e}")
            return False
    
    def _get_config_file_path(self) -> str:
        """
        获取配置文件路径
        
        Returns:
            配置文件路径
        """
        config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "config")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "ai_config.json")
    
    def _load_config_from_file(self):
        """
        从配置文件加载配置
        只有当配置文件中的值不为空时才覆盖环境变量中的配置
        """
        try:
            config_file = self._get_config_file_path()
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    
                # 更新配置，只有当配置文件中的值不为空时才覆盖
                if "api_url" in config and config["api_url"]:
                    self.api_url = config["api_url"]
                if "api_key" in config and config["api_key"]:
                    self.api_key = config["api_key"]
                if "model" in config and config["model"]:
                    self.model = config["model"]
                if "system_prompt" in config and config["system_prompt"]:
                    self.system_prompt = config["system_prompt"]
                if "max_tokens" in config and config["max_tokens"] is not None:
                    self.max_tokens = int(config["max_tokens"])
                if "temperature" in config and config["temperature"] is not None:
                    self.temperature = float(config["temperature"])
                if "timeout" in config and config["timeout"] is not None:
                    self.timeout = float(config["timeout"])
                    
                logger.info("从配置文件加载AI配置成功")
        except Exception as e:
            logger.error(f"从配置文件加载AI配置失败: {e}")
    
    def _save_config_to_file(self):
        """
        保存配置到文件
        """
        try:
            config_file = self._get_config_file_path()
            config = {
                "api_url": self.api_url,
                "api_key": self.api_key,
                "model": self.model,
                "system_prompt": self.system_prompt,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "timeout": self.timeout
            }
            
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
            logger.info("AI配置已保存到文件")
        except Exception as e:
            logger.error(f"保存AI配置到文件失败: {e}")


# 全局AI服务实例
_ai_service_instance = None

def get_ai_service() -> AIService:
    """
    获取全局AI服务实例（单例模式）
    
    Returns:
        AI服务实例
    """
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance


# ========== 工具函数 ==========

def handle_ai_tool(arguments: dict, ai_service: Optional[AIService] = None) -> str:
    """
    处理AI工具调用
    
    Args:
        arguments: 工具参数
        ai_service: AI服务实例（可选）
        
    Returns:
        处理结果文本
    """
    try:
        action = arguments.get('action')
        
        # 如果没有提供AI服务实例，使用全局实例
        if ai_service is None:
            ai_service = get_ai_service()
        
        if action == 'chat':
            message = arguments.get('message', '')
            if not message:
                return "错误: 请提供消息内容"
            
            # 使用asyncio运行异步处理
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                reply = loop.run_until_complete(ai_service.simple_chat(message))
                return f"用户消息: {message}\nAI回复: {reply}"
            finally:
                loop.close()
        
        elif action == 'advanced_chat':
            messages = arguments.get('messages', [])
            if not messages:
                return "错误: 请提供消息列表"
            
            # 使用asyncio运行异步处理
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                reply = loop.run_until_complete(ai_service.get_reply(messages))
                return f"AI回复: {reply}"
            finally:
                loop.close()
        
        elif action == 'config':
            config_info = ai_service.get_config_info()
            
            lines = ["AI服务配置信息:\n"]
            lines.append(f"API URL: {config_info['api_url'] or '未配置'}")
            lines.append(f"API Key: {'已配置' if config_info['api_key_configured'] else '未配置'}")
            lines.append(f"模型: {config_info['model']}")
            lines.append(f"最大Token数: {config_info['max_tokens']}")
            lines.append(f"温度参数: {config_info['temperature']}")
            lines.append(f"超时时间: {config_info['timeout']}秒")
            lines.append(f"服务状态: {'已配置' if config_info['is_configured'] else '未配置'}")
            
            return "\n".join(lines)
        
        elif action == 'test':
            test_message = arguments.get('message', '你好，请介绍一下你自己')
            
            # 使用asyncio运行异步处理
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                reply = loop.run_until_complete(ai_service.simple_chat(test_message))
                return f"测试消息: {test_message}\nAI回复: {reply}"
            finally:
                loop.close()
        
        elif action == 'update_config':
            # 更新配置
            if 'api_url' in arguments:
                ai_service.api_url = arguments['api_url']
            if 'api_key' in arguments:
                ai_service.api_key = arguments['api_key']
            if 'model' in arguments:
                ai_service.model = arguments['model']
            if 'system_prompt' in arguments:
                ai_service.system_prompt = arguments['system_prompt']
            if 'max_tokens' in arguments:
                ai_service.max_tokens = int(arguments['max_tokens'])
            if 'temperature' in arguments:
                ai_service.temperature = float(arguments['temperature'])
            
            return "AI服务配置更新成功"
        
        else:
            return f"未知操作: {action}"
    
    except Exception as e:
        error_msg = f"处理AI工具失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg