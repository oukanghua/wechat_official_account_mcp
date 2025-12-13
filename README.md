# 微信公众号 MCP 服务器 (FastMCP 2.0)

基于 **FastMCP 2.0** 的微信公众号服务器，集成 **OpenAI AI 智能回复**功能。支持微信公众号消息处理、静态网页服务和现代化聊天界面。

## 🚀 功能特性

### 核心功能
- **📱 微信公众号消息处理**: 支持文本、图片、语音等多种消息类型
- **🤖 AI 智能回复**: 集成 OpenAI GPT 模型，提供智能自动回复
- **⚡ 优化的 Web 聊天 API**: 核心 `/chat/api/send` 接口优化后延迟降低至约 1 秒
- **📄 静态网页服务**: 提供 HTML 页面管理和 HTTP 服务
- **💬 聊天界面**: 现代化的 Web 聊天界面，支持实时对话
- **🔗 MCP 协议支持**: 兼容 MCP 2.0 标准，支持 stdio、HTTP、SSE 传输

### 技术架构
- **后端框架**: FastMCP 2.0
- **AI 服务**: OpenAI GPT API
- **HTTP 服务**: 内置优化的 HTTP 服务器（默认端口 3004）
- **数据存储**: 本地文件系统存储
- **前端界面**: 响应式 HTML/CSS/JavaScript
- **性能优化**: 事件循环复用、HTTP 客户端池化、配置懒加载

### 性能优化亮点
- **🔄 事件循环复用**: 避免频繁创建销毁事件循环，降低线程切换开销
- **🌐 HTTP 客户端池化**: 复用 AI 服务连接，减少 TCP 握手次数
- **📊 配置懒加载**: 仅在初始化时加载配置，避免重复 I/O 操作
- **⏱️ 低延迟聊天 API**: 从前端请求到模型调用延迟优化至约 0.96 秒
- **💪 错误恢复机制**: 自动处理连接异常，确保服务稳定性

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境
- 创建 `.env` 文件：

```bash
cp .env.example .env
```

```env
# ============================================
# 🔥 MCP基础配置（必需）
# ============================================
MCP_TRANSPORT=http      # 传输协议选择：stdio/http/sse
MCP_HOST=0.0.0.0       # Web服务器绑定地址（可选，有默认值）
MCP_PORT=3003          # Web服务器端口（可选，有默认值）
# ============================================
# ⚙️ Web服务器/消息服务配置（必需）
# ============================================
# 端口配置
# - 开发环境: 3003
# - 生产环境: 80 (HTTP) 或 443 (HTTPS)
WECHAT_MSG_SERVER_PORT=80   # 📋 服务器端口
WECHAT_MSG_SERVER_HOST=0.0.0.0  # 📋 监听地址
WECHAT_MSG_CONTEXT_PATH=/wechat-oa # 静态网页服务上下文路径（可选，默认/）
WECHAT_MSG_AI_TIMEOUT=3                      # 公众号接口AI回复超时时间（秒），页面访问不设置超时
WECHAT_MSG_AI_TIMEOUT_PROMPT="\n--内容未完全生成，请访问http://ip:port/wechat-oa/chat" # 流式模式超时提示语
WECHAT_OFFICIAL_API_URL=https://api.weixin.qq.com  # 微信服务端API基础URL

# ============================================
# 🤖 OpenAI AI服务配置（AI智能聊天功能）
# ============================================
OPENAI_API_KEY=your_openai_api_key          # OpenAI API密钥
OPENAI_MODEL=gpt-3.5-turbo                  # OpenAI模型选择
OPENAI_MAX_TOKENS=40000                      # 最大token数量
OPENAI_TEMPERATURE=0.7                      # 回复创造性（0.0-2.0）
OPENAI_TIMEOUT=300                        # API超时时间（秒）
OPENAI_INTERACTION_MODE=stream                  # AI交互模式：stream（流式）或block（阻塞）
OPENAI_PROMPT="你是一个专业的热点资讯分析师，专注于实时追踪、深度解析和前瞻预测全球范围内的热点新闻事件，当前任务是简洁快速回复公众号用户的问题。"
# 聊天界面配置密码（用于保护配置功能）
OPENAI_CONFIG_PASSWORD=your_config_password_here     
# ============================================
# 🔥 微信公众号基础配置
# ============================================
WECHAT_APP_ID=your_app_id           # 🔥 微信公众号AppID（必需）
WECHAT_APP_SECRET=your_app_secret   # 🔥 微信公众号AppSecret（必需）
# ============================================
# 🔥 微信公众号【消息推送】配置
# ============================================
WECHAT_TOKEN=your_wechat_token      # 🔥 微信服务【消息推送】验证Token（必需）
```

### 微信公众号后台配置

1. **登录微信公众号后台**：访问 [mp.weixin.qq.com](https://mp.weixin.qq.com/) 并登录

2. **配置服务器地址**：
   - 进入「开发」>「基本配置」
   - 点击「修改配置」按钮
   - 填写以下信息：
     - **URL**：填写服务器地址，格式为 `http://your_domain.com:3004/wechat/reply`（若设置了WECHAT_MSG_CONTEXT_PATH，则为 `http://your_domain.com:3004${WECHAT_MSG_CONTEXT_PATH}/wechat/reply`）
     - **Token**：填写与 `.env` 文件中 `WECHAT_TOKEN` 相同的值
     - **EncodingAESKey**：随机生成或自定义，选择「明文模式」或「兼容模式」
   - 点击「提交」按钮，微信会验证服务器地址是否可用

3. **启用服务器配置**：
   - 提交成功后，点击「启用」按钮
   - 此时微信公众号的消息将自动推送到你的服务器

4. **配置消息回复**：
   - 进入「开发」>「消息管理」>「消息回复」
   - 确保自动回复功能已开启
   - 选择「关键词回复」或「自动回复」配置

### 启动服务器

#### stdio 模式（默认，MCP客户端使用）
```bash
python main.py
```

#### HTTP 模式（Web应用/API集成）
```bash
export MCP_TRANSPORT=http
python main.py
# 访问: http://localhost:port/mcp
```

### Web 服务器使用示例

#### 访问聊天界面
```bash
# 访问介绍页
# URL: http://localhost:3004/WECHAT_MSG_CONTEXT_PATH/
# 访问聊天界面
# URL: http://localhost:3004/WECHAT_MSG_CONTEXT_PATH/chat/
```

#### 调用优化的聊天 API

**使用 PowerShell（Windows）：**
```powershell
# 发送聊天请求（优化后延迟约 0.96 秒）
Invoke-RestMethod -Uri http://localhost:3004/chat/api/send -Method Post -ContentType "application/json" -Body '{"message": "你好", "history": []}'
```

**使用 curl（Linux/Mac）：**
```bash
# 发送聊天请求（优化后延迟约 0.96 秒）
curl -X POST http://localhost:3004/chat/api/send \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "history": []}'
```

#### 验证优化效果

1. 启动服务器，观察控制台输出
2. 发送 API 请求，查看日志中的性能指标
3. 优化后的日志会显示：
   ```
   INFO: 请求数据处理完成，耗时: 0.01秒
   INFO: 获取AI服务实例完成，耗时: 0.02秒
   INFO: 创建/获取事件循环完成，耗时: 0.01秒
   INFO: 开始调用AI模型，耗时: 0.96秒
   ```

---

## 📖 功能概览

### 账号类型支持

- **服务号**：支持所有功能（认证、素材、草稿、发布）
- **订阅号（认证）**：支持所有功能（认证、素材、草稿、发布）  
- **订阅号（未认证）**：支持认证、素材、草稿功能，**不支持发布功能**

> **重要**：发布服务（`wechat_publish`）仅限认证的公众号和服务号使用。

### Web 服务器端点

Web 服务器提供以下核心 API 端点：

| 端点 | 方法 | 描述 | 延迟优化 |
|------|------|------|----------|
| `/api/chat` 或 `/chat/api/send` | POST | AI 聊天消息发送接口 | ✅ 优化至约 0.96 秒 |
| `/api/config` 或 `/chat/api/config` | GET/POST | 获取/保存聊天服务配置 | - |
| `/api/validate-password` | POST | 密码验证接口 | - |
| `/` 或 `/chat/` | GET | 主页面（聊天界面） | - |
| `/static/*` | GET | 静态资源访问 | - |
| `/wechat/reply` | GET | 微信服务器验证接口 | - |
| `/wechat/reply` | POST | 微信消息接收和自动回复接口 | - |

#### 核心优化端点：`/chat/api/send`

**请求格式**：
```json
{
  "message": "你好",
  "history": [
    {"role": "user", "content": "之前的问题"},
    {"role": "assistant", "content": "之前的回答"}
  ]
}
```

**响应格式**：
- 流式响应（Server-Sent Events）
- 逐字返回 AI 生成内容
- 支持实时显示生成过程

**优化亮点**：
- 事件循环复用，避免线程切换开销
- HTTP 客户端池化，减少连接建立时间
- 配置懒加载，避免重复 I/O 操作
- 错误自动恢复，确保服务稳定性
- 从前端请求到模型调用延迟优化至约 0.96 秒

---

## 🛠️ MCP 工具

### 1. 认证管理 (`wechat_auth`)
```python
# 登录认证
wechat_auth(action="login")
# 查看认证状态  
wechat_auth(action="status")
# 登出
wechat_auth(action="logout")
```
**功能**：配置微信公众号 AppID、AppSecret，获取和刷新 Access Token，查看当前配置

### 2. 素材管理 (`wechat_temporary_media`)
```python
# 上传临时素材
wechat_temporary_media(file_path="/path/to/image.jpg", media_type="image")
```
**功能**：上传临时素材（图片、语音、视频、缩略图），获取临时素材，支持文件路径或 Base64 编码数据上传

### 3. 图文消息图片上传 (`wechat_upload_img`)
```python
# 上传图文消息所需图片
wechat_upload_img(file_path="/path/to/image.jpg")
```
**功能**：上传图文消息内所需的图片，不占用素材库限制，返回可直接使用的图片 URL

### 4. 永久素材管理 (`wechat_permanent_media`)
```python
# 获取永久媒体素材
wechat_permanent_media(media_id="your_media_id")
```
**功能**：上传、获取、删除永久素材，获取素材列表和统计信息，支持图片、语音、视频、缩略图、图文消息

### 5. 草稿管理 (`wechat_draft`)
```python
# 创建草稿
wechat_draft(article={
    "title": "文章标题",
    "content": "文章内容",
    "cover_media_id": "media_id",
    "author": "作者",
    "digest": "摘要"
})
```
**功能**：创建、获取、删除、更新图文草稿，获取草稿列表和统计信息，支持多篇文章的草稿

### 6. 发布管理 (`wechat_publish`)
```python
# 发布草稿到微信公众号
wechat_publish(media_id="draft_media_id", no_content=True)

# 获取发布列表（不返回content内容）
wechat_publish(action="list", no_content=True)
```
**功能**：发布草稿到微信公众号，获取发布状态，删除已发布文章，获取发布列表

### 7. 静态网页管理 (`static_page`)
```python
# 生成随机命名静态网页
static_page(action="generate", htmlContent="<html><body><h1>Hello World</h1></body></html>")

# 生成自定义命名静态网页
static_page(action="generate", htmlContent="<html><body><h1>Custom Page</h1></body></html>", filename="my_page")

# 启动Web服务器（可选，服务会自动随主服务启动）
static_page(action="start_server", port=3004)

# 启动集成服务器（包含微信消息处理和聊天界面）
static_page(action="start_integrated_server", port=3004)

# 查看服务器状态
static_page(action="server_status")

# 查看集成服务器状态
static_page(action="integrated_server_status")

# 停止集成服务器
static_page(action="stop_integrated_server")

# 列出所有静态网页
static_page(action="list")

# 获取网页信息
static_page(action="info", filename="my_page")

# 删除静态网页
static_page(action="delete", filename="my_page")
```
**功能**：动态生成静态HTML网页，集成服务器支持微信消息处理和AI聊天界面，提供完整的网页和消息管理功能

### 8. 统一工具调用接口
```python
# 使用通用接口调用任何工具
wechat_tool_call(tool_name="wechat_auth", arguments={"action": "status"})
```

## ⚙️ 部署配置

### 多传输协议支持

| 模式 | 描述 | 适用场景 | 启动方式 |
|------|------|----------|----------|
| `stdio` | 标准输入输出模式 | 传统 MCP 客户端集成 | `python main.py` |
| `http` | HTTP REST API 模式 | Web 应用、API 集成 | `export MCP_TRANSPORT=http && python main.py` |
| `sse` | 服务器发送事件模式 | 实时通知、流式响应 | `export MCP_TRANSPORT=sse && python main.py` |

### 性能优化配置

Web 服务器的性能优化功能默认启用，无需额外配置。优化包括：

1. **事件循环复用**：自动为每个线程初始化和复用事件循环
2. **HTTP 客户端池化**：AI 服务连接自动复用，减少 TCP 握手次数
3. **配置懒加载**：仅在服务初始化时加载配置，避免重复 I/O 操作
4. **错误自动恢复**：连接异常时自动重建 HTTP 客户端

#### 环境变量配置

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `MCP_HOST` | `0.0.0.0` | HTTP 服务器绑定地址 |
| `MCP_PORT` | `3003` | MCP HTTP 服务端口 |
| `WECHAT_MSG_SERVER_PORT` | `3004` | Web 服务器监听端口 |
| `WECHAT_MSG_SERVER_HOST` | `0.0.0.0` | Web 服务器监听地址 |
| `WECHAT_MSG_CONTEXT_PATH` | `` | 静态网页服务上下文路径 |
| `WECHAT_OFFICIAL_API_URL` | `https://api.weixin.qq.com` | 微信服务端API基础URL |
| `WECHAT_MSG_AI_TIMEOUT` | `4.8` | 公众号接口AI回复超时时间（秒） |
| `WECHAT_MSG_AI_TIMEOUT_PROMPT` | `\n\n（内容未完全生成，后续回复将继续完善）` | 流式模式超时提示语 |
| `OPENAI_CONFIG_PASSWORD` | `` | 聊天界面配置密码（用于保护配置功能） |

#### 性能监控

优化后的性能指标：
- **请求处理延迟**：从前端请求到 AI 模型调用延迟约 0.96 秒
- **每秒处理请求数**：支持高并发请求
- **连接复用率**：AI 服务连接复用率 > 90%

#### 日志查看

查看性能日志，确认优化效果：
```bash
# 本地运行
python main.py

# Docker 部署
docker compose logs -f
```

性能日志示例：
```
INFO: 请求数据处理完成，耗时: 0.01秒
INFO: 获取AI服务实例完成，耗时: 0.02秒
INFO: 创建/获取事件循环完成，耗时: 0.01秒
INFO: 开始调用AI模型，耗时: 0.96秒
```

### Docker 部署

#### 使用 Docker Compose（推荐）
```bash
# 构建并启动
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

Docker 部署包含以下特性：
- **自动健康检查**：30秒间隔检测服务可用性，失败时自动重启
- **环境变量配置**：支持 `.env` 文件配置所有参数
- **网络配置**：预配置网络和端口映射

---

## 📁 项目结构

```
wechat_official_account_mcp/
├── main.py                 # MCP 服务器主文件（FastMCP 2.0）
├── mcp_server.py           # 核心服务器实现
├── requirements.txt        # 项目依赖
├── .env.example           # 环境变量示例
├── Dockerfile             # Docker 构建文件
├── docker-compose.yml     # Docker Compose 配置
├── templates/             # 模板文件
│   ├── chat_template.html        # 聊天界面模板
│   ├── index_template.html        # 索引页面模板
│   ├── phub_template.html         # P站样式模板
│   └── static_pages_template.html # 静态网页模板
├── tools/                 # MCP 工具模块
│   ├── auth.py            # 认证工具
│   ├── media.py           # 素材管理工具
│   ├── draft.py           # 草稿管理工具
│   ├── publish.py         # 发布工具
│   ├── template.py        # 模板工具
│   └── static_pages.py    # 静态网页管理工具
├── shared/                # 共享模块
│   ├── storage/          # 存储管理
│   │   ├── auth_manager.py     # 认证管理器
│   │   └── storage_manager.py  # 存储管理器（已扩展静态网页支持）
│   └── utils/            # 工具类
│       ├── wechat_api_client.py # 微信 API 客户端
│       ├── web_server.py         # Web 服务器（优化过的聊天API）
│       └── ai_service.py         # AI 服务客户端（优化过的模型调用）
├── data/                  # 数据目录（持久化存储）
│   ├── storage.db         # 存储数据库
│   └── static_pages/      # 静态网页文件目录
│       └── metadata.json  # 网页元数据文件
└── logs/                  # 日志文件目录
```

---

## 🔌 MCP 客户端配置

### Claude Desktop

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
      "args": ["C:\\path\\to\\wechat_official_account_mcp\\main.py"],
      "env": {
        "WECHAT_APP_ID": "your_app_id",
        "WECHAT_APP_SECRET": "your_app_secret",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

### HTTP 模式客户端

对于 HTTP 模式，可以直接访问：
```bash
# 健康检查
curl http://localhost:3003/health

# API 调用示例
curl -X POST http://localhost:3003/tools/wechat_auth \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"action": "status"}}'
```

---

## 🐛 故障排除

### 常见问题

#### 1. FastMCP 2.0 导入失败
```bash
# 确保安装正确版本
pip install fastmcp>=2.0.0
pip install -r requirements.txt
```

#### 2. HTTP 模式启动失败
- 检查端口 `3003` 是否被占用
- 确认环境变量 `MCP_TRANSPORT=http` 已设置
- 检查防火墙设置

#### 3. Docker 部署问题
```bash
# 重新构建镜像
docker compose build --no-cache

# 查看详细日志
docker compose logs --details

# 重启服务
docker compose restart
```

#### 4. 发布功能不可用
- 确认公众号类型：发布功能仅限认证的公众号和服务号
- 检查认证状态：使用 `wechat_auth(action="status")` 查看
- 查看错误日志获取详细错误信息

### 日志位置
- **本地运行**：控制台输出 + `logs/mcp_server.log`
- **Docker 部署**：容器日志 `docker compose logs`

### 健康检查
```bash
# 检查 HTTP 服务状态
curl http://localhost:3003/health

# Docker 健康检查状态
docker ps --format "table {{.Names}}\t{{.Status}}"
```

---

## 📚 更新日志

### v2.0.0 (2024-12)
- ✨ **重大升级**：升级至 FastMCP 2.0 框架
- ✨ **多协议支持**：新增 HTTP 和 SSE 传输模式
- ✨ **智能兼容**：自动检测并回退到原始 MCP SDK
- 🔧 **架构重构**：使用装饰器风格 API
- 🔧 **增强日志**：完整的错误处理和日志记录
- 📦 **Docker 优化**：添加健康检查和网络配置
- ⚡ **性能优化**：Web 服务器聊天 API 延迟从 15-52 秒优化至约 0.96 秒
  - 事件循环复用，避免频繁创建销毁
  - HTTP 客户端池化，减少连接建立时间
  - 配置懒加载，避免重复 I/O 操作
  - 错误自动恢复，确保服务稳定性
- 📝 **文档完善**：统一的 README 文档和使用指南

### v1.x.x (之前版本)
- ✅ 基础 MCP 工具支持
- ✅ 微信公众号 API 集成
- ✅ stdio 传输模式

---

## 🤝 支持与贡献

### 获取帮助
1. 查看日志文件获取详细错误信息
2. 检查环境变量配置
3. 确认依赖版本兼容性
4. 参考故障排除章节

### 贡献代码
欢迎提交 Issue 和 Pull Request！

---

**FastMCP 2.0** 让 MCP 服务器开发更简单、更强大！ 🎉