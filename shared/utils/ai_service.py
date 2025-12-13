"""
OpenAI API 服务模块
处理与 OpenAI API 的通信和消息回复
"""
import os
import json
import logging
import asyncio
import httpx
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from collections import OrderedDict

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
        
        # 只在第一次初始化时从配置文件加载，后续通过save_config更新
        if not hasattr(self.__class__, '_config_loaded'):
            self._load_config_from_file()
            self.__class__._config_loaded = True
        
        # 复用HTTP客户端，减少连接建立和销毁的开销
        if not hasattr(self.__class__, '_http_client'):
            self.__class__._http_client = None
        
        # 初始化HTTP客户端
        self._init_http_client()
        
        # 初始化微信消息缓存
        if not hasattr(self.__class__, '_wechat_cache'):
            # 使用OrderedDict实现LRU缓存
            self.__class__._wechat_cache = OrderedDict()
        
        # 缓存时间配置
        wechat_cache_time = os.getenv('WECHAT_MSG_AI_CACHE_TIME')
        self.wechat_cache_time = float(wechat_cache_time) if wechat_cache_time else 300.0  # 默认5分钟
    
    def is_configured(self) -> bool:
        """
        检查AI服务是否已正确配置
        
        Returns:
            是否已配置
        """
        return bool(self.api_url and self.api_key)
    
    def _init_http_client(self):
        """
        初始化复用的HTTP客户端
        """
        if self.__class__._http_client is None or self.__class__._http_client.is_closed:
            self.__class__._http_client = httpx.AsyncClient(timeout=self.timeout)
    
    async def _close_http_client(self):
        """
        关闭HTTP客户端
        """
        if self.__class__._http_client and not self.__class__._http_client.is_closed:
            await self.__class__._http_client.aclose()
            self.__class__._http_client = None
    
    async def get_reply(self, messages: List[Dict[str, str]], stream: bool = False, timeout: float = 4.5, source: str = "unknown", signature: str = "") -> str:
        """
        获取AI回复
        
        Args:
            messages: 消息列表，包含 role 和 content
            stream: 是否使用流式调用
            timeout: 流式调用时的默认超时时间（秒）
            source: 请求来源，可选值："wechat"（公众号）、"page"（页面访问）、"unknown"（未知）
            signature: 微信请求签名，用于缓存键生成
            
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
            
            # 微信对话缓存检查（block模式）
            if source == "wechat" and not stream:
                # 获取用户问题
                user_message = messages[-1]['content'] if messages else ''
                # 生成缓存键
                cache_key = f"{user_message}_{signature}"
                current_time = time.time()
                
                # 检查缓存是否存在且未过期
                if cache_key in self.__class__._wechat_cache:
                    cached_content, expire_time = self.__class__._wechat_cache[cache_key]
                    if expire_time > current_time:
                        logger.info(f"微信对话缓存命中: {cache_key}")
                        return cached_content
                    else:
                        logger.info(f"微信对话缓存已过期: {cache_key}")
                        # 清理过期缓存项
                        self._remove_cache_item(cache_key)
            
            # 调用OpenAI API
            # 使用复用的HTTP客户端，减少连接建立和销毁的开销
            client = self.__class__._http_client
            
            # 构建请求参数
            request_params = {
                "model": self.model,
                "messages": full_messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            # 统一超时策略
            final_timeout = timeout
            
            if source == "wechat":
                # 微信公众号：使用专用超时配置
                wechat_timeout = os.getenv('WECHAT_MSG_AI_TIMEOUT')
                if wechat_timeout:
                    try:
                        final_timeout = float(wechat_timeout)
                    except ValueError:
                        logger.warning(f"WECHAT_MSG_AI_TIMEOUT 配置值无效: {wechat_timeout}，使用默认值 {timeout}秒")
            elif source == "page":
                # 页面访问：使用OPENAI_TIMEOUT配置
                page_timeout = os.getenv('OPENAI_TIMEOUT', '300')
                try:
                    final_timeout = float(page_timeout)
                except ValueError:
                    logger.warning(f"OPENAI_TIMEOUT 配置值无效: {page_timeout}，使用默认值 300秒")
            
            if stream:
                request_params["stream"] = True
                
                # 流式调用 - 使用client.stream()方法
                try:
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
                        timed_out = False
                        
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
                        
                        # 使用超时机制
                        try:
                            # 创建任务
                            stream_task = asyncio.create_task(collect_stream())
                            if final_timeout is None:
                                await stream_task
                            else:
                                await asyncio.wait_for(stream_task, timeout=final_timeout)
                        except asyncio.TimeoutError:
                            logger.warning(f"流式响应超时（{final_timeout}秒），返回已接收内容")
                            timed_out = True
                            # 取消任务以避免资源泄漏
                            if 'stream_task' in locals():
                                stream_task.cancel()
                                try:
                                    await stream_task  # 等待任务被取消
                                except asyncio.CancelledError:
                                    pass
                        
                        # 构建最终回复并处理
                        reply_content = ''.join(collected_content)
                        processed_content = self._process_response(reply_content, source, timed_out)
                        
                        # 微信对话内容缓存（stream模式）
                        if source == "wechat" and processed_content:
                            # 获取用户问题
                            user_message = messages[-1]['content'] if messages else ''
                            # 生成缓存键（用户问题 + signature）
                            cache_key = f"{user_message}_{signature}"
                            
                            # 清理过期缓存
                            self._clean_expired_cache()
                            
                            # 存储新缓存
                            current_time = time.time()
                            expire_time = current_time + self.wechat_cache_time
                            self.__class__._wechat_cache[cache_key] = (processed_content, expire_time)
                            logger.info(f"写入缓存: {cache_key}")
                            
                            # 限制缓存大小
                            self._limit_cache_size()
                        
                        return processed_content
                except httpx.RemoteProtocolError:
                    # 处理连接错误，重新初始化客户端
                    self._init_http_client()
                    logger.warning(f"HTTP连接异常，已重新初始化客户端")
                    return f"AI服务连接异常，请稍后重试"
            else:
                # 阻塞式调用
                try:
                    response = await client.post(
                        f"{self.api_url.rstrip('/')}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json=request_params,
                        timeout=final_timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0]['message']['content']
                            processed_content = self._process_response(content, source)
                            
                            # 微信对话内容缓存
                            if source == "wechat" and processed_content:
                                # 生成缓存键（用户问题 + signature）
                                user_message = messages[-1]['content'] if messages else ''
                                cache_key = f"{user_message}_{signature}"
                                
                                # 清理过期缓存
                                self._clean_expired_cache()
                                
                                # 存储新缓存
                                current_time = time.time()
                                expire_time = current_time + self.wechat_cache_time
                                self.__class__._wechat_cache[cache_key] = (processed_content, expire_time)
                                logger.info(f"写入缓存: {cache_key}")
                                
                                # 限制缓存大小
                                self._limit_cache_size()
                            
                            return processed_content
                        else:
                            logger.error(f"API返回格式异常: {result}")
                            return "AI服务返回格式异常"
                    else:
                        logger.error(f"AI API调用失败: {response.status_code} - {response.text}")
                        return f"AI服务暂时不可用: {response.status_code}"
                except httpx.RemoteProtocolError:
                    # 处理连接错误，重新初始化客户端
                    self._init_http_client()
                    logger.warning(f"HTTP连接异常，已重新初始化客户端")
                    return f"AI服务连接异常，请稍后重试"
                    
        except asyncio.TimeoutError:
            logger.error("AI API调用超时")
            return self._process_response("", source, timed_out=True)
        except Exception as e:
            logger.error(f"获取AI回复时发生错误: {e}")
            return f"服务器开小差了: {str(e)}"
    
    async def simple_chat(self, user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None, stream: bool = False, timeout: float = 4.5, source: str = "unknown", signature: str = "") -> str:
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
            
            return await self.get_reply(messages, stream=stream, timeout=timeout, source=source, signature=signature)
            
        except Exception as e:
            logger.error(f"简单对话时发生错误: {e}")
            return f"对话失败: {str(e)}"
    
    async def stream_chat(self, user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None, source: str = "unknown", signature: str = "") -> AsyncGenerator[str, None]:
        """
        流式对话模式
        
        Args:
            user_message: 用户消息
            conversation_history: 对话历史（可选）
            source: 请求来源，可选值："wechat"（公众号）、"page"（页面访问）、"unknown"（未知）
            signature: 微信请求签名，用于缓存键生成
            
        Yields:
            AI回复的内容片段
        """
        try:
            if not self.is_configured():
                yield "AI服务未配置，无法提供智能回复"
                return
            
            # 微信对话缓存检查（stream模式）
            if source == "wechat":
                # 生成缓存键
                cache_key = f"{user_message}_{signature}"
                current_time = time.time()
                
                # 检查缓存是否存在且未过期
                if cache_key in self.__class__._wechat_cache:
                    cached_content, expire_time = self.__class__._wechat_cache[cache_key]
                    if expire_time > current_time:
                        logger.info(f"微信对话缓存命中: {cache_key}")
                        # 模拟流式响应，分块yield缓存内容
                        # 每次yield 100个字符
                        chunk_size = 100
                        for i in range(0, len(cached_content), chunk_size):
                            chunk = cached_content[i:i+chunk_size]
                            yield chunk
                            # 模拟网络延迟
                            await asyncio.sleep(0.1)
                        return
                    else:
                        logger.info(f"微信对话缓存已过期: {cache_key}")
                        # 清理过期缓存项
                        self._remove_cache_item(cache_key)
            
            # 构建完整的消息列表
            messages = conversation_history or []
            messages.append({"role": "user", "content": user_message})
            
            full_messages = [
                {"role": "system", "content": self.system_prompt}
            ] + messages
            
            # 验证消息格式
            for msg in full_messages:
                if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                    logger.error(f"无效的消息格式: {msg}")
                    yield "消息格式错误"
                    return
            
            # 调用OpenAI API - 使用复用的HTTP客户端
            client = self.__class__._http_client
            
            # 构建请求参数
            request_params = {
                "model": self.model,
                "messages": full_messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": True
            }
            
            # 根据来源和配置决定超时策略
            final_timeout = None
            if source == "wechat":
                # 公众号接口：使用配置的超时时间
                wechat_timeout = os.getenv('WECHAT_MSG_AI_TIMEOUT')
                if wechat_timeout:
                    try:
                        final_timeout = float(wechat_timeout)
                    except ValueError:
                        logger.warning(f"WECHAT_MSG_AI_TIMEOUT 配置值无效: {wechat_timeout}")
            elif source == "page":
                # 页面访问：使用OPENAI_TIMEOUT配置
                page_timeout = os.getenv('OPENAI_TIMEOUT', '300')
                try:
                    final_timeout = float(page_timeout)
                except ValueError:
                    logger.warning(f"OPENAI_TIMEOUT 配置值无效: {page_timeout}，使用默认值 300秒")
            
            # 流式调用
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
                    yield f"AI服务暂时不可用: {response.status_code}"
                    return
                
                # 处理流式响应
                collected_content = []
                total_length = 0
                reached_limit = False
                
                # 获取微信长度限制
                wechat_len_limit = None
                if source == "wechat":
                    wechat_len_limit = os.getenv('WECHAT_MSG_AI_LEN_LIMIT')
                    if wechat_len_limit:
                        try:
                            wechat_len_limit = int(wechat_len_limit)
                        except ValueError:
                            logger.warning(f"WECHAT_MSG_AI_LEN_LIMIT 配置值无效: {wechat_len_limit}")
                            wechat_len_limit = None
                
                # 定义流式响应处理函数
                async def process_stream():
                    nonlocal collected_content, total_length, reached_limit
                    async for line in response.aiter_lines():
                        if reached_limit:
                            break
                            
                        if line.startswith('data: ') and line != 'data: [DONE]':
                            # 解析JSON数据
                            try:
                                data = json.loads(line[6:])  # 去掉 'data: ' 前缀
                                if 'choices' in data and data['choices']:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content_part = delta['content']
                                        
                                        # 微信长度限制处理（与_process_response保持一致）
                                        if source == "wechat" and wechat_len_limit:
                                            remaining = wechat_len_limit - total_length
                                            if remaining <= 0:
                                                # 已达到限制，不再yield内容
                                                reached_limit = True
                                                continue
                                                
                                            if len(content_part) > remaining:
                                                # 超过剩余限制，截取部分内容并添加省略号
                                                content_part = content_part[:remaining] + "..."
                                                yield content_part
                                                logger.info(f"微信消息超过长度限制({wechat_len_limit}字符)，已截取")
                                                reached_limit = True
                                                continue
                                        
                                        # 正常yield内容
                                        yield content_part
                                        collected_content.append(content_part)
                                        total_length += len(content_part)
                            except json.JSONDecodeError:
                                continue
                        elif line == 'data: [DONE]':
                            break
                
                # 使用超时机制处理流式响应
                timed_out = False
                try:
                    if final_timeout is None:
                        async for content in process_stream():
                            yield content
                    else:
                        # 创建一个协程包装整个流式处理，统一处理超时
                        async def wrapped_stream():
                            async for content in process_stream():
                                yield content
                        
                        # 使用wait_for包装整个流式处理过程
                        stream_coroutine = wrapped_stream()
                        try:
                            async for content in stream_coroutine:
                                yield content
                        except asyncio.TimeoutError:
                            # 超时处理
                            logger.warning(f"流式响应超时（{final_timeout}秒），返回已接收内容")
                            timed_out = True
                except Exception as e:
                    logger.error(f"处理流式响应时发生错误: {e}")
                    # 即使发生异常，也继续执行缓存保存逻辑
                    
                # 统一处理最终响应
                if source == "wechat":
                    complete_content = ''.join(collected_content)
                    # 使用_process_response方法统一处理
                    processed_content = self._process_response(complete_content, source, timed_out)
                    
                    # 如果处理后的内容与原始内容不同，说明有截断或添加了提示
                    if processed_content != complete_content:
                        # 计算差异部分并yield
                        diff = processed_content[len(complete_content):]
                        if diff:
                            yield diff
                    
                    # 微信对话内容缓存
                    if processed_content:
                        # 生成缓存键（用户问题 + signature）
                        cache_key = f"{user_message}_{signature}"
                        
                        # 清理过期缓存
                        self._clean_expired_cache()
                        
                        # 存储新缓存
                        current_time = time.time()
                        expire_time = current_time + self.wechat_cache_time
                        self.__class__._wechat_cache[cache_key] = (processed_content, expire_time)
                        logger.info(f"写入缓存: {cache_key}")
                        
                        # 限制缓存大小
                        self._limit_cache_size()
        except httpx.RemoteProtocolError:
            # 处理连接错误，重新初始化客户端
            self._init_http_client()
            logger.warning(f"HTTP连接异常，已重新初始化客户端")
            yield f"AI服务连接异常，请稍后重试"
        except asyncio.TimeoutError:
            logger.error("AI API调用超时")
            # 超时提示处理
            if source == "wechat":
                timeout_prompt = os.getenv('WECHAT_MSG_AI_TIMEOUT_PROMPT', '\n（内容未完全生成，后续回复将继续完善）')
                yield timeout_prompt
            else:
                yield "AI服务响应超时，请稍后重试"
        except Exception as e:
            logger.error(f"流式对话时发生错误: {e}")
            yield f"对话失败: {str(e)}"
    
    def _load_config_from_file(self):
        """
        从配置文件加载配置
        """
        config_file = os.path.join(os.path.dirname(__file__), "..", "..", "config", "ai_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    
                # 更新配置
                if "api_url" in config and not self.api_url:
                    self.api_url = config["api_url"]
                if "api_key" in config and not self.api_key:
                    self.api_key = config["api_key"]
                if "model" in config and not self.model:
                    self.model = config["model"]
                if "system_prompt" in config and not self.system_prompt:
                    self.system_prompt = config["system_prompt"]
                if "max_tokens" in config:
                    self.max_tokens = config["max_tokens"]
                if "temperature" in config:
                    self.temperature = config["temperature"]
                if "timeout" in config:
                    self.timeout = config["timeout"]
                    
                logger.info(f"已从配置文件加载AI服务配置: {config_file}")
            except Exception as e:
                logger.error(f"从配置文件加载配置失败: {e}")
    
    def save_config(self, api_url: str, api_key: str, model: str, system_prompt: str, max_tokens: int = 1000, temperature: float = 0.7, timeout: float = 30.0) -> bool:
        """
        保存AI服务配置
        
        Args:
            api_url: API基础URL
            api_key: API密钥
            model: 模型名称
            system_prompt: 系统提示词
            max_tokens: 最大Token数
            temperature: 温度参数
            timeout: 超时时间（秒）
            
        Returns:
            是否保存成功
        """
        try:
            # 更新内存中的配置
            self.api_url = api_url
            self.api_key = api_key
            self.model = model
            self.system_prompt = system_prompt
            self.max_tokens = max_tokens
            self.temperature = temperature
            self.timeout = timeout
            
            # 保存到配置文件
            config_file = os.path.join(os.path.dirname(__file__), "..", "..", "config", "ai_config.json")
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            config_data = {
                "api_url": api_url,
                "model": model,
                "system_prompt": system_prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "timeout": timeout
            }
            
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"AI服务配置已保存到: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存AI服务配置失败: {e}")
            return False
    
    def _remove_cache_item(self, cache_key: str) -> None:
        """
        移除指定的缓存项
        
        Args:
            cache_key: 要移除的缓存键
        """
        if cache_key in self.__class__._wechat_cache:
            del self.__class__._wechat_cache[cache_key]
            logger.info(f"移除缓存项: {cache_key}")
    
    def _clean_expired_cache(self) -> None:
        """
        清理所有过期的缓存项
        """
        current_time = time.time()
        expired_keys = []
        
        # 找出所有过期的缓存键
        for key, (_, expire_time) in self.__class__._wechat_cache.items():
            if expire_time < current_time:
                expired_keys.append(key)
        
        # 移除过期缓存
        if expired_keys:
            logger.info(f"清理{len(expired_keys)}个过期缓存项")
            for key in expired_keys:
                del self.__class__._wechat_cache[key]
    
    def _limit_cache_size(self) -> None:
        """
        限制缓存大小，超过限制时移除最早的缓存项
        """
        max_cache_size = int(os.getenv('WECHAT_MSG_AI_CACHE_SIZE', '100'))
        if len(self.__class__._wechat_cache) > max_cache_size:
            remove_count = len(self.__class__._wechat_cache) - max_cache_size
            logger.info(f"缓存大小超过限制，移除{remove_count}个最早的缓存项")
            
            # 移除最早的缓存项
            for _ in range(remove_count):
                self.__class__._wechat_cache.popitem(last=False)
    
    def _process_response(self, content: str, source: str, timed_out: bool = False) -> str:
        """
        处理AI响应，根据来源应用不同的处理逻辑
        
        Args:
            content: AI原始响应内容
            source: 请求来源，可选值："wechat"（公众号）、"page"（页面访问）、"unknown"（未知）
            timed_out: 是否超时
            
        Returns:
            处理后的响应内容
        """
        # 如果不是微信来源，直接返回原始内容
        if source != "wechat":
            return content
            
        processed_content = content
        
        # 1. 长度限制处理
        wechat_len_limit = os.getenv('WECHAT_MSG_AI_LEN_LIMIT')
        if wechat_len_limit:
            try:
                limit = int(wechat_len_limit)
                if len(processed_content) > limit:
                    processed_content = processed_content[:limit] + "..."
                    logger.info(f"微信消息超过长度限制({limit}字符)，已截取")
            except ValueError:
                logger.warning(f"WECHAT_MSG_AI_LEN_LIMIT 配置值无效: {wechat_len_limit}")
        
        # 2. 超时提示处理
        if timed_out or processed_content == '':
            timeout_prompt = os.getenv('WECHAT_MSG_AI_TIMEOUT_PROMPT', '\n（内容未完全生成，后续回复将继续完善）')
            processed_content += timeout_prompt
            logger.info(f"微信消息处理超时，已添加超时提示")
        
        return processed_content
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        获取当前配置信息
        
        Returns:
            配置信息字典
        """
        return {
            "api_url": self.api_url,
            "api_key_configured": bool(self.api_key),
            "model": self.model,
            "system_prompt": self.system_prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout,
            "is_configured": self.is_configured()
        }


# 全局AI服务实例
_ai_service_instance = None


def get_ai_service(api_url: Optional[str] = None, api_key: Optional[str] = None, 
                   model: Optional[str] = None, system_prompt: Optional[str] = None) -> AIService:
    """
    获取全局AI服务实例
    
    Args:
        api_url: API基础URL
        api_key: API密钥
        model: 模型名称
        system_prompt: 系统提示词
        
    Returns:
        AI服务实例
    """
    global _ai_service_instance
    
    if _ai_service_instance is None:
        _ai_service_instance = AIService(api_url=api_url, api_key=api_key, model=model, system_prompt=system_prompt)
    
    return _ai_service_instance
