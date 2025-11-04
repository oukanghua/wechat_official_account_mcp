# 微信公众号管理器MCP（WeChat Official Account MCP）

这是一个功能完整的微信公众号管理插件，提供了丰富的API和工具来管理微信公众号内容和交互。

## 功能特性

### 核心功能
- 微信公众号消息接收与回复
- 文本、图片、语音、链接等多种消息类型处理
- 事件处理（关注、取消关注、菜单点击等）
- 微信公众号API封装

### 工具集
- 获取访问令牌
- 创建图文草稿
- 发布草稿文章
- 上传临时媒体文件

## 项目结构

```
wechat_complete_plugin/
├── api/                # API路由模块
│   ├── __init__.py
│   └── routes.py
├── tools/              # 工具模块
│   ├── __init__.py
│   ├── get_access_token.py
│   ├── create_draft.py
│   ├── publish_draft.py
│   └── upload_media.py
├── handlers/           # 消息处理器
│   ├── __init__.py
│   ├── base.py         # 基础消息处理器
│   ├── text.py         # 文本消息处理器
│   ├── image.py        # 图片消息处理器
│   ├── voice.py        # 语音消息处理器
│   ├── link.py         # 链接消息处理器
│   ├── event.py        # 事件处理器
│   └── unsupported.py  # 不支持的消息处理器
├── utils/              # 工具类
│   ├── __init__.py
│   ├── wechat_api_client.py  # 微信API客户端
│   ├── wechat_message_crypto.py  # 微信消息加解密
│   └── message_parser.py  # 消息解析工具
├── config.py           # 配置管理
├── requirements.txt    # 依赖列表
├── .env.example        # 环境变量示例
└── __init__.py
```

## 安装与配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 文件为 `.env`，并填入实际的配置信息：

```bash
cp .env.example .env
```

### 3. 必要配置项

- `WECHAT_APP_ID`: 微信公众号的AppID
- `WECHAT_APP_SECRET`: 微信公众号的AppSecret
- `WECHAT_TOKEN`: 微信公众号配置的Token
- `WECHAT_ENCODING_AES_KEY`: 微信公众号配置的EncodingAESKey（可选，用于消息加密）

## 使用方法

### 启动服务

```bash
python -m wechat_complete_plugin.api.routes
```

服务默认在 `http://0.0.0.0:5000` 启动。

### 微信公众号配置

1. 登录微信公众号后台
2. 在「开发」->「基本配置」中配置服务器地址（URL）为您的服务器地址
3. 配置Token和EncodingAESKey与环境变量保持一致
4. 启用消息加解密方式（可选）

## 工具使用

### 获取访问令牌

```python
from wechat_complete_plugin.tools import GetAccessTokenTool

# 创建工具实例
tool = GetAccessTokenTool()

# 设置凭据
tool.runtime.credentials = {
    'app_id': 'your_app_id',
    'app_secret': 'your_app_secret'
}

# 调用工具
for message in tool.invoke({'force_refresh': False}):
    print(message.content)
```

### 创建图文草稿

```python
from wechat_complete_plugin.tools import CreateDraftTool

# 创建工具实例
tool = CreateDraftTool()

# 设置凭据
tool.runtime.credentials = {
    'app_id': 'your_app_id',
    'app_secret': 'your_app_secret'
}

# 调用工具
params = {
    'title': '文章标题',
    'content': '<p>文章内容</p>',
    'thumb_media_id': 'thumb_media_id',
    'author': '作者',
    'digest': '文章摘要'
}

for message in tool.invoke(params):
    print(message.content)
```

### 发布草稿

```python
from wechat_complete_plugin.tools import PublishDraftTool

# 创建工具实例
tool = PublishDraftTool()

# 设置凭据
tool.runtime.credentials = {
    'app_id': 'your_app_id',
    'app_secret': 'your_app_secret'
}

# 调用工具
for message in tool.invoke({'media_id': 'draft_media_id'}):
    print(message.content)
```

### 上传临时媒体

```python
from wechat_complete_plugin.tools import UploadMediaTool

# 创建工具实例
tool = UploadMediaTool()

# 设置凭据
tool.runtime.credentials = {
    'app_id': 'your_app_id',
    'app_secret': 'your_app_secret'
}

# 调用工具
params = {
    'media_type': 'image',
    'media_url': 'https://example.com/image.jpg'
}

for message in tool.invoke(params):
    print(message.content)
```

## 消息处理流程

1. 微信服务器发送消息到配置的URL
2. API接收消息并验证签名
3. 根据消息类型路由到相应的处理器
4. 处理器处理消息并生成回复
5. API将回复返回给微信服务器

## 注意事项

1. 确保服务器能够被外网访问，微信服务器需要回调您的接口
2. 访问令牌有7200秒的有效期，插件内部已实现自动刷新
3. 临时媒体文件有效期为3天
4. 图文消息内容需符合微信公众号的内容规范

## 错误处理

所有API调用都包含完善的错误处理机制，会记录详细的日志信息。在生产环境中，建议定期检查日志以排查潜在问题。

## 日志配置

通过环境变量 `LOG_LEVEL` 可以设置日志级别，默认为 `INFO`。支持的日志级别包括：DEBUG、INFO、WARNING、ERROR、CRITICAL。

## 许可证

MIT License