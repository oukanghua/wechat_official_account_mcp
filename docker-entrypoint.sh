#!/bin/bash
set -e

# 确保数据目录存在
mkdir -p /app/data

# 如果提供了环境变量，更新配置文件
if [ -n "$WECHAT_APP_ID" ] && [ -n "$WECHAT_APP_SECRET" ]; then
    echo "环境变量已提供，将使用环境变量配置"
fi

# 执行传入的命令
exec "$@"

