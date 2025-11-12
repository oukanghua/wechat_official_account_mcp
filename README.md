# 微信公众号 MCP 服务器

一个功能完整的微信公众号管理 MCP 服务器，提供认证、素材管理、草稿和发布等完整的公众号管理功能。

## 功能特性

### 账号类型支持

- **服务号**：支持所有功能（认证、素材、草稿、发布）
- **订阅号（认证）**：支持所有功能（认证、素材、草稿、发布）
- **订阅号（未认证）**：支持认证、素材、草稿功能，**不支持发布功能**

> **注意**：发布服务（`wechat_publish`）仅限认证的公众号和服务号使用。未认证的订阅号无法使用发布功能。

### MCP 工具

1. **认证管理** (`wechat_auth`)
   - 配置微信公众号 AppID、AppSecret
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
   - **权限要求**：仅认证的公众号和服务号可以使用发布功能

## 项目结构

```
wechat_official_account_mcp/
├── main.py                 # MCP 服务器主文件
├── main_mcp.py            # MCP 服务器入口（可选）
├── tools/                  # MCP 工具
│   ├── auth.py            # 认证工具
│   ├── media.py           # 素材管理工具
│   ├── draft.py           # 草稿管理工具
│   └── publish.py         # 发布工具
│
├── shared/                # 共享模块
│   ├── storage/          # 存储管理
│   │   ├── auth_manager.py    # 认证管理器
│   │   └── storage_manager.py # 存储管理器
│   └── utils/            # 工具类
│       └── wechat_api_client.py # 微信 API 客户端
├── data/                  # 数据目录（不提交到 git）
│   └── auth_config.json  # 认证配置（本地存储）
├── Dockerfile            # Docker 构建文件
└── docker-compose.yml    # Docker Compose 配置
```

## 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd wechat_official_account_mcp
```

### 2. 安装依赖

```bash
pip install mcp requests python-dotenv aiohttp
```

或者使用 requirements.txt（如果存在）：

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
# 微信公众号基础配置（必需）
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
```

## 使用

### 账号权限说明

在使用发布功能前，请确认您的公众号类型：

- ✅ **服务号**：可以使用所有功能，包括发布
- ✅ **认证的订阅号**：可以使用所有功能，包括发布
- ❌ **未认证的订阅号**：可以使用认证、素材、草稿功能，但**无法使用发布功能**

如果您的账号不支持发布功能，调用发布接口时会返回相应的错误信息。

### 启动 MCP 服务器

MCP 服务器通过 stdio 与客户端通信：

```bash
python main.py
```

或者使用入口文件：

```bash
python mcp_server.py
```

### Docker 方式运行

#### 使用 Docker Compose（推荐）

```bash
# 构建并启动
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

#### 使用 Docker

```bash
# 构建镜像
docker build -t wechat-mcp .

# 运行容器
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -e WECHAT_APP_ID=your_app_id \
  -e WECHAT_APP_SECRET=your_app_secret \
  wechat-mcp
```

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
      "args": ["C:\\path\\to\\wechat_official_account_mcp\\main.py"],
      "env": {
        "WECHAT_APP_ID": "your_app_id",
        "WECHAT_APP_SECRET": "your_app_secret"
      }
    }
  }
}
```