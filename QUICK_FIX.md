# MCP 启动失败快速修复

## 错误：获取 Manifest 失败: MCP service startup failed

### 快速修复步骤

#### 方法 1: 使用修复脚本（推荐）

```powershell
.\fix_mcp_config.ps1
```

脚本会自动：
- 检测 Python 路径
- 检查并安装依赖
- 更新配置文件
- 使用正确的 Python 路径

#### 方法 2: 手动修复

**步骤 1: 检查 Python**

```powershell
# 查找 Python
Get-Command python -ErrorAction SilentlyContinue
```

如果找不到，使用完整路径：
```
C:\Users\maluw\AppData\Local\Microsoft\WindowsApps\python.exe
```

**步骤 2: 安装依赖**

```powershell
# 使用完整路径安装
C:\Users\maluw\AppData\Local\Microsoft\WindowsApps\python.exe -m pip install -r requirements.txt
```

**步骤 3: 更新配置文件**

编辑 `C:\Users\maluw\AppData\Roaming\Claude\claude_desktop_config.json`：

使用完整 Python 路径：

```json
{
  "mcpServers": {
    "wechat-official-account": {
      "command": "C:\\Users\\maluw\\AppData\\Local\\Microsoft\\WindowsApps\\python.exe",
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

**步骤 4: 重启 Claude Desktop**

### 常见问题

#### 问题 1: Python 命令不可用

**解决**: 使用完整路径

```json
{
  "command": "C:\\Users\\maluw\\AppData\\Local\\Microsoft\\WindowsApps\\python.exe"
}
```

#### 问题 2: 依赖未安装

**解决**: 手动安装

```powershell
C:\Users\maluw\AppData\Local\Microsoft\WindowsApps\python.exe -m pip install mcp flask requests python-dotenv Pillow pycryptodome cryptography sqlalchemy
```

#### 问题 3: 模块导入失败

**解决**: 确保在项目根目录运行，所有文件都存在

### 验证

运行测试脚本：

```powershell
C:\Users\maluw\AppData\Local\Microsoft\WindowsApps\python.exe test_mcp_startup.py
```

如果所有检查通过，说明配置正确。

### 使用 Docker（备选）

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

前提：确保 Docker 容器正在运行：
```powershell
docker-compose up -d
```

