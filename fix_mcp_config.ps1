# 修复 MCP 配置的脚本
# 自动检测并修复常见配置问题

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MCP 配置修复工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$configPath = "$env:APPDATA\Claude\claude_desktop_config.json"

# 1. 检查 Python
Write-Host "`n1. 检查 Python 环境..." -ForegroundColor Yellow

$pythonCmds = @("python", "py", "python3")
$pythonPath = $null

foreach ($cmd in $pythonCmds) {
    try {
        $result = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($result) {
            $pythonPath = $result.Source
            Write-Host "   ✅ 找到 Python: $pythonPath" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonPath) {
    # 尝试 Windows Store Python
    $storePython = "$env:LOCALAPPDATA\Microsoft\WindowsApps\python.exe"
    if (Test-Path $storePython) {
        $pythonPath = $storePython
        Write-Host "   ✅ 找到 Windows Store Python: $pythonPath" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 未找到 Python，请先安装 Python" -ForegroundColor Red
        exit 1
    }
}

# 2. 检查依赖
Write-Host "`n2. 检查依赖..." -ForegroundColor Yellow

$depsOk = $true
try {
    $mcpCheck = & $pythonPath -c "import mcp; print('OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ MCP 已安装" -ForegroundColor Green
    } else {
        Write-Host "   ❌ MCP 未安装" -ForegroundColor Red
        $depsOk = $false
    }
} catch {
    Write-Host "   ❌ MCP 检查失败" -ForegroundColor Red
    $depsOk = $false
}

if (-not $depsOk) {
    Write-Host "`n正在安装依赖..." -ForegroundColor Yellow
    & $pythonPath -m pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ 依赖安装完成" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 依赖安装失败" -ForegroundColor Red
        exit 1
    }
}

# 3. 获取项目路径
Write-Host "`n3. 获取项目路径..." -ForegroundColor Yellow
$projectPath = (Get-Location).Path
$mainPyPath = Join-Path $projectPath "main.py"

if (-not (Test-Path $mainPyPath)) {
    Write-Host "   ❌ 未找到 main.py" -ForegroundColor Red
    exit 1
}

$mainPyPathEscaped = $mainPyPath -replace '\\', '\\'
Write-Host "   ✅ 项目路径: $mainPyPathEscaped" -ForegroundColor Green

# 4. 读取或创建配置
Write-Host "`n4. 更新配置文件..." -ForegroundColor Yellow

$existingConfig = @{}
if (Test-Path $configPath) {
    try {
        $content = Get-Content $configPath -Raw -Encoding UTF8
        $existingConfig = $content | ConvertFrom-Json -AsHashtable
        Write-Host "   ✅ 读取现有配置" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  配置文件格式有误，将创建新配置" -ForegroundColor Yellow
        $existingConfig = @{}
    }
} else {
    Write-Host "   ℹ️  配置文件不存在，将创建新文件" -ForegroundColor Yellow
}

# 5. 构建配置
if (-not $existingConfig.mcpServers) {
    $existingConfig.mcpServers = @{}
}

$mcpConfig = @{
    command = $pythonPath
    args = @($mainPyPathEscaped)
}

# 读取 .env 文件（如果存在）
if (Test-Path ".env") {
    $envVars = @{}
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim() -replace '^["'']|["'']$', ''
            if ($key -and $value) {
                $envVars[$key] = $value
            }
        }
    }
    
    if ($envVars.Count -gt 0) {
        $mcpConfig.env = @{}
        if ($envVars.WECHAT_APP_ID) { $mcpConfig.env.WECHAT_APP_ID = $envVars.WECHAT_APP_ID }
        if ($envVars.WECHAT_APP_SECRET) { $mcpConfig.env.WECHAT_APP_SECRET = $envVars.WECHAT_APP_SECRET }
        if ($envVars.WECHAT_TOKEN) { $mcpConfig.env.WECHAT_TOKEN = $envVars.WECHAT_TOKEN }
        if ($envVars.WECHAT_ENCODING_AES_KEY) { $mcpConfig.env.WECHAT_ENCODING_AES_KEY = $envVars.WECHAT_ENCODING_AES_KEY }
    }
}

$existingConfig.mcpServers["wechat-official-account"] = $mcpConfig

# 6. 保存配置
Write-Host "`n5. 保存配置..." -ForegroundColor Yellow

$configDir = Split-Path -Parent $configPath
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Force -Path $configDir | Out-Null
}

# 备份
if (Test-Path $configPath) {
    $backupPath = "$configPath.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item $configPath $backupPath
    Write-Host "   ✅ 已备份现有配置" -ForegroundColor Green
}

# 保存
try {
    $jsonConfig = $existingConfig | ConvertTo-Json -Depth 10
    $jsonConfig | Set-Content -Path $configPath -Encoding UTF8 -NoNewline
    Write-Host "   ✅ 配置已保存" -ForegroundColor Green
    
    Write-Host "`n配置内容:" -ForegroundColor Cyan
    Write-Host $jsonConfig -ForegroundColor Gray
    
} catch {
    Write-Host "   ❌ 保存失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ 配置修复完成！" -ForegroundColor Green
Write-Host "`n下一步:" -ForegroundColor Yellow
Write-Host "1. 重启 Claude Desktop" -ForegroundColor White
Write-Host "2. 测试 MCP 工具" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan

