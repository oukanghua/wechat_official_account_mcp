# 远程服务器排查指南

## 问题：HTTP 返回非 200

当在远程服务器上部署后，微信公众平台验证失败，返回非 200 状态码。

## 排查步骤

### 1. 检查服务器是否正常运行

```bash
# 查看容器状态
docker compose ps

# 查看启动日志
docker compose logs --tail=50 wechat-server

# 实时查看日志
docker compose logs -f wechat-server
```

### 2. 检查配置是否正确

```bash
# 进入容器检查环境变量
docker compose exec wechat-server env | grep WECHAT

# 检查 .env 文件
cat .env | grep WECHAT_TOKEN
```

**重要检查项：**
- `WECHAT_TOKEN` 必须与微信公众平台配置的 Token **完全一致**
- `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET` 必须正确
- 确保 `.env` 文件在项目根目录

### 3. 查看详细的验证请求日志

当微信公众平台发送验证请求时，日志会显示：

```
收到微信验证请求: signature=xxx..., timestamp=xxx, nonce=xxx, echostr=xxx...
微信服务器验证失败: 期望签名=xxx, 实际签名=xxx
验证参数: token=xxx..., timestamp=xxx, nonce=xxx
```

**如果看到这些日志：**
- 检查 `期望签名` 和 `实际签名` 是否不同
- 如果不同，说明 Token 不匹配
- 确保 `.env` 文件中的 `WECHAT_TOKEN` 与微信公众平台一致

### 4. 测试服务器可访问性

```bash
# 从服务器本地测试
curl "http://localhost:80/health"

# 从外网测试（替换为你的服务器IP或域名）
curl "http://your-server-ip:80/health"
```

### 5. 检查防火墙和端口

```bash
# 检查端口是否开放
netstat -tlnp | grep 80

# 检查防火墙规则（CentOS/RHEL）
firewall-cmd --list-ports

# 如果端口未开放，添加规则
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --reload
```

### 6. 手动测试验证接口

创建一个测试脚本 `test_verification.sh`：

```bash
#!/bin/bash

TOKEN="your_token_here"  # 替换为你的 Token
TIMESTAMP=$(date +%s)
NONCE="test123"
ECHOSTR="test_echostr"

# 计算签名
TEMP_LIST=($TOKEN $TIMESTAMP $NONCE)
IFS=$'\n' SORTED=($(sort <<<"${TEMP_LIST[*]}"))
TEMP_STR=$(IFS=''; echo "${SORTED[*]}")
SIGNATURE=$(echo -n "$TEMP_STR" | sha1sum | cut -d' ' -f1)

# 发送请求
curl -v "http://localhost:80/wechat?signature=$SIGNATURE&timestamp=$TIMESTAMP&nonce=$NONCE&echostr=$ECHOSTR"
```

运行测试：
```bash
chmod +x test_verification.sh
./test_verification.sh
```

**预期结果：**
- 如果返回 `test_echostr`，说明服务器配置正确
- 如果返回 403，检查 Token 是否正确

### 7. 检查微信公众平台配置

在微信公众平台（https://mp.weixin.qq.com）：
1. 进入"开发" -> "基本配置"
2. 检查"服务器配置"：
   - **URL**: `http://your-server-ip:80/wechat` 或 `http://your-domain.com/wechat`
   - **Token**: 必须与 `.env` 文件中的 `WECHAT_TOKEN` **完全一致**（区分大小写）
   - **EncodingAESKey**: 如果使用加密模式，必须与 `.env` 文件中的 `WECHAT_ENCODING_AES_KEY` 一致

### 8. 常见问题

#### 问题 1: Token 不匹配

**症状：** 日志显示"微信服务器验证失败"，期望签名和实际签名不同

**解决：**
1. 检查 `.env` 文件中的 `WECHAT_TOKEN`
2. 检查微信公众平台配置的 Token
3. 确保两者完全一致（包括大小写、空格等）

#### 问题 2: 服务器无法访问

**症状：** 微信公众平台提示"服务器没有正确响应"

**解决：**
1. 确保服务器可以从外网访问
2. 检查防火墙是否开放 80 端口
3. 检查域名解析是否正确（如果使用域名）
4. 确保服务器正在运行：`docker compose ps`

#### 问题 3: 端口配置错误

**症状：** 容器运行但无法访问

**解决：**
1. 检查 `docker-compose.yml` 中的端口映射
2. 检查 `.env` 文件中的 `WECHAT_SERVER_PORT`
3. 确保端口映射正确：`"${WECHAT_SERVER_PORT:-8000}:${WECHAT_SERVER_PORT:-8000}"`

#### 问题 4: 配置未加载

**症状：** 日志显示"未配置微信公众号信息"或"未配置 token"

**解决：**
1. 检查 `.env` 文件是否存在
2. 检查环境变量是否正确传递到容器
3. 重启容器：`docker compose restart wechat-server`

## 调试技巧

### 查看实时日志

```bash
# 查看所有日志
docker compose logs -f

# 只查看 wechat-server 的日志
docker compose logs -f wechat-server

# 查看最近 100 行日志
docker compose logs --tail=100 wechat-server
```

### 进入容器调试

```bash
# 进入容器
docker compose exec wechat-server bash

# 检查环境变量
env | grep WECHAT

# 检查配置文件
cat /app/.env  # 如果存在

# 手动测试
python -c "import os; print(os.getenv('WECHAT_TOKEN'))"
```

### 测试健康检查

```bash
# 从容器内测试
docker compose exec wechat-server curl http://localhost:80/health

# 从服务器本地测试
curl http://localhost:80/health
```

## 验证成功的标志

当微信公众平台验证成功时，日志会显示：

```
收到微信验证请求: signature=xxx..., timestamp=xxx, nonce=xxx, echostr=xxx...
微信服务器验证成功，返回 echostr: xxx
```

并且在微信公众平台会显示"配置成功"。

## 需要帮助？

如果以上步骤都无法解决问题，请提供：
1. 完整的错误日志：`docker compose logs wechat-server`
2. `.env` 文件内容（隐藏敏感信息）
3. 微信公众平台的错误提示
4. 服务器配置信息（端口、网络模式等）



