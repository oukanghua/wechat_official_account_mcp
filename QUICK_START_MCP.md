# MCP 快速配置指南

## 快速开始

### 方法 1: 使用自动安装脚本（推荐）

```powershell
# 在项目根目录运行
.\setup_mcp.ps1
```

脚本会自动：
- 读取 `.env` 文件中的环境变量
- 合并到现有的 Claude Desktop 配置
- 备份现有配置
- 创建新的配置文件

### 方法 2: 手动配置

#### 步骤 1: 找到配置文件

Claude Desktop 配置文件位置：
```
%APPDATA%\Claude\claude_desktop_config.json
```

完整路径示例：
```
C:\Users\maluw\AppData\Roaming\Claude\claude_desktop_config.json
```

#### 步骤 2: 编辑配置文件

1. 打开配置文件（如果不存在则创建）
2. 添加或更新以下内容：

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

**重要提示**：
- 将路径 `C:\\Users\\maluw\\Code\\MCP\\wechat_official_account_mcp\\main.py` 替换为你的实际项目路径
- 如果已有 `.env` 文件，可以省略 `env` 部分
- 如果配置文件已有其他 MCP 服务器，只需添加 `wechat-official-account` 部分

#### 步骤 3: 合并到现有配置

如果配置文件已存在其他 MCP 服务器，只需添加 `wechat-official-account`：

```json
{
  "mcpServers": {
    "existing-server": {
      // ... 现有配置 ...
    },
    "wechat-official-account": {
      "command": "python",
      "args": [
        "C:\\Users\\maluw\\Code\\MCP\\wechat_official_account_mcp\\main.py"
      ]
    }
  }
}
```

### 方法 3: 使用项目中的配置文件

项目已包含配置文件模板：

1. **复制配置文件**：
   ```powershell
   # 查看配置文件内容
   Get-Content claude_desktop_config.json
   ```

2. **手动合并到 Claude Desktop 配置**：
   - 打开 Claude Desktop 配置文件
   - 复制 `claude_desktop_config.json` 中的内容
   - 合并到现有配置中

## 验证配置

### 1. 检查配置文件格式

```powershell
# 验证 JSON 格式
Get-Content "$env:APPDATA\Claude\claude_desktop_config.json" | ConvertFrom-Json | Out-Null
if ($?) {
    Write-Host "✅ JSON 格式正确" -ForegroundColor Green
} else {
    Write-Host "❌ JSON 格式错误" -ForegroundColor Red
}
```

### 2. 测试 MCP 服务器

```powershell
# 测试服务器是否能正常启动
python main.py
```

应该看到 "微信公众号 MCP 服务器启动中..." 的日志。

### 3. 重启 Claude Desktop

修改配置后必须重启 Claude Desktop 才能生效。

## 配置示例

### 完整配置（包含环境变量）

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

### 简化配置（使用 .env 文件）

如果已配置 `.env` 文件，可以省略 `env` 部分：

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

## 常见问题

### Q: 如何找到项目路径？

```powershell
# 在项目根目录运行
(Get-Location).Path
```

### Q: 路径格式问题？

Windows 路径需要转义反斜杠：
- 正确：`"C:\\Users\\maluw\\Code\\MCP\\wechat_official_account_mcp\\main.py"`
- 错误：`"C:\Users\maluw\Code\MCP\wechat_official_account_mcp\main.py"`

或者使用正斜杠：
- `"C:/Users/maluw/Code/MCP/wechat_official_account_mcp/main.py"`

### Q: 配置后工具不可用？

1. 确认配置文件格式正确（JSON 格式）
2. 确认路径正确
3. 重启 Claude Desktop
4. 检查 Python 环境是否正确

## 下一步

配置完成后：
1. 重启 Claude Desktop
2. 在对话中测试：询问可用工具
3. 使用 `wechat_auth` 工具配置或验证微信公众号信息
4. 开始使用文章发布等功能

