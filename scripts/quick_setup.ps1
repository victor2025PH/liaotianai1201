# 快速设置脚本 - 配置 Telegram API 并同步到远程服务器
param(
    [string]$ApiId = "",
    [string]$ApiHash = "",
    [string]$SessionName = "",
    [string]$OpenaiKey = ""
)

$ErrorActionPreference = "Continue"

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  快速设置 - 配置 Telegram API 并部署" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 步骤 1: 检查或创建 .env 文件
Write-Host "[1/4] 检查本地 .env 文件..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  ✓ .env 文件已存在" -ForegroundColor Green
    $envContent = Get-Content ".env" -Raw
    $hasApiId = $envContent -match "TELEGRAM_API_ID\s*=\s*(\d+)" -and $matches[1] -ne "123456"
    $hasApiHash = $envContent -match "TELEGRAM_API_HASH\s*=\s*([^\r\n]+)" -and $matches[1] -notmatch "your_telegram_api_hash"
    $hasSessionName = $envContent -match "TELEGRAM_SESSION_NAME\s*=\s*([^\r\n]+)" -and $matches[1] -notmatch "your_session_name"
    
    if ($hasApiId -and $hasApiHash -and $hasSessionName) {
        Write-Host "  ✓ Telegram API 配置完整" -ForegroundColor Green
        $skipConfig = $true
    } else {
        Write-Host "  ⚠ Telegram API 配置不完整" -ForegroundColor Yellow
        $skipConfig = $false
    }
} else {
    Write-Host "  ✗ .env 文件不存在" -ForegroundColor Red
    $skipConfig = $false
}

# 步骤 2: 配置 Telegram API（如果需要）
if (-not $skipConfig) {
    Write-Host "`n[2/4] 配置 Telegram API 凭证..." -ForegroundColor Yellow
    
    if (-not $ApiId) {
        Write-Host "`n请输入 Telegram API ID (从 https://my.telegram.org 获取):" -ForegroundColor Cyan
        $ApiId = Read-Host "TELEGRAM_API_ID"
    }
    
    if (-not $ApiHash) {
        Write-Host "`n请输入 Telegram API Hash:" -ForegroundColor Cyan
        $ApiHash = Read-Host "TELEGRAM_API_HASH"
    }
    
    if (-not $SessionName) {
        Write-Host "`n请输入 Session 名称 (例如: my_bot):" -ForegroundColor Cyan
        $SessionName = Read-Host "TELEGRAM_SESSION_NAME"
    }
    
    if (-not $OpenaiKey) {
        Write-Host "`n请输入 OpenAI API Key (可选，直接回车跳过):" -ForegroundColor Cyan
        $OpenaiKey = Read-Host "OPENAI_API_KEY"
    }
    
    # 验证输入
    if (-not $ApiId -or -not ($ApiId -match "^\d+$")) {
        Write-Host "`n✗ TELEGRAM_API_ID 必须是数字" -ForegroundColor Red
        exit 1
    }
    
    if (-not $ApiHash -or $ApiHash -eq "") {
        Write-Host "`n✗ TELEGRAM_API_HASH 不能为空" -ForegroundColor Red
        exit 1
    }
    
    if (-not $SessionName -or $SessionName -eq "") {
        Write-Host "`n✗ TELEGRAM_SESSION_NAME 不能为空" -ForegroundColor Red
        exit 1
    }
    
    # 创建或更新 .env 文件
    Write-Host "`n保存配置到 .env 文件..." -ForegroundColor Yellow
    $templateFile = "docs/env.example"
    if (Test-Path $templateFile) {
        $templateContent = Get-Content $templateFile -Raw
        $newContent = $templateContent
        $newContent = $newContent -replace "TELEGRAM_API_ID=.*", "TELEGRAM_API_ID=$ApiId"
        $newContent = $newContent -replace "TELEGRAM_API_HASH=.*", "TELEGRAM_API_HASH=$ApiHash"
        $newContent = $newContent -replace "TELEGRAM_SESSION_NAME=.*", "TELEGRAM_SESSION_NAME=$SessionName"
        if ($OpenaiKey) {
            $newContent = $newContent -replace "OPENAI_API_KEY=.*", "OPENAI_API_KEY=$OpenaiKey"
        }
        $newContent | Out-File -FilePath ".env" -Encoding UTF8 -NoNewline
    } else {
        # 创建基本配置
        $newContent = @"
TELEGRAM_API_ID=$ApiId
TELEGRAM_API_HASH=$ApiHash
TELEGRAM_SESSION_NAME=$SessionName
"@
        if ($OpenaiKey) {
            $newContent += "OPENAI_API_KEY=$OpenaiKey`n"
        }
        $newContent | Out-File -FilePath ".env" -Encoding UTF8 -NoNewline
    }
    Write-Host "  ✓ .env 文件已创建/更新" -ForegroundColor Green
}

# 步骤 3: 同步到远程服务器
Write-Host "`n[3/4] 同步配置到远程服务器..." -ForegroundColor Yellow
pwsh -ExecutionPolicy Bypass -File "scripts\sync_env_to_remote.ps1"
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 配置已同步" -ForegroundColor Green
} else {
    Write-Host "  ✗ 同步失败" -ForegroundColor Red
    exit 1
}

# 步骤 4: 启动远程服务器的 main.py
Write-Host "`n[4/4] 启动远程服务器的 main.py..." -ForegroundColor Yellow
pwsh -ExecutionPolicy Bypass -File "scripts\fix_and_start_remote_main.ps1" -StartMain

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  快速设置完成" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步: 测试自动回复功能" -ForegroundColor Yellow
Write-Host "  pwsh -ExecutionPolicy Bypass -File scripts\test_remote_sessions.ps1 -Detailed" -ForegroundColor Gray

