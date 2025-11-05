# MCP 配置安装脚本 (Windows PowerShell)
# 此脚本将自动配置 Claude Desktop 的 MCP 设置

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "微信公众号 MCP 配置安装脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 获取配置路径
$configPath = "$env:APPDATA\Claude\claude_desktop_config.json"
$configDir = Split-Path -Parent $configPath

Write-Host "`n配置路径: $configPath" -ForegroundColor Yellow

# 检查 Claude Desktop 是否已安装
if (-not (Test-Path $configDir)) {
    Write-Host "`n❌ 未找到 Claude Desktop 配置目录" -ForegroundColor Red
    Write-Host "请先安装并运行 Claude Desktop" -ForegroundColor Yellow
    exit 1
}

# 获取当前项目路径
$projectPath = (Get-Location).Path
$mainPyPath = Join-Path $projectPath "main.py"

# 检查 main.py 是否存在
if (-not (Test-Path $mainPyPath)) {
    Write-Host "`n❌ 未找到 main.py 文件" -ForegroundColor Red
    Write-Host "请确保在项目根目录运行此脚本" -ForegroundColor Yellow
    exit 1
}

# 转换路径格式（Windows 使用反斜杠）
$mainPyPath = $mainPyPath -replace '\\', '\\'

Write-Host "`n项目路径: $mainPyPath" -ForegroundColor Green

# 读取现有配置（如果存在）
$existingConfig = @{}
if (Test-Path $configPath) {
    Write-Host "`n读取现有配置..." -ForegroundColor Yellow
    try {
        $existingConfig = Get-Content $configPath -Raw | ConvertFrom-Json -AsHashtable
        if ($existingConfig.mcpServers) {
            Write-Host "✅ 找到现有 MCP 配置" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️  现有配置文件格式有误，将创建新配置" -ForegroundColor Yellow
        $existingConfig = @{}
    }
} else {
    Write-Host "`n创建新配置文件..." -ForegroundColor Yellow
}

# 读取环境变量（从 .env 文件）
$envVars = @{}
if (Test-Path ".env") {
    Write-Host "`n从 .env 文件读取环境变量..." -ForegroundColor Yellow
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            if ($key -and $value) {
                $envVars[$key] = $value
            }
        }
    }
    Write-Host "✅ 读取到 $($envVars.Count) 个环境变量" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  未找到 .env 文件，将使用默认值" -ForegroundColor Yellow
}

# 构建 MCP 配置
$mcpConfig = @{
    command = "python"
    args = @($mainPyPath)
    env = @{
        WECHAT_APP_ID = $envVars.WECHAT_APP_ID
        WECHAT_APP_SECRET = $envVars.WECHAT_APP_SECRET
        WECHAT_TOKEN = $envVars.WECHAT_TOKEN
        WECHAT_ENCODING_AES_KEY = $envVars.WECHAT_ENCODING_AES_KEY
    }
}

# 移除空值
$mcpConfig.env = $mcpConfig.env.GetEnumerator() | Where-Object { $_.Value } | ForEach-Object {
    @{ $_.Key = $_.Value }
} | ForEach-Object { $_ }

# 如果没有环境变量，移除 env 部分
if ($mcpConfig.env.Count -eq 0) {
    $mcpConfig.Remove('env')
}

# 合并到现有配置
if (-not $existingConfig.mcpServers) {
    $existingConfig.mcpServers = @{}
}

$existingConfig.mcpServers["wechat-official-account"] = $mcpConfig

# 保存配置
Write-Host "`n保存配置到: $configPath" -ForegroundColor Yellow
$jsonConfig = $existingConfig | ConvertTo-Json -Depth 10

# 确保目录存在
New-Item -ItemType Directory -Force -Path $configDir | Out-Null

# 备份现有配置（如果存在）
if (Test-Path $configPath) {
    $backupPath = "$configPath.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item $configPath $backupPath
    Write-Host "✅ 已备份现有配置到: $backupPath" -ForegroundColor Green
}

# 保存新配置
$jsonConfig | Set-Content -Path $configPath -Encoding UTF8

Write-Host "`n✅ 配置已保存！" -ForegroundColor Green
Write-Host "`n配置内容:" -ForegroundColor Cyan
Write-Host $jsonConfig -ForegroundColor Gray

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "下一步操作:" -ForegroundColor Cyan
Write-Host "1. 重启 Claude Desktop" -ForegroundColor Yellow
Write-Host "2. 在对话中测试 MCP 工具" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

