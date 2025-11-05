# MCP 服务故障排除

## 错误：获取 Manifest 失败: MCP service startup failed

### 可能原因

1. **Python 依赖未安装**
2. **项目模块导入失败**
3. **Python 路径问题**
4. **环境变量问题**

### 解决步骤

#### 步骤 1: 检查 Python 环境

```powershell
# 检查 Python 是否可用
python --version

# 如果 python 不可用，尝试
py --version

# 或使用完整路径
C:\Users\maluw\AppData\Local\Microsoft\WindowsApps\python.exe --version
```

#### 步骤 2: 安装依赖

```powershell
# 确保在项目根目录
cd C:\Users\maluw\Code\MCP\wechat_official_account_mcp

# 安装依赖
pip install -r requirements.txt

# 或者使用完整路径
C:\Users\maluw\AppData\Local\Microsoft\WindowsApps\python.exe -m pip install -r requirements.txt
```

#### 步骤 3: 测试 MCP 服务器

```powershell
# 运行诊断脚本
python test_mcp_startup.py

# 或直接测试
python main.py
```

如果看到错误，请记录错误信息。

#### 步骤 4: 检查配置文件

确保 Claude Desktop 配置文件中的路径正确：

```json
{
  "mcpServers": {
    "wechat-official-account": {
      "command": "python",
      "args": [
        "C:\\Users\\maluw\\Code\\MCP\\wechat_official_account_mcp\\main.py"
      ]
    }
  }
}
```

**注意**：
- 路径使用双反斜杠 `\\`
- 确保路径存在且 `main.py` 文件存在

#### 步骤 5: 使用完整 Python 路径（如果 python 命令不可用）

如果 `python` 命令不可用，可以在配置中使用完整路径：

```json
{
  "mcpServers": {
    "wechat-official-account": {
      "command": "C:\\Users\\maluw\\AppData\\Local\\Microsoft\\WindowsApps\\python.exe",
      "args": [
        "C:\\Users\\maluw\\Code\\MCP\\wechat_official_account_mcp\\main.py"
      ]
    }
  }
}
```

#### 步骤 6: 检查日志

MCP 服务器的错误日志会输出到 stderr。如果 Claude Desktop 有日志功能，可以查看详细错误信息。

### 常见错误和解决方案

#### 错误 1: ModuleNotFoundError

**原因**: 依赖未安装

**解决**:
```powershell
pip install -r requirements.txt
```

#### 错误 2: 无法导入项目模块

**原因**: 路径问题或模块缺失

**解决**:
1. 确保在项目根目录运行
2. 检查所有模块文件是否存在
3. 确保 `__init__.py` 文件存在（如果需要）

#### 错误 3: MCP SDK 导入失败

**原因**: MCP 包未安装或版本不兼容

**解决**:
```powershell
pip install --upgrade mcp
```

#### 错误 4: 环境变量未加载

**原因**: `.env` 文件不存在或格式错误

**解决**:
1. 检查 `.env` 文件是否存在
2. 确保格式正确（`KEY=value`，每行一个）
3. 或在 MCP 配置的 `env` 中直接设置

### 验证配置

运行以下命令验证配置：

```powershell
# 1. 检查 Python
python --version

# 2. 检查依赖
pip list | Select-String "mcp"

# 3. 测试导入
python -c "import sys; sys.path.insert(0, '.'); from storage.auth_manager import AuthManager; print('OK')"

# 4. 测试 MCP SDK
python -c "from mcp.server import Server; print('MCP OK')"
```

### 使用 Docker 运行（备选方案）

如果本地 Python 环境有问题，可以使用 Docker：

```json
{
  "mcpServers": {
    "wechat-official-account": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "wechat_message_server",
        "python",
        "/app/main.py"
      ]
    }
  }
}
```

前提：Docker 容器正在运行。

### 获取详细错误信息

在配置中添加环境变量以获取详细日志：

```json
{
  "mcpServers": {
    "wechat-official-account": {
      "command": "python",
      "args": [
        "C:\\Users\\maluw\\Code\\MCP\\wechat_official_account_mcp\\main.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

