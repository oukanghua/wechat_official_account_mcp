# MCP 启动失败修复指南

## 问题：获取 Manifest 失败: MCP service startup failed

## 已修复的问题

### 1. ✅ 修复了 `sys` 变量作用域问题
- **问题**: `main.py` 中在函数内部重新导入 `sys` 导致 `UnboundLocalError`
- **修复**: 移除了函数内部的 `import sys`（已在文件顶部导入）

### 2. ✅ 改进了 `stdio_server` 的使用方式
- **问题**: `stdio_server` 的返回值处理不正确
- **修复**: 添加了正确的流处理逻辑，支持元组和对象两种格式

## 验证步骤

### 步骤 1: 测试 MCP 服务器

运行测试脚本：

```powershell
python test_mcp_connection.py
```

应该看到：
```
✅ MCP SDK 导入成功
✅ 项目模块导入成功
✅ MCP 服务器创建成功
✅ 工具注册成功
```

### 步骤 2: 检查配置文件

确保 Claude Desktop 配置文件正确：

**配置文件位置**:
```
C:\Users\maluw\AppData\Roaming\Claude\claude_desktop_config.json
```

**配置内容**:
```json
{
  "mcpServers": {
    "wechat-official-account": {
      "command": "python",
      "args": [
        "C:\\Users\\maluw\\Code\\MCP\\wechat_official_account_mcp\\main.py"
      ],
      "env": {
        "WECHAT_APP_ID": "wx5d3e84e3e5720b58",
        "WECHAT_APP_SECRET": "5393f5c008c2d2941ee9fe981d55f8f2"
      }
    }
  }
}
```

**重要提示**:
- 使用 `python` 命令（已添加到 PATH）
- 使用**绝对路径**指向 `main.py`
- 确保路径使用双反斜杠 `\\` 或正斜杠 `/`

### 步骤 3: 重启 Claude Desktop

修改配置后必须**完全重启** Claude Desktop。

### 步骤 4: 验证工具可用

重启后，在 Claude Desktop 中：
1. 打开对话
2. 询问："有哪些可用的工具？"
3. 应该能看到 `wechat_auth`、`wechat_draft` 等工具

## 如果仍然失败

### 检查 1: Python 路径

```powershell
# 检查 python 命令
python --version

# 如果不可用，使用完整路径
C:\Users\maluw\AppData\Local\Programs\Python\Python312\python.exe --version
```

如果 `python` 不可用，在配置中使用完整路径：

```json
{
  "command": "C:\\Users\\maluw\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
}
```

### 检查 2: 依赖安装

```powershell
# 检查 MCP 是否安装
python -c "import mcp; print('MCP installed')"

# 如果未安装，安装依赖
pip install -r requirements.txt
```

### 检查 3: 项目路径

确保 `main.py` 文件存在：

```powershell
Test-Path "C:\Users\maluw\Code\MCP\wechat_official_account_mcp\main.py"
```

### 检查 4: 手动测试启动

```powershell
# 进入项目目录
cd C:\Users\maluw\Code\MCP\wechat_official_account_mcp

# 运行服务器（应该会等待 stdin 输入）
python main.py
```

如果看到 "微信公众号 MCP 服务器启动中..." 且没有错误，说明服务器正常。

### 检查 5: 查看详细日志

如果 Claude Desktop 有日志功能，查看详细错误信息。

## 常见错误

### 错误 1: "python: command not found"

**解决**: 使用完整 Python 路径

### 错误 2: "ModuleNotFoundError"

**解决**: 安装依赖
```powershell
pip install -r requirements.txt
```

### 错误 3: "No such file or directory"

**解决**: 检查配置文件中的路径是否正确，使用绝对路径

### 错误 4: "MCP service startup failed"

**可能原因**:
- Python 路径错误
- 依赖未安装
- 配置文件语法错误
- 项目路径错误

**解决**: 按照上述步骤逐一检查

## 成功标志

如果配置正确，应该能看到：
1. Claude Desktop 不再报错
2. 在对话中可以调用 MCP 工具
3. 工具列表包含 `wechat_*` 相关工具

## 下一步

配置成功后，可以：
1. 使用 `wechat_auth` 配置微信公众号信息
2. 使用 `wechat_draft` 创建草稿
3. 使用 `wechat_publish` 发布文章


