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
- 可配置的消息处理器

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

### 3. 配置环境变量（可选）

创建 `.env` 文件：

```env
# 微信公众号配置（可选，也可通过 MCP 工具配置）
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
WECHAT_TOKEN=your_token
WECHAT_ENCODING_AES_KEY=your_encoding_aes_key

# 服务器配置
WECHAT_SERVER_PORT=8000
WECHAT_SERVER_HOST=0.0.0.0
WECHAT_API_PROXY=api.weixin.qq.com
WECHAT_API_TIMEOUT=30
```

## Docker 部署

> **注意**：如果在中国大陆地区遇到网络连接问题，请参考下面的"网络问题解决方案"部分。

### 使用 Docker Compose（推荐）

1. **创建环境变量文件**

创建 `.env` 文件（或直接在 docker-compose.yml 中设置）：

```env
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
WECHAT_TOKEN=your_token
WECHAT_ENCODING_AES_KEY=your_encoding_aes_key
WECHAT_SERVER_PORT=8000
WECHAT_API_PROXY=api.weixin.qq.com
WECHAT_API_TIMEOUT=30
```

2. **构建并启动服务**

使用快速启动脚本（推荐）：

**Linux/Mac:**
```bash
chmod +x docker-run.sh
./docker-run.sh
```

**Windows:**
```cmd
docker-run.bat
```

或手动执行：

```bash
# 构建镜像（生产环境）
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

**开发模式**（需要实时修改代码）：

```bash
# 使用开发配置（挂载代码目录）
docker-compose -f docker-compose.dev.yml build
docker-compose -f docker-compose.dev.yml up -d
```

3. **配置微信公众号**

在微信公众平台配置服务器地址为：`http://your-domain:8000/wechat`

### 使用 Docker 直接运行

1. **构建镜像**

```bash
docker build -t wechat-official-account-mcp .
```

2. **运行容器**

```bash
# 运行消息接收服务器
docker run -d \
  --name wechat-server \
  -p 8000:8000 \
  -e WECHAT_APP_ID=your_app_id \
  -e WECHAT_APP_SECRET=your_app_secret \
  -e WECHAT_TOKEN=your_token \
  -e WECHAT_ENCODING_AES_KEY=your_encoding_aes_key \
  -v $(pwd)/data:/app/data \
  wechat-official-account-mcp

# 查看日志
docker logs -f wechat-server
```

3. **运行 MCP 服务器**

```bash
# MCP 服务器通过 stdio 运行，通常不需要单独容器
# 如果需要，可以这样运行：
docker run -it \
  --name wechat-mcp \
  -v $(pwd)/data:/app/data \
  -e WECHAT_APP_ID=your_app_id \
  -e WECHAT_APP_SECRET=your_app_secret \
  wechat-official-account-mcp \
  python main.py
```

### Docker 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `WECHAT_APP_ID` | 微信公众号 AppID | - |
| `WECHAT_APP_SECRET` | 微信公众号 AppSecret | - |
| `WECHAT_TOKEN` | 微信公众号 Token | - |
| `WECHAT_ENCODING_AES_KEY` | 消息加密密钥 | - |
| `WECHAT_SERVER_PORT` | 消息接收服务器端口 | 8000 |
| `WECHAT_SERVER_HOST` | 消息接收服务器主机 | 0.0.0.0 |
| `WECHAT_API_PROXY` | 微信 API 代理地址 | api.weixin.qq.com |
| `WECHAT_API_TIMEOUT` | API 请求超时时间（秒） | 30 |

### 网络问题解决方案

如果遇到无法连接到 Docker Hub 的问题（常见于中国大陆地区），可以使用以下方法：

#### 方法 1：配置 Docker 镜像加速器（推荐）

1. **配置 Docker Desktop 镜像加速器**

在 Docker Desktop 设置中添加镜像加速器：
- 阿里云：`https://registry.cn-hangzhou.aliyuncs.com`
- 腾讯云：`https://mirror.ccs.tencentyun.com`
- 网易：`https://hub-mirror.c.163.com`

2. **或使用国内优化的 Docker Compose 配置**

```bash
# 使用国内优化的配置
docker-compose -f docker-compose.china.yml build
docker-compose -f docker-compose.china.yml up -d
```

#### 方法 2：使用已存在的本地镜像

```bash
# 先手动拉取镜像（如果网络允许）
docker pull python:3.12-slim

# 然后再构建
docker-compose build
```

#### 方法 3：使用代理

如果已有代理，可以配置 Docker 使用代理：

```bash
# 设置代理环境变量
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port
docker-compose build
```

## 使用

### 作为 MCP 服务器使用

#### 1. 配置 MCP 客户端

**Windows 用户**（Claude Desktop 配置路径：`%APPDATA%\Claude\claude_desktop_config.json`）：

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

**Linux/Mac 用户**：

```json
{
  "mcpServers": {
    "wechat-official-account": {
      "command": "python",
      "args": [
        "/path/to/wechat_official_account_mcp/main.py"
      ]
    }
  }
}
```

**注意**：
- 将路径替换为你的实际项目路径
- 如果已配置 `.env` 文件，可以省略 `env` 部分
- 详细配置说明请参考 `MCP_SETUP.md`

#### 2. 使用工具

在 AI 对话中，可以调用以下工具：

- `wechat_auth` - 配置微信公众号信息
- `wechat_media_upload` - 上传临时素材
- `wechat_upload_img` - 上传图文消息图片
- `wechat_permanent_media` - 管理永久素材
- `wechat_draft` - 管理草稿
- `wechat_publish` - 发布文章

### 作为消息接收服务器使用

#### 1. 启动服务器

```bash
python api/wechat_server.py
```

或者使用环境变量配置端口：

```bash
WECHAT_SERVER_PORT=8000 python api/wechat_server.py
```

#### 2. 配置微信公众号

1. 登录微信公众平台 (https://mp.weixin.qq.com/)
2. 进入"设置与开发" -> "基本配置"
3. 在"服务器配置"下：
   - 服务器地址(URL): `http://your-domain:8000/wechat`
   - Token: 与配置中的 `WECHAT_TOKEN` 相同
   - 消息加解密方式: 根据是否配置 `WECHAT_ENCODING_AES_KEY` 选择明文或安全模式
   - 如果使用安全模式，EncodingAESKey 要与配置中的相同

## 项目结构

```
wechat_official_account_mcp/
├── main.py                 # MCP 服务器主文件
├── api/
│   └── wechat_server.py    # 微信公众号消息接收服务器
├── tools/                  # MCP 工具实现
│   ├── auth.py            # 认证工具
│   ├── media.py           # 素材管理工具
│   ├── draft.py           # 草稿管理工具
│   └── publish.py         # 发布工具
├── storage/                # 存储管理
│   ├── auth_manager.py    # 认证管理器
│   └── storage_manager.py  # 存储管理器
├── handlers/               # 消息处理器
│   ├── text.py            # 文本消息处理器
│   ├── image.py           # 图片消息处理器
│   ├── voice.py           # 语音消息处理器
│   ├── link.py            # 链接消息处理器
│   ├── event.py           # 事件处理器
│   └── unsupported.py     # 不支持的消息处理器
├── utils/                  # 工具类
│   ├── wechat_api_client.py    # 微信 API 客户端
│   ├── wechat_crypto.py        # 消息加解密工具
│   └── message_parser.py       # 消息解析工具
├── models.py               # 数据模型
├── config.py              # 配置管理
└── requirements.txt        # 依赖列表
```

## 开发

### 运行测试

```bash
python -m pytest tests/
```

### 代码检查

```bash
flake8 .
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

- [dify_wechat_plugin](https://github.com/bikeread/dify_wechat_plugin) - 微信公众号 Dify 插件
- [wechat-official-account-mcp](https://github.com/xwang152-jack/wechat-official-account-mcp) - 微信公众号 MCP 服务（TypeScript 版本）
