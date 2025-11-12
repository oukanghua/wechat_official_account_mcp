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

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install --no-cache-dir mcp requests python-dotenv aiohttp && \
    python -c "import mcp; print('MCP installed')" || echo "Warning: MCP package may not be installed"

# 复制项目文件
COPY . .

# 创建数据目录（用于存储 SQLite 数据库）
RUN mkdir -p /app/data

# MCP 服务器通过 stdio 通信，不需要暴露端口
# 使用 stdin/stdout 进行通信
CMD ["python", "main.py"]
