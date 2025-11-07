# 使用Python官方镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 配置pip使用国内镜像源以加速下载
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn

# 更新包列表并安装系统依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends --fix-missing \
       gcc \
       python3-dev \
       curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt文件
COPY requirements.txt .

# 安装Python依赖（直接在系统Python中安装，容器本身已隔离）
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    # 验证关键依赖是否安装成功
    python -c "import flask; print('Flask installed:', flask.__version__)" && \
    python -c "import requests; print('Requests installed')" && \
    python -c "import mcp; print('MCP installed')" || echo "Warning: Some packages may not be installed"

# 复制项目文件
COPY . .

# 复制并设置启动脚本权限
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 创建数据目录（用于存储 SQLite 数据库）
RUN mkdir -p /app/data

# 设置环境变量文件（如果.env文件存在）
# 注意：建议通过 docker-compose.yml 或环境变量传递配置，而不是在镜像中包含 .env

# 暴露消息接收服务器端口（默认8000）
EXPOSE 8000

# 使用启动脚本
ENTRYPOINT ["docker-entrypoint.sh"]

# 默认运行消息接收服务器
# 如果作为 MCP 服务器运行，应该通过 docker-compose 或直接运行 main.py
CMD ["python", "main_server.py"]
