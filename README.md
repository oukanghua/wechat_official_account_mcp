# 微信公众号 MCP 服务器

一个功能完整的微信公众号管理 MCP 服务器，合并了 `dify_wechat_plugin` 和 `wechat-official-account-mcp` 的功能。

## 功能特性

### MCP 工具

1. **认证管理** (`wechat_auth`)
   - 配置微信公众号 AppID、AppSecret、Token、EncodingAESKey
   - 获取和刷新 Access Token
   - 查看当前配置

2. **素材管理** (`wechat_media_upload`)
   - 上传临时素材（图片、语音、视频、缩略图）
   - 获取临时素材
   - 支持文件路径或 Base64 编码数据上传

3. **图文消息图片上传** (`wechat_upload_img`)
   - 上传图文消息内所需的图片
   - 不占用素材库限制
   - 返回可直接使用的图片 URL

4. **永久素材管理** (`wechat_permanent_media`)
   - 上传、获取、删除永久素材
   - 获取素材列表和统计信息
   - 支持图片、语音、视频、缩略图、图文消息

5. **草稿管理** (`wechat_draft`)
   - 创建、获取、删除、更新图文草稿
   - 获取草稿列表和统计信息
   - 支持多篇文章的草稿

6. **发布管理** (`wechat_publish`)
   - 发布草稿到微信公众号
   - 获取发布状态
   - 删除已发布文章
   - 获取发布列表

### 消息接收服务器

独立的 HTTP 服务器用于接收和处理微信公众号消息：

- 支持文本、图片、语音、链接、事件等多种消息类型
- 支持明文和加密两种模式
- 自动验证微信服务器签名
- **集成 Dify AI 支持**（可选）
- **超时和重试机制**（5秒超时，自动重试）
- **客服消息模式**（可选）
- **交互等待模式**（可选）

## 项目结构

```
wechat_official_account_mcp/
├── mcp/                    # MCP 服务器功能（独立）
│   ├── server.py          # MCP 服务器主文件
│   └── tools/              # MCP 工具
│       ├── auth.py         # 认证工具
│       ├── media.py        # 素材管理工具
│       ├── draft.py        # 草稿管理工具
│       └── publish.py      # 发布工具
│
├── server/                 # 微信消息服务器功能（独立）
│   ├── wechat_server.py    # 消息服务器主文件
│   ├── custom_message.py   # 客服消息发送器
│   ├── handlers/           # 消息处理器
│   └── utils/              # 服务器专用工具
│
├── shared/                  # 共享代码
│   ├── models.py           # 数据模型
│   ├── config.py           # 配置管理
│   ├── storage/            # 存储管理
│   └── utils/              # 共享工具（微信 API 客户端等）
│
├── main_mcp.py             # MCP 服务器入口
├── main_server.py          # 消息服务器入口
└── requirements.txt        # 依赖列表
```

## 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd wechat_official_account_mcp
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
# 微信公众号基础配置（必需）
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
WECHAT_TOKEN=your_token
WECHAT_ENCODING_AES_KEY=your_encoding_aes_key  # 可选

# 消息服务器配置（可选）
WECHAT_SERVER_PORT=8000  # 生产环境建议使用 80 或 443
WECHAT_SERVER_HOST=0.0.0.0

# HTTPS 配置（使用 443 端口时需要）
# WECHAT_SSL_CERT=/path/to/cert.pem
# WECHAT_SSL_KEY=/path/to/key.pem

# 消息处理配置（可选）
WECHAT_TIMEOUT_MESSAGE=内容生成耗时较长，请稍等...
WECHAT_RETRY_WAIT_TIMEOUT_RATIO=0.7
WECHAT_ENABLE_CUSTOM_MESSAGE=false
WECHAT_CONTINUE_WAITING_MESSAGE=生成答复中，继续等待请回复1
WECHAT_MAX_CONTINUE_COUNT=2

# Dify AI 集成（可选）
DIFY_API_KEY=your_dify_api_key
DIFY_APP_ID=your_dify_app_id
DIFY_BASE_URL=https://api.dify.ai/v1
```

## 使用

### 启动 MCP 服务器

MCP 服务器通过 stdio 与客户端通信：

```bash
python main_mcp.py
```

### 启动消息服务器

消息服务器提供 HTTP/HTTPS 接口接收微信消息：

```bash
python main_server.py
```

**端口配置**：
- 默认端口：8000（开发环境）
- 生产环境：建议使用 80（HTTP）或 443（HTTPS）
- 微信要求：服务器必须使用 80 或 443 端口

**配置端口**（在 `.env` 文件中）：
```env
# 使用 80 端口（HTTP）
WECHAT_SERVER_PORT=80

# 或使用 443 端口（HTTPS，需要 SSL 证书）
WECHAT_SERVER_PORT=443
WECHAT_SSL_CERT=/path/to/cert.pem
WECHAT_SSL_KEY=/path/to/key.pem
```

**注意事项**：
1. 使用 80 端口需要 root 权限（Linux/Mac）或管理员权限（Windows）
2. 使用 443 端口需要配置 SSL 证书（推荐使用 Let's Encrypt）
3. 生产环境建议使用 Nginx 等反向代理提供 HTTPS，而不是直接在 Flask 中启用 SSL

### 配置 MCP 客户端

#### Claude Desktop

编辑配置文件（Windows）：
```
%APPDATA%\Claude\claude_desktop_config.json
```

添加配置：
```json
{
  "mcpServers": {
    "wechat-official-account": {
      "command": "python",
      "args": ["C:\\path\\to\\wechat_official_account_mcp\\main_mcp.py"],
      "env": {
        "WECHAT_APP_ID": "your_app_id",
        "WECHAT_APP_SECRET": "your_app_secret"
      }
    }
  }
}
```

#### Cursor

编辑设置文件，添加 MCP 服务器配置。

## 部署

### Docker 部署

#### 构建镜像

```bash
docker build -t wechat-mcp .
```

#### 运行容器

```bash
docker-compose up -d
```

### 生产环境部署

**重要**：微信公众号要求服务器使用 **80（HTTP）** 或 **443（HTTPS）** 端口。

**推荐方案**：使用 Nginx 反向代理
- 应用运行在 8000 端口（非特权端口，不需要 root 权限）
- Nginx 监听 80/443 端口，转发到应用
- 使用 Let's Encrypt 提供免费 HTTPS 证书

详细部署说明请参考：[DEPLOYMENT.md](DEPLOYMENT.md)

## 消息服务器特性

### 超时处理机制

- **5 秒超时**: 符合微信要求，如果 AI 处理在 5 秒内完成，直接返回结果
- **自动重试**: 超时后返回 HTTP 500，触发微信重试（最多 3 次）
- **灵活配置**: 可配置重试等待超时系数

### 响应模式

#### 1. 客服消息模式

启用方式：
```env
WECHAT_ENABLE_CUSTOM_MESSAGE=true
```

工作流程：
1. AI 处理超时时，先返回超时提示消息
2. 处理完成后通过客服消息 API 发送完整响应

#### 2. 交互等待模式

启用方式：
```env
WECHAT_ENABLE_CUSTOM_MESSAGE=false
WECHAT_CONTINUE_WAITING_MESSAGE=生成答复中，继续等待请回复1
WECHAT_MAX_CONTINUE_COUNT=2
```

工作流程：
1. AI 处理超时时，提示用户回复"1"继续等待
2. 用户回复"1"后继续等待 AI 处理
3. 最多等待 N 次（可配置）

### Dify AI 集成

配置 Dify API 后，消息会自动调用 AI 处理：

```env
DIFY_API_KEY=your_dify_api_key
DIFY_APP_ID=your_dify_app_id
```

如果不配置，消息会返回默认回复。

## 常见问题

### 1. MCP 服务器启动失败

**原因**: Python 路径或依赖问题

**解决**:
- 检查 Python 版本（推荐 3.8+）
- 确保所有依赖已安装：`pip install -r requirements.txt`
- 检查 `.env` 文件配置是否正确

### 2. 消息服务器验证失败

**原因**: Token 不匹配或 URL 不正确

**解决**:
- 检查 `.env` 文件中的 `WECHAT_TOKEN` 是否与微信公众号平台一致
- 检查服务器 URL 是否正确
- 确保服务器可以访问

### 3. 消息解密失败

**原因**: EncodingAESKey 配置错误

**解决**:
- 检查 `.env` 文件中的 `WECHAT_ENCODING_AES_KEY` 是否与微信公众号平台一致
- 确保使用正确的加密模式

### 4. AI 处理超时

**原因**: AI 处理时间过长

**解决**:
- 启用客服消息模式：`WECHAT_ENABLE_CUSTOM_MESSAGE=true`
- 或启用交互等待模式
- 优化 Dify 应用的处理速度

## 开发

### 项目结构说明

- **mcp/**: MCP 服务器功能，提供工具接口
- **server/**: 消息服务器功能，接收和处理微信消息
- **shared/**: 两个功能模块共用的代码

### 添加新工具

1. 在 `mcp/tools/` 目录下创建新工具文件
2. 实现 `register_*_tools()` 函数注册工具
3. 实现 `handle_*_tool()` 函数处理工具调用
4. 在 `mcp/server.py` 中注册新工具

### 添加新消息处理器

1. 在 `server/handlers/` 目录下创建新处理器文件
2. 继承 `MessageHandler` 基类
3. 实现 `handle_message()` 方法
4. 在 `server/wechat_server.py` 中注册新处理器

## 许可证

MIT License

## 致谢

- [dify_wechat_plugin](https://github.com/bikeread/dify_wechat_plugin) - 微信公众号 Dify 插件
- [wechat-official-account-mcp](https://github.com/xwang152-jack/wechat-official-account-mcp) - 微信公众号 MCP 服务
