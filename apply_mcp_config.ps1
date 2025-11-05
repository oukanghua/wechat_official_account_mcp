# 快速应用 MCP 配置到 Claude Desktop
# 使用方法: .\apply_mcp_config.ps1

param(
    [switch]$Force  # 强制覆盖现有配置
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "微信公众号 MCP 配置应用工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 配置文件路径
$configPath = "$env:APPDATA\Claude\claude_desktop_config.json"
$configDir = Split-Path -Parent $configPath

# 获取项目路径
$projectPath = (Get-Location).Path
$mainPyPath = Join-Path $projectPath "main.py"

# 检查 main.py 是否存在
if (-not (Test-Path $mainPyPath)) {
    Write-Host "`n❌ 错误: 未找到 main.py 文件" -ForegroundColor Red
    Write-Host "请确保在项目根目录运行此脚本" -ForegroundColor Yellow
    exit 1
}

# 转换路径格式
$mainPyPathEscaped = $mainPyPath -replace '\\', '\\'

Write-Host "`n项目路径: $projectPath" -ForegroundColor Green
Write-Host "main.py 路径: $mainPyPathEscaped" -ForegroundColor Green

# 读取 .env 文件
$envVars = @{}
if (Test-Path ".env") {
    Write-Host "`n读取 .env 文件..." -ForegroundColor Yellow
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim() -replace '^["'']|["'']$', ''  # 移除引号
            if ($key -and $value) {
                $envVars[$key] = $value
            }
        }
    }
    Write-Host "✅ 读取到 $($envVars.Count) 个环境变量" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  未找到 .env 文件" -ForegroundColor Yellow
}

# 构建 MCP 配置
$mcpServerConfig = @{
    command = "python"
    args = @($mainPyPathEscaped)
}

# 如果有环境变量，添加到配置
if ($envVars.Count -gt 0) {
    $mcpServerConfig.env = @{}
    if ($envVars.WECHAT_APP_ID) { $mcpServerConfig.env.WECHAT_APP_ID = $envVars.WECHAT_APP_ID }
    if ($envVars.WECHAT_APP_SECRET) { $mcpServerConfig.env.WECHAT_APP_SECRET = $envVars.WECHAT_APP_SECRET }
    if ($envVars.WECHAT_TOKEN) { $mcpServerConfig.env.WECHAT_TOKEN = $envVars.WECHAT_TOKEN }
    if ($envVars.WECHAT_ENCODING_AES_KEY) { $mcpServerConfig.env.WECHAT_ENCODING_AES_KEY = $envVars.WECHAT_ENCODING_AES_KEY }
}

# 读取或创建现有配置
$existingConfig = @{}
if (Test-Path $configPath) {
    Write-Host "`n读取现有配置..." -ForegroundColor Yellow
    try {
        $existingConfig = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable
        Write-Host "✅ 成功读取现有配置" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  现有配置文件格式有误" -ForegroundColor Yellow
        if (-not $Force) {
            $response = Read-Host "是否覆盖现有配置？(y/N)"
            if ($response -ne 'y' -and $response -ne 'Y') {
                Write-Host "已取消操作" -ForegroundColor Yellow
                exit 0
            }
        }
        $existingConfig = @{}
    }
} else {
    Write-Host "`n配置文件不存在，将创建新文件" -ForegroundColor Yellow
}

# 确保 mcpServers 存在
if (-not $existingConfig.mcpServers) {
    $existingConfig.mcpServers = @{}
}

# 检查是否已存在配置
if ($existingConfig.mcpServers["wechat-official-account"] -and -not $Force) {
    Write-Host "`n⚠️  配置 'wechat-official-account' 已存在" -ForegroundColor Yellow
    $response = Read-Host "是否覆盖？(y/N)"
    if ($response -ne 'y' -and $response -ne 'Y') {
        Write-Host "已取消操作" -ForegroundColor Yellow
        exit 0
    }
}

# 更新配置
$existingConfig.mcpServers["wechat-official-account"] = $mcpServerConfig

# 确保目录存在
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Force -Path $configDir | Out-Null
    Write-Host "✅ 已创建配置目录" -ForegroundColor Green
}

# 备份现有配置
if (Test-Path $configPath) {
    $backupPath = "$configPath.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item $configPath $backupPath
    Write-Host "✅ 已备份现有配置: $backupPath" -ForegroundColor Green
}

# 转换为 JSON 并保存
try {
    $jsonConfig = $existingConfig | ConvertTo-Json -Depth 10
    $jsonConfig | Set-Content -Path $configPath -Encoding UTF8 -NoNewline
    
    Write-Host "`n✅ 配置已成功保存！" -ForegroundColor Green
    Write-Host "`n配置文件路径: $configPath" -ForegroundColor Cyan
    Write-Host "`n配置内容:" -ForegroundColor Cyan
    Write-Host $jsonConfig -ForegroundColor Gray
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "下一步操作:" -ForegroundColor Cyan
    Write-Host "1. 重启 Claude Desktop" -ForegroundColor Yellow
    Write-Host "2. 在对话中测试 MCP 工具" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    
} catch {
    Write-Host "`n❌ 保存配置失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

