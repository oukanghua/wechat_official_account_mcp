# GitHub 推送脚本
# 使用方法：在 PowerShell 中执行此脚本，并输入你的 GitHub 仓库地址

Write-Host "=== GitHub 推送脚本 ===" -ForegroundColor Green
Write-Host ""

# 检查是否有远程仓库
$remote = git remote get-url origin 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "当前远程仓库: $remote" -ForegroundColor Yellow
    $useExisting = Read-Host "是否使用现有远程仓库？(y/n)"
    if ($useExisting -eq "y" -or $useExisting -eq "Y") {
        Write-Host "使用现有远程仓库..." -ForegroundColor Green
        git push -u origin main
        exit 0
    }
}

# 获取仓库地址
Write-Host "请输入你的 GitHub 仓库地址：" -ForegroundColor Cyan
Write-Host "示例: https://github.com/your-username/wechat_official_account_mcp.git" -ForegroundColor Gray
Write-Host "或: git@github.com:your-username/wechat_official_account_mcp.git" -ForegroundColor Gray
$repoUrl = Read-Host "仓库地址"

if ([string]::IsNullOrWhiteSpace($repoUrl)) {
    Write-Host "错误: 仓库地址不能为空" -ForegroundColor Red
    exit 1
}

# 添加远程仓库
Write-Host ""
Write-Host "添加远程仓库..." -ForegroundColor Yellow
git remote add origin $repoUrl 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    # 如果已存在，尝试更新
    Write-Host "远程仓库已存在，尝试更新..." -ForegroundColor Yellow
    git remote set-url origin $repoUrl
}

# 验证远程仓库
Write-Host "验证远程仓库..." -ForegroundColor Yellow
git remote -v

# 推送代码
Write-Host ""
Write-Host "推送代码到 GitHub..." -ForegroundColor Yellow
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ 代码已成功推送到 GitHub！" -ForegroundColor Green
    Write-Host "仓库地址: $repoUrl" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "✗ 推送失败，请检查：" -ForegroundColor Red
    Write-Host "1. 仓库地址是否正确" -ForegroundColor Yellow
    Write-Host "2. 是否已登录 GitHub（使用 HTTPS 需要 token，使用 SSH 需要配置 key）" -ForegroundColor Yellow
    Write-Host "3. 仓库是否已创建" -ForegroundColor Yellow
}

