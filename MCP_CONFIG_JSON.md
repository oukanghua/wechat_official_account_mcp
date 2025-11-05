# MCP 配置 JSON 格式说明

## 基本结构

MCP 客户端（如 Claude Desktop、Cursor）使用 JSON 配置文件来定义 MCP 服务器。

### 基本格式

```json
{
  "mcpServers": {
    "服务器名称": {
      "command": "命令",
      "args": ["参数1", "参数2"],
      "env": {
        "环境变量名": "环境变量值"
      }
    }
  }
}
```

## 微信公众号 MCP 服务器配置

### 完整配置示例

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
        "WECHAT_APP_SECRET": "5393f5c008c2d2941ee9fe981d55f8f2",
        "WECHAT_TOKEN": "your_token_here",
        "WECHAT_ENCODING_AES_KEY": "your_encoding_aes_key_here"
      }
    }
  }
}
```

## 字段说明

### 1. `mcpServers` (对象)
- **类型**: 对象
- **说明**: 包含所有 MCP 服务器的配置
- **必需**: 是

### 2. 服务器名称 (对象键)
- **类型**: 字符串
- **说明**: MCP 服务器的唯一标识符
- **示例**: `"wechat-official-account"`
- **必需**: 是

### 3. `command` (字符串)
- **类型**: 字符串
- **说明**: 用于启动 MCP 服务器的命令
- **示例**: 
  - `"python"` - 使用 Python 解释器
  - `"docker"` - 使用 Docker
  - `"node"` - 使用 Node.js
- **必需**: 是

### 4. `args` (数组)
- **类型**: 字符串数组
- **说明**: 传递给命令的参数
- **示例**: 
  ```json
  ["C:\\Users\\maluw\\Code\\MCP\\wechat_official_account_mcp\\main.py"]
  ```
- **必需**: 是
- **注意**: 
  - Windows 路径使用双反斜杠 `\\` 或正斜杠 `/`
  - 路径必须是绝对路径

### 5. `env` (对象，可选)
- **类型**: 对象
- **说明**: 环境变量键值对
- **示例**:
  ```json
  {
    "WECHAT_APP_ID": "wx5d3e84e3e5720b58",
    "WECHAT_APP_SECRET": "5393f5c008c2d2941ee9fe981d55f8f2"
  }
  ```
- **必需**: 否
- **注意**: 
  - 如果已在 `.env` 文件中配置，可以省略
  - 如果在这里配置，会覆盖 `.env` 文件中的设置

## 配置位置

### Claude Desktop (Windows)

**配置文件路径**:
```
C:\Users\你的用户名\AppData\Roaming\Claude\claude_desktop_config.json
```

**环境变量方式**:
```
%APPDATA%\Claude\claude_desktop_config.json
```

### Cursor (Windows)

**配置文件路径**:
```
C:\Users\你的用户名\AppData\Roaming\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
```

## 配置示例

### 示例 1: 使用 Python (推荐)

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

### 示例 2: 使用完整 Python 路径

如果 `python` 命令不可用，使用完整路径：

```json
{
  "mcpServers": {
    "wechat-official-account": {
      "command": "C:\\Users\\maluw\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
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

### 示例 3: 使用 Docker

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
      ],
      "env": {
        "WECHAT_APP_ID": "wx5d3e84e3e5720b58",
        "WECHAT_APP_SECRET": "5393f5c008c2d2941ee9fe981d55f8f2"
      }
    }
  }
}
```

### 示例 4: 最小配置（使用 .env 文件）

如果已在 `.env` 文件中配置了环境变量：

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

### 示例 5: 多个 MCP 服务器

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
    },
    "another-server": {
      "command": "node",
      "args": [
        "path/to/another/server.js"
      ]
    }
  }
}
```

## 环境变量说明

### 必需的环境变量

- `WECHAT_APP_ID`: 微信公众号 AppID
- `WECHAT_APP_SECRET`: 微信公众号 AppSecret

### 可选的环境变量

- `WECHAT_TOKEN`: 微信公众号 Token（用于消息接收）
- `WECHAT_ENCODING_AES_KEY`: 微信公众号消息加密密钥（用于消息加密）

## 路径格式说明

### Windows 路径

**使用双反斜杠**:
```json
"C:\\Users\\maluw\\Code\\MCP\\wechat_official_account_mcp\\main.py"
```

**或使用正斜杠**:
```json
"C:/Users/maluw/Code/MCP/wechat_official_account_mcp/main.py"
```

**绝对路径**:
```json
"C:\\Users\\maluw\\Code\\MCP\\wechat_official_account_mcp\\main.py"
```

**相对路径** (不推荐):
```json
"./main.py"  // 不推荐，可能导致路径错误
```

## 验证配置

### 1. 检查 JSON 格式

使用在线 JSON 验证器或 PowerShell：

```powershell
# PowerShell
$json = Get-Content "claude_desktop_config.json" -Raw
try {
    $obj = $json | ConvertFrom-Json
    Write-Host "JSON 格式正确"
} catch {
    Write-Host "JSON 格式错误: $_"
}
```

### 2. 检查路径

确保路径存在：

```powershell
Test-Path "C:\Users\maluw\Code\MCP\wechat_official_account_mcp\main.py"
```

### 3. 检查命令

确保命令可用：

```powershell
python --version
```

## 常见问题

### 问题 1: JSON 格式错误

**错误**: `Unexpected token`, `SyntaxError`

**解决**: 
- 检查 JSON 格式是否正确
- 确保所有字符串都用双引号
- 检查是否有多余的逗号
- 使用 JSON 验证器验证

### 问题 2: 路径错误

**错误**: `No such file or directory`

**解决**:
- 使用绝对路径
- 检查路径是否正确
- Windows 路径使用 `\\` 或 `/`

### 问题 3: 命令不可用

**错误**: `command not found`

**解决**:
- 使用完整的命令路径
- 确保命令在 PATH 中
- 检查命令是否正确安装

## 快速配置

### 方法 1: 手动编辑

1. 打开配置文件
2. 添加或更新 `mcpServers` 部分
3. 保存文件
4. 重启客户端

### 方法 2: 使用项目脚本

```powershell
# 使用自动配置脚本
.\setup_mcp.ps1
```

脚本会自动：
- 读取 `.env` 文件
- 生成配置 JSON
- 更新 Claude Desktop 配置

## 完整配置模板

```json
{
  "mcpServers": {
    "wechat-official-account": {
      "command": "python",
      "args": [
        "C:/Users/maluw/Code/MCP/wechat_official_account_mcp/main.py"
      ],
      "env": {
        "WECHAT_APP_ID": "你的AppID",
        "WECHAT_APP_SECRET": "你的AppSecret",
        "WECHAT_TOKEN": "你的Token（可选）",
        "WECHAT_ENCODING_AES_KEY": "你的加密密钥（可选）"
      }
    }
  }
}
```

## 注意事项

1. **路径格式**: Windows 路径使用 `\\` 或 `/`
2. **绝对路径**: 建议使用绝对路径
3. **环境变量**: 敏感信息建议使用环境变量
4. **JSON 格式**: 确保 JSON 格式正确
5. **重启客户端**: 修改配置后需要重启客户端


