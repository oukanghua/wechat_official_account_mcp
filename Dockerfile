# 使用Python官方镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 配置pip使用国内镜像源以加速下载
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn \
    # 配置apt使用阿里云镜像源以加速下载
    && sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
    # 更新包列表并安装系统依赖
    && apt-get update \
    && apt-get install -y --no-install-recommends --fix-missing \
       gcc \
       python3-dev \
       curl \
    && rm -rf /var/lib/apt/lists/* && \
    # 安装Python依赖 (FastMCP 2.0)
    pip install --upgrade pip && \
    pip install --no-cache-dir fastmcp>=2.0.0 requests python-dotenv && \
    python -c "import fastmcp; print(f'FastMCP {fastmcp.__version__} installed successfully')" || echo "Warning: FastMCP package installation may have issues"

# 复制项目文件
COPY . .

# 创建数据目录（用于存储数据库）
RUN mkdir -p /app/data

# MCP 服务器支持多种模式：
# - HTTP模式：默认模式，通过端口3003对外提供服务
# - stdio模式：通过标准输入输出通信（主要用于传统MCP客户端）
# - SSE模式：服务器发送事件模式
# 
# 环境变量控制：
# - MCP_TRANSPORT=http     # HTTP模式（Docker部署推荐）
# - MCP_TRANSPORT=stdio    # stdio模式（传统MCP客户端）
# - MCP_TRANSPORT=sse      # SSE模式（实时通知）
CMD ["python", "main.py"]
