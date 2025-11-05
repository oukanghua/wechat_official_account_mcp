# MCP 配置指南

本文档说明如何配置 MCP 客户端以使用微信公众号 MCP 服务器。

## Claude Desktop 配置

### Windows 配置位置

配置文件路径：`%APPDATA%\Claude\claude_desktop_config.json`

或者直接访问：`C:\Users\你的用户名\AppData\Roaming\Claude\claude_desktop_config.json`

### 配置示例

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
        "WECHAT_APP_SECRET": "your_app_secret_here",
        "WECHAT_TOKEN": "your_token_here",
        "WECHAT_ENCODING_AES_KEY": "your_encoding_aes_key_here"
      }
    }
  }
}
```

### 配置说明

1. **command**: 使用 `python` 命令运行 MCP 服务器
2. **args**: MCP 服务器主文件的完整路径
   - Windows: 使用双反斜杠 `\\` 或正斜杠 `/`
   - 示例: `"C:\\Users\\maluw\\Code\\MCP\\wechat_official_account_mcp\\main.py"`
3. **env**: 环境变量（可选）
   - 如果已在 `.env` 文件中配置，可以省略 `env` 部分
   - 如果在这里配置，会覆盖 `.env` 文件中的设置

### 使用 Docker 运行（可选）

如果使用 Docker 运行，配置如下：

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

## Cursor 配置

### 配置文件位置

配置文件路径：`%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`

### 配置示例

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

## 验证配置

### 1. 检查 Python 环境

确保 Python 已安装并可用：

```powershell
python --version
```

### 2. 检查依赖

确保已安装所有依赖：

```powershell
cd C:\Users\maluw\Code\MCP\wechat_official_account_mcp
pip install -r requirements.txt
```

### 3. 测试 MCP 服务器

手动测试 MCP 服务器是否能正常启动：

```powershell
python main.py
```

如果看到 "微信公众号 MCP 服务器启动中..." 的日志，说明服务器运行正常。

### 4. 在 Claude Desktop/Cursor 中验证

1. 重启 Claude Desktop 或 Cursor
2. 在对话中询问可用工具
3. 应该能看到 `wechat_auth`、`wechat_draft`、`wechat_publish` 等工具

## 可用工具列表

配置成功后，可以使用以下 MCP 工具：

- **wechat_auth** - 配置微信公众号信息
- **wechat_media_upload** - 上传临时素材
- **wechat_upload_img** - 上传图文消息图片
- **wechat_permanent_media** - 管理永久素材
- **wechat_draft** - 创建和管理草稿
- **wechat_publish** - 发布草稿到公众号

## 故障排除

### 问题 1: MCP 服务器无法启动

**检查**:
- Python 路径是否正确
- 项目路径是否正确
- 依赖是否已安装

**解决**:
```powershell
# 检查 Python
python --version

# 检查依赖
pip list | Select-String "mcp"

# 测试运行
python main.py
```

### 问题 2: 工具不可用

**检查**:
- 配置文件格式是否正确（JSON 格式）
- 路径是否正确
- 环境变量是否正确

**解决**:
- 验证 JSON 格式（可以使用在线 JSON 验证器）
- 检查路径是否存在
- 重启 Claude Desktop/Cursor

### 问题 3: 环境变量未生效

**说明**:
- MCP 配置中的 `env` 会覆盖 `.env` 文件
- 如果使用 `.env` 文件，可以省略配置中的 `env` 部分

## 快速开始示例

### 示例 1: 使用环境变量文件（推荐）

1. 在项目根目录创建 `.env` 文件：
```env
WECHAT_APP_ID=wx5d3e84e3e5720b58
WECHAT_APP_SECRET=your_app_secret_here
WECHAT_TOKEN=your_token_here
WECHAT_ENCODING_AES_KEY=your_encoding_aes_key_here
```

2. MCP 配置中不包含 `env`：
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

### 示例 2: 在配置中直接设置环境变量

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
        "WECHAT_APP_SECRET": "your_app_secret_here"
      }
    }
  }
}
```

## 注意事项

1. **路径格式**: Windows 路径使用双反斜杠 `\\` 或正斜杠 `/`
2. **环境变量**: 如果使用 `.env` 文件，MCP 配置中的 `env` 是可选的
3. **重启**: 修改配置后需要重启 Claude Desktop 或 Cursor
4. **权限**: 确保 Python 有权限访问项目目录

