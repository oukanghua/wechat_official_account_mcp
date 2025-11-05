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

## 使用

### 作为 MCP 服务器使用

#### 1. 配置 MCP 客户端

在 Claude Desktop 或 Cursor 的 MCP 配置文件中添加：

```json
{
  "mcpServers": {
    "wechat-official-account": {
      "command": "python",
      "args": ["/path/to/wechat_official_account_mcp/main.py"]
    }
  }
}
```

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
