# MCP Connection Closed 错误修复

## 问题

MCP 客户端连接后立即关闭，错误信息：
```
MCPClient#onClose
MCPClient#startFailed MCP error -32000: Connection closed
```

## 可能原因

1. **服务器启动时出错**：初始化过程中发生异常，但错误没有正确输出
2. **导入失败**：模块导入失败但没有正确报告
3. **工作目录问题**：在不同的工作目录下运行导致路径问题
4. **初始化超时**：服务器没有及时发送初始化响应

## 已应用的修复

### 1. 延迟导入模块
- 将项目模块的导入移到 `main()` 函数中
- 确保在切换到正确的目录后再导入

### 2. 添加路径管理
```python
# 添加项目目录到 Python 路径
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
```

### 3. 改进错误处理
- 添加 `sys.stderr.flush()` 确保错误立即输出
- 改进异常处理，确保所有错误都被记录

### 4. 动态导入工具
- 在 `list_tools()` 和 `call_tool()` 中使用动态导入
- 确保在正确的环境下导入模块

## 验证步骤

### 1. 测试服务器启动

```powershell
# 从不同目录测试
cd C:\Users\maluw
python C:\Users\maluw\Code\MCP\wechat_official_account_mcp\main.py
```

应该看到：
```
微信公众号 MCP 服务器启动中...
工作目录: C:\Users\maluw\Code\MCP\wechat_official_account_mcp
Python 版本: ...
MCP 服务器已启动，等待客户端连接...
```

### 2. 检查错误输出

如果服务器立即退出，查看 stderr 输出：

```powershell
python main.py 2>&1 | Select-Object -First 50
```

### 3. 测试模块导入

```powershell
python -c "import sys; sys.path.insert(0, 'C:\\Users\\maluw\\Code\\MCP\\wechat_official_account_mcp'); from tools.auth import register_auth_tools; print('OK')"
```

## 如果仍然失败

### 检查 1: 查看详细日志

在 Claude Desktop 的日志中查找：
- 是否有 Python 错误输出
- 是否有导入错误
- 是否有其他异常

### 检查 2: 手动测试

```powershell
# 进入项目目录
cd C:\Users\maluw\Code\MCP\wechat_official_account_mcp

# 运行服务器
python main.py
```

如果看到 "MCP 服务器已启动，等待客户端连接..." 且没有错误，说明服务器正常。

### 检查 3: 检查 Python 路径

确保配置文件中的路径正确：

```json
{
  "command": "python",
  "args": [
    "C:\\Users\\maluw\\Code\\MCP\\wechat_official_account_mcp\\main.py"
  ]
}
```

### 检查 4: 使用完整 Python 路径

如果 `python` 命令不可用：

```json
{
  "command": "C:\\Users\\maluw\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
  "args": [
    "C:\\Users\\maluw\\Code\\MCP\\wechat_official_account_mcp\\main.py"
  ]
}
```

## 常见问题

### 问题 1: 服务器立即退出

**原因**: 导入失败或初始化错误

**解决**: 
1. 检查 stderr 输出
2. 确保所有依赖已安装：`pip install -r requirements.txt`
3. 确保项目目录结构完整

### 问题 2: Connection closed 立即发生

**原因**: 服务器没有发送有效的初始化响应

**解决**:
1. 确保服务器代码没有语法错误
2. 确保 `stdio_server()` 正确使用
3. 检查 MCP SDK 版本是否兼容

### 问题 3: 模块导入失败

**原因**: Python 路径或工作目录问题

**解决**:
1. 代码已添加路径管理
2. 确保在项目根目录运行
3. 检查所有模块文件是否存在

## 调试技巧

### 启用详细日志

在 `main.py` 中，日志级别已经是 INFO，应该能看到详细信息。

### 添加更多日志

如果需要，可以在关键位置添加更多日志：

```python
logger.debug(f"当前工作目录: {os.getcwd()}")
logger.debug(f"Python 路径: {sys.path}")
logger.debug(f"环境变量: {os.environ.get('WECHAT_APP_ID', 'NOT SET')}")
```

### 测试 MCP 协议

可以创建一个简单的测试客户端来验证服务器响应。

## 下一步

如果问题仍然存在，请提供：
1. 完整的错误日志（从 stderr）
2. 服务器启动时的完整输出
3. Claude Desktop 的完整日志


