# 修复总结：异步生成器不可迭代问题

## 问题描述
在运行项目时出现以下错误：
```
TypeError: 'async_generator' object is not iterable
```

这个错误发生在`_handle_chat_api`方法中，当使用流式响应模式时，Flask试图直接使用异步生成器作为响应内容，但Flask默认不支持异步生成器作为响应内容。

## 修复方案

### 修改文件
- `shared/utils/web_server.py`：更新了`_handle_chat_api`方法中的流式响应处理逻辑

### 修复内容
将异步生成器转换为同步可迭代对象，通过以下步骤实现：

1. 创建一个新的事件循环
2. 定义异步函数来处理流式响应
3. 创建异步生成器
4. 使用事件循环手动迭代异步生成器
5. 确保事件循环总是被正确关闭

### 核心代码更改
```python
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
```

## 修复效果
- 解决了`TypeError: 'async_generator' object is not iterable`错误
- 保持了流式响应的功能
- 提高了代码的健壮性和错误处理能力

## 使用说明
修复后，项目应该能够正常启动并支持流式响应模式。您可以通过设置`OPENAI_INTERACTION_MODE`环境变量来选择响应模式：

- `OPENAI_INTERACTION_MODE=stream`：使用流式响应模式
- `OPENAI_INTERACTION_MODE=block`：使用阻塞响应模式

默认值为`block`。