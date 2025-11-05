# 配置说明

本项目包含两个主要功能，每个功能有不同的配置需求：

## 功能 1: 文章发布（MCP 工具）

### 所需配置
- ✅ `WECHAT_APP_ID` - 微信公众号 AppID
- ✅ `WECHAT_APP_SECRET` - 微信公众号 AppSecret

### 功能说明
通过 MCP 协议调用以下工具：
- `wechat_draft` - 创建和管理草稿
- `wechat_publish` - 发布草稿到公众号
- `wechat_media_upload` - 上传素材
- `wechat_upload_img` - 上传图文消息图片
- `wechat_permanent_media` - 管理永久素材

### 使用方式
1. 配置 MCP 客户端（Claude Desktop 或 Cursor）
2. 在 AI 对话中调用 `wechat_publish` 等工具
3. 工具会自动使用已配置的 AppID 和 AppSecret 获取 Access Token

## 功能 2: 消息接收服务器

### 所需配置
- ✅ `WECHAT_APP_ID` - 微信公众号 AppID（已配置）
- ✅ `WECHAT_APP_SECRET` - 微信公众号 AppSecret（已配置）
- ⚠️ `WECHAT_TOKEN` - 服务器验证 Token（可选，用于接收消息）
- ⚠️ `WECHAT_ENCODING_AES_KEY` - 消息加密密钥（可选，用于安全模式）

### 功能说明
独立的 HTTP 服务器，用于接收和处理微信公众号消息：
- 接收用户发送的文本、图片、语音、链接等消息
- 处理关注、取消关注等事件
- 自动回复消息

### 使用方式
1. 在微信公众平台配置服务器地址：`http://your-domain:8000/wechat`
2. 设置 Token（与 `WECHAT_TOKEN` 相同）
3. 选择消息加解密方式（明文或安全模式）

## 当前配置状态

✅ **文章发布功能**：已完全配置，可以使用
- AppID: 已配置
- AppSecret: 已配置

⚠️ **消息接收功能**：部分配置
- AppID: ✅ 已配置
- AppSecret: ✅ 已配置
- Token: ⚠️ 需要配置（如果只使用文章发布功能，可以不配置）
- EncodingAESKey: ⚠️ 可选（如果只使用文章发布功能，可以不配置）

## 配置建议

### 如果只需要文章发布功能
只需配置：
```env
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
```

### 如果需要消息接收功能
需要额外配置：
```env
WECHAT_TOKEN=your_token
WECHAT_ENCODING_AES_KEY=your_encoding_aes_key  # 可选，如果使用安全模式
```

## 验证配置

检查配置是否正确：
```bash
docker exec wechat_message_server python -c "from storage.auth_manager import AuthManager; am = AuthManager(); c = am.get_config(); print('AppID:', c.get('app_id') if c else '未配置'); print('AppSecret:', '已配置' if c and c.get('app_secret') else '未配置'); print('Token:', c.get('token') if c else '未配置')"
```

