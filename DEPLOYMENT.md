# 部署指南

## 微信公众号服务器配置

微信公众号要求服务器使用 **80（HTTP）** 或 **443（HTTPS）** 端口。

### 方案 1: 直接使用 80/443 端口（不推荐生产环境）

#### 使用 80 端口（HTTP）

```bash
# 在 .env 文件中配置
WECHAT_SERVER_PORT=80

# 启动（需要 root 权限）
sudo python main_server.py
```

#### 使用 443 端口（HTTPS）

```bash
# 在 .env 文件中配置
WECHAT_SERVER_PORT=443
WECHAT_SSL_CERT=/path/to/cert.pem
WECHAT_SSL_KEY=/path/to/key.pem

# 启动（需要 root 权限）
sudo python main_server.py
```

**注意事项**：
- 需要 root 权限才能绑定 80/443 端口
- 直接使用 Flask 的 SSL 支持在生产环境不推荐
- 建议使用反向代理（Nginx/Apache）

### 方案 2: 使用 Nginx 反向代理（推荐）

这是生产环境的推荐方案。

#### 1. 安装 Nginx

```bash
# Ubuntu/Debian
sudo apt-get install nginx

# CentOS/RHEL
sudo yum install nginx
```

#### 2. 配置 Nginx

编辑 `/etc/nginx/sites-available/wechat-server`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # HTTP 重定向到 HTTPS（可选）
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书配置
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 代理到 Flask 应用（运行在 8000 端口）
    location /wechat {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 3. 启用配置

```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/wechat-server /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

#### 4. 启动应用

```bash
# 应用运行在 8000 端口（不需要 root 权限）
python main_server.py
```

#### 5. 配置微信公众号

在微信公众平台配置：
- **服务器地址(URL)**: `https://your-domain.com/wechat`
- **Token**: 与 `.env` 中的 `WECHAT_TOKEN` 相同

### 方案 3: 使用 Docker + Nginx

#### 1. 创建 Nginx 配置文件

创建 `nginx/nginx.conf`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location /wechat {
        proxy_pass http://wechat-server:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 2. 更新 docker-compose.yml

```yaml
services:
  wechat-server:
    build: .
    container_name: wechat_message_server
    restart: unless-stopped
    environment:
      - WECHAT_APP_ID=${WECHAT_APP_ID}
      - WECHAT_APP_SECRET=${WECHAT_APP_SECRET}
      - WECHAT_TOKEN=${WECHAT_TOKEN}
      - WECHAT_SERVER_PORT=8000
    command: python main_server.py
    networks:
      - wechat_network

  nginx:
    image: nginx:alpine
    container_name: wechat_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - wechat-server
    networks:
      - wechat_network

networks:
  wechat_network:
    driver: bridge
```

#### 3. 启动服务

```bash
docker-compose up -d
```

### 获取 SSL 证书

#### 使用 Let's Encrypt（免费）

```bash
# 安装 Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书（自动配置 Nginx）
sudo certbot --nginx -d your-domain.com

# 证书会自动续期
```

#### 使用其他 CA

从证书颁发机构获取 SSL 证书，然后配置到 Nginx 或 Flask 应用。

### 防火墙配置

确保防火墙允许 80 和 443 端口：

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 验证配置

1. **测试服务器**：
   ```bash
   curl http://your-domain.com/wechat?signature=test&timestamp=123&nonce=test&echostr=test
   ```

2. **在微信公众平台提交配置**：
   - URL: `https://your-domain.com/wechat`
   - Token: 配置的 Token
   - 加密方式: 根据是否配置 EncodingAESKey 选择

3. **验证通过后**，服务器即可接收微信消息。

## 常见问题

### 1. 端口被占用

```bash
# 检查端口占用
sudo lsof -i :80
sudo lsof -i :443

# 或使用 netstat
sudo netstat -tulpn | grep :80
```

### 2. 权限不足

```bash
# 使用 root 权限运行（不推荐）
sudo python main_server.py

# 或使用反向代理（推荐）
# 让 Nginx 监听 80/443，应用运行在非特权端口
```

### 3. SSL 证书问题

- 确保证书文件路径正确
- 检查证书是否过期
- 验证证书与域名匹配

### 4. 微信验证失败

- 检查 URL 是否正确（必须使用 HTTPS，除非使用 80 端口）
- 验证 Token 是否匹配
- 检查服务器是否可访问（微信服务器需要能访问你的服务器）

## 推荐配置

**生产环境推荐**：
- ✅ 使用 Nginx 反向代理
- ✅ 使用 HTTPS（443 端口）
- ✅ 使用 Let's Encrypt 免费证书
- ✅ 应用运行在 8000 端口（非特权端口）
- ✅ 使用 systemd 或 Docker 管理服务

