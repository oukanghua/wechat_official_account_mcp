# 微信公众号 MCP 服务器 (FastMCP 2.0)

一个功能完整的微信公众号管理 MCP 服务器，基于 **FastMCP 2.0** 框架，支持多种传输模式，提供认证、素材管理、草稿和发布等完整的公众号管理功能。

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境
创建 `.env` 文件：
```env
# 微信公众号配置
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret

# FastMCP 2.0 配置（可选）
MCP_TRANSPORT=http      # 传输模式: stdio(默认), http, sse
MCP_HOST=0.0.0.0       # HTTP 服务器绑定地址
MCP_PORT=3003          # HTTP 服务器端口

# 静态网页服务器配置（可选）
STATIC_PAGE_PORT=3004  # 静态网页HTTP服务器端口
```

### 启动服务器

#### stdio 模式（默认，MCP客户端使用）
```bash
python main.py
```

#### HTTP 模式（Web应用/API集成）
```bash
export MCP_TRANSPORT=http
python main.py
# 访问: http://localhost:3003/mcp
```

#### Docker 部署
```bash
docker compose up -d
docker compose logs -f
```

---

## 📖 功能概览

### 账号类型支持

- **服务号**：支持所有功能（认证、素材、草稿、发布）
- **订阅号（认证）**：支持所有功能（认证、素材、草稿、发布）  
- **订阅号（未认证）**：支持认证、素材、草稿功能，**不支持发布功能**

> **重要**：发布服务（`wechat_publish`）仅限认证的公众号和服务号使用。

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

### 统一工具调用接口
```python
# 使用通用接口调用任何工具
wechat_tool_call(tool_name="wechat_auth", arguments={"action": "status"})
```

### 7. 静态网页管理 (`static_page`)
```python
# 生成随机命名静态网页
static_page(action="generate", htmlContent="<html><body><h1>Hello World</h1></body></html>")

# 生成自定义命名静态网页
static_page(action="generate", htmlContent="<html><body><h1>Custom Page</h1></body></html>", filename="my_page")

# 启动HTTP服务器（可选，服务会自动随主服务启动）
static_page(action="start_server", port=3004)

# 查看服务器状态
static_page(action="server_status")

# 列出所有静态网页
static_page(action="list")

# 获取网页信息
static_page(action="info", filename="my_page")

# 删除静态网页
static_page(action="delete", filename="my_page")
```
**功能**：动态生成静态HTML网页，通过HTTP服务器访问，支持随机命名和自定义命名，提供完整的网页管理功能

## ⚙️ 部署配置

### 多传输协议支持

| 模式 | 描述 | 适用场景 | 启动方式 |
|------|------|----------|----------|
| `stdio` | 标准输入输出模式 | 传统 MCP 客户端集成 | `python main.py` |
| `http` | HTTP REST API 模式 | Web 应用、API 集成 | `export MCP_TRANSPORT=http && python main.py` |
| `sse` | 服务器发送事件模式 | 实时通知、流式响应 | `export MCP_TRANSPORT=sse && python main.py` |

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
│   └── phub_template.html # P站样式模板
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
│       └── static_page_server.py # 静态网页HTTP服务器
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