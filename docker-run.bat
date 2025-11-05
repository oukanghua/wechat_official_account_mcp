@echo off
REM Docker 快速启动脚本 (Windows)

echo 微信公众号 MCP 服务器 Docker 启动脚本
echo.

REM 检查 Docker 是否安装
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 错误：未安装 Docker
    exit /b 1
)

REM 检查 Docker Compose 是否安装
where docker-compose >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    docker compose version >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo 错误：未安装 Docker Compose
        exit /b 1
    )
)

REM 检查环境变量文件
if not exist ".env" (
    echo 警告：未找到 .env 文件
    echo 请创建 .env 文件并设置以下变量：
    echo   WECHAT_APP_ID=your_app_id
    echo   WECHAT_APP_SECRET=your_app_secret
    echo   WECHAT_TOKEN=your_token
    echo   WECHAT_ENCODING_AES_KEY=your_encoding_aes_key
    echo.
    set /p continue="是否继续？（y/n）"
    if /i not "%continue%"=="y" exit /b 1
)

REM 创建数据目录
if not exist "data" mkdir data

REM 选择操作
echo 请选择操作：
echo 1. 构建并启动服务
echo 2. 仅构建镜像
echo 3. 启动服务
echo 4. 停止服务
echo 5. 查看日志
echo 6. 重启服务
echo 7. 使用国内镜像源构建（适用于网络问题）
echo.
set /p choice="请输入选项 (1-7): "

if "%choice%"=="1" (
    echo 构建并启动服务...
    docker-compose build
    docker-compose up -d
    echo 服务已启动！
    echo 查看日志: docker-compose logs -f
) else if "%choice%"=="2" (
    echo 构建镜像...
    docker-compose build
    echo 构建完成！
) else if "%choice%"=="3" (
    echo 启动服务...
    docker-compose up -d
    echo 服务已启动！
    echo 查看日志: docker-compose logs -f
) else if "%choice%"=="4" (
    echo 停止服务...
    docker-compose down
    echo 服务已停止！
) else if "%choice%"=="5" (
    echo 查看日志（按 Ctrl+C 退出）...
    docker-compose logs -f
) else if "%choice%"=="6" (
    echo 重启服务...
    docker-compose restart
    echo 服务已重启！
) else if "%choice%"=="7" (
    echo 使用国内镜像源构建...
    docker-compose -f docker-compose.china.yml build
    docker-compose -f docker-compose.china.yml up -d
    echo 服务已启动！
    echo 查看日志: docker-compose -f docker-compose.china.yml logs -f
) else (
    echo 无效选项
    exit /b 1
)

