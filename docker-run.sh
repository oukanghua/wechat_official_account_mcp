#!/bin/bash
# Docker 快速启动脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}微信公众号 MCP 服务器 Docker 启动脚本${NC}"
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误：未安装 Docker${NC}"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}错误：未安装 Docker Compose${NC}"
    exit 1
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}警告：未找到 .env 文件${NC}"
    echo "请创建 .env 文件并设置以下变量："
    echo "  WECHAT_APP_ID=your_app_id"
    echo "  WECHAT_APP_SECRET=your_app_secret"
    echo "  WECHAT_TOKEN=your_token"
    echo "  WECHAT_ENCODING_AES_KEY=your_encoding_aes_key"
    echo ""
    read -p "是否继续？（y/n）" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 创建数据目录
mkdir -p data

# 选择操作
echo "请选择操作："
echo "1. 构建并启动服务（docker-compose up -d）"
echo "2. 仅构建镜像（docker-compose build）"
echo "3. 启动服务（docker-compose up -d）"
echo "4. 停止服务（docker-compose down）"
echo "5. 查看日志（docker-compose logs -f）"
echo "6. 重启服务（docker-compose restart）"
echo "7. 运行 MCP 服务器（交互式）"
echo "8. 使用国内镜像源构建（适用于网络问题）"
echo ""
read -p "请输入选项 (1-8): " choice

case $choice in
    1)
        echo -e "${GREEN}构建并启动服务...${NC}"
        docker-compose build
        docker-compose up -d
        echo -e "${GREEN}服务已启动！${NC}"
        echo "查看日志: docker-compose logs -f"
        ;;
    2)
        echo -e "${GREEN}构建镜像...${NC}"
        docker-compose build
        echo -e "${GREEN}构建完成！${NC}"
        ;;
    3)
        echo -e "${GREEN}启动服务...${NC}"
        docker-compose up -d
        echo -e "${GREEN}服务已启动！${NC}"
        echo "查看日志: docker-compose logs -f"
        ;;
    4)
        echo -e "${YELLOW}停止服务...${NC}"
        docker-compose down
        echo -e "${GREEN}服务已停止！${NC}"
        ;;
    5)
        echo -e "${GREEN}查看日志（按 Ctrl+C 退出）...${NC}"
        docker-compose logs -f
        ;;
    6)
        echo -e "${GREEN}重启服务...${NC}"
        docker-compose restart
        echo -e "${GREEN}服务已重启！${NC}"
        ;;
    7)
        echo -e "${GREEN}运行 MCP 服务器（交互式）...${NC}"
        docker run -it --rm \
          -v $(pwd)/data:/app/data \
          -e WECHAT_APP_ID=${WECHAT_APP_ID:-} \
          -e WECHAT_APP_SECRET=${WECHAT_APP_SECRET:-} \
          wechat-official-account-mcp \
          python main.py
        ;;
    8)
        echo -e "${GREEN}使用国内镜像源构建...${NC}"
        docker-compose -f docker-compose.china.yml build
        docker-compose -f docker-compose.china.yml up -d
        echo -e "${GREEN}服务已启动！${NC}"
        echo "查看日志: docker-compose -f docker-compose.china.yml logs -f"
        ;;
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

