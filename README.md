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
# 访问: http://localhost:3003
```

#### Docker 部署
```bash
docker compose up -d
docker compose logs -f
```

---

## 📖 详细功能说明

### 账号类型支持

- **服务号**：支持所有功能（认证、素材、草稿、发布）
- **订阅号（认证）**：支持所有功能（认证、素材、草稿、发布）  
- **订阅号（未认证）**：支持认证、素材、草稿功能，**不支持发布功能**

> **重要**：发布服务（`wechat_publish`）仅限认证的公众号和服务号使用。

### MCP 工具

#### 1. 认证管理 (`wechat_auth`)
```python
# 登录认证
wechat_auth(action="login")
# 查看认证状态  
wechat_auth(action="status")
# 登出
wechat_auth(action="logout")
```

**功能**：
- 配置微信公众号 AppID、AppSecret
- 获取和刷新 Access Token
- 查看当前配置

#### 2. 素材管理 (`wechat_media_upload`)
```python
# 上传临时素材
wechat_media_upload(file_path="/path/to/image.jpg", media_type="image")
```

**功能**：
- 上传临时素材（图片、语音、视频、缩略图）
- 获取临时素材
- 支持文件路径或 Base64 编码数据上传

#### 3. 图文消息图片上传 (`wechat_upload_img`)
```python
# 上传图文消息所需图片
wechat_upload_img(file_path="/path/to/image.jpg")
```

**功能**：
- 上传图文消息内所需的图片
- 不占用素材库限制
- 返回可直接使用的图片 URL

#### 4. 永久素材管理 (`wechat_permanent_media`)
```python
# 获取永久媒体素材
wechat_permanent_media(media_id="your_media_id")
```

**功能**：
- 上传、获取、删除永久素材
- 获取素材列表和统计信息
- 支持图片、语音、视频、缩略图、图文消息

#### 5. 草稿管理 (`wechat_draft`)
```python
# 创建草稿
wechat_draft(title="文章标题", content="文章内容")
```

**功能**：
- 创建、获取、删除、更新图文草稿
- 获取草稿列表和统计信息
- 支持多篇文章的草稿

#### 6. 发布管理 (`wechat_publish`)
```python
# 发布草稿到微信公众号
wechat_publish(media_id="draft_media_id")
```

**功能**：
- 发布草稿到微信公众号
- 获取发布状态
- 删除已发布文章
- 获取发布列表
- **权限要求**：仅认证的公众号和服务号可以使用发布功能

#### 7. 模板工具 (`wechat_template`)
```python
# 使用P站样式模板
wechat_template(action="use", template_name="phub_template", title="标题", content="内容")
```

**功能**：
- 根据P站样式模板生成公众号文章HTML内容
- 支持多种内容块：标题、章节、统计、引用、代码、进度条等
- AI可以自动识别用户说"使用p站模板"或"使用phub模板"时使用此工具
- 详见 [模板使用指南](docs/template_usage.md)

#### 统一工具调用接口
```python
# 使用通用接口调用任何工具
wechat_tool_call(tool_name="wechat_auth", arguments={"action": "status"})
```

### MCP 资源

#### P站样式模板 (`template://phub_template`)
- P站（Pornhub）样式的公众号文章HTML模板
- AI可以读取模板内容了解结构
- 配合模板工具使用，生成符合样式的HTML文章

---

## 🔧 FastMCP 2.0 新特性

### 多传输协议支持

| 模式 | 描述 | 适用场景 | 启动方式 |
|------|------|----------|----------|
| `stdio` | 标准输入输出模式 | 传统 MCP 客户端集成 | `python main.py` |
| `http` | HTTP REST API 模式 | Web 应用、API 集成 | `export MCP_TRANSPORT=http && python main.py` |
| `sse` | 服务器发送事件模式 | 实时通知、流式响应 | `export MCP_TRANSPORT=sse && python main.py` |

### 纯 FastMCP 2.0 实现
- ✅ **单一框架**：完全基于 FastMCP 2.0 构建
- ✅ **现代化API**：装饰器风格的简洁编程接口
- ✅ **完整功能**：支持所有 MCP 工具和资源

### 环境变量配置

```bash
# MCP 服务器配置
MCP_TRANSPORT=http      # 传输协议选择
MCP_HOST=0.0.0.0       # 绑定地址（HTTP 模式）
MCP_PORT=3003          # 端口（HTTP 模式）

# 微信公众号配置
WECHAT_APP_ID=your_app_id      # 微信应用 ID
WECHAT_APP_SECRET=your_secret  # 微信应用密钥

# 其他配置
PYTHONUNBUFFERED=1    # 输出不缓冲
PYTHONPATH=/app       # Python 模块路径
```

---

## 🐳 Docker 部署

### 使用 Docker Compose（推荐）
```bash
# 构建并启动
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

### 环境变量配置
在 `.env` 文件中配置环境变量：

```env
# 微信公众号配置
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret

# FastMCP 2.0 配置
MCP_TRANSPORT=http
MCP_HOST=0.0.0.0
MCP_PORT=3003
```

### Docker 健康检查
服务自动配置健康检查：
- 检测 HTTP 服务可用性
- 30秒间隔检测
- 失败时自动重启

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
│   └── template.py        # 模板工具
├── shared/                # 共享模块
│   ├── storage/          # 存储管理
│   │   ├── auth_manager.py     # 认证管理器
│   │   └── storage_manager.py  # 存储管理器
│   └── utils/            # 工具类
│       └── wechat_api_client.py # 微信 API 客户端
├── data/                  # 数据目录（持久化存储）
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
curl http://localhost:8000/health
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