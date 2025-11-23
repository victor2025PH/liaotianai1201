# 交互式配置 Telegram API 凭证
param(
    [string]$ApiId = "",
    [string]$ApiHash = "",
    [string]$SessionName = "",
    [string]$OpenaiKey = ""
)

$ErrorActionPreference = "Continue"

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  Telegram API 凭证配置工具" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否已有 .env 文件
$envFile = ".env"
$envExists = Test-Path $envFile

if ($envExists) {
    Write-Host "发现现有 .env 文件，将更新配置" -ForegroundColor Yellow
    $existingContent = Get-Content $envFile -Raw
} else {
    Write-Host "将创建新的 .env 文件" -ForegroundColor Yellow
    $existingContent = ""
}

# 读取现有配置
if ($existingContent) {
    if ($existingContent -match "TELEGRAM_API_ID\s*=\s*([^\r\n]+)") {
        $currentApiId = $matches[1].Trim()
    }
    if ($existingContent -match "TELEGRAM_API_HASH\s*=\s*([^\r\n]+)") {
        $currentApiHash = $matches[1].Trim()
    }
    if ($existingContent -match "TELEGRAM_SESSION_NAME\s*=\s*([^\r\n]+)") {
        $currentSessionName = $matches[1].Trim()
    }
    if ($existingContent -match "OPENAI_API_KEY\s*=\s*([^\r\n]+)") {
        $currentOpenaiKey = $matches[1].Trim()
    }
}

# 交互式输入（如果没有通过参数提供）
if (-not $ApiId) {
    if ($currentApiId -and $currentApiId -ne "123456" -and $currentApiId -ne "your_api_id") {
        Write-Host "当前 TELEGRAM_API_ID: $currentApiId" -ForegroundColor Gray
        $useCurrent = Read-Host "使用当前值? (Y/n)"
        if ($useCurrent -eq "" -or $useCurrent -eq "Y" -or $useCurrent -eq "y") {
            $ApiId = $currentApiId
        }
    }
    if (-not $ApiId) {
        Write-Host "`n请输入 Telegram API ID (从 https://my.telegram.org 获取):" -ForegroundColor Yellow
        $ApiId = Read-Host "TELEGRAM_API_ID"
    }
}

if (-not $ApiHash) {
    if ($currentApiHash -and $currentApiHash -ne "your_telegram_api_hash") {
        Write-Host "当前 TELEGRAM_API_HASH: $($currentApiHash.Substring(0, [Math]::Min(20, $currentApiHash.Length)))..." -ForegroundColor Gray
        $useCurrent = Read-Host "使用当前值? (Y/n)"
        if ($useCurrent -eq "" -or $useCurrent -eq "Y" -or $useCurrent -eq "y") {
            $ApiHash = $currentApiHash
        }
    }
    if (-not $ApiHash) {
        Write-Host "`n请输入 Telegram API Hash (从 https://my.telegram.org 获取):" -ForegroundColor Yellow
        $ApiHash = Read-Host "TELEGRAM_API_HASH"
    }
}

if (-not $SessionName) {
    if ($currentSessionName -and $currentSessionName -ne "your_session_name") {
        Write-Host "当前 TELEGRAM_SESSION_NAME: $currentSessionName" -ForegroundColor Gray
        $useCurrent = Read-Host "使用当前值? (Y/n)"
        if ($useCurrent -eq "" -or $useCurrent -eq "Y" -or $useCurrent -eq "y") {
            $SessionName = $currentSessionName
        }
    }
    if (-not $SessionName) {
        Write-Host "`n请输入 Session 名称 (例如: my_bot):" -ForegroundColor Yellow
        $SessionName = Read-Host "TELEGRAM_SESSION_NAME"
    }
}

if (-not $OpenaiKey) {
    if ($currentOpenaiKey -and $currentOpenaiKey -ne "your_openai_api_key") {
        Write-Host "当前 OPENAI_API_KEY: $($currentOpenaiKey.Substring(0, [Math]::Min(20, $currentOpenaiKey.Length)))..." -ForegroundColor Gray
        $useCurrent = Read-Host "使用当前值? (Y/n)"
        if ($useCurrent -eq "" -or $useCurrent -eq "Y" -or $useCurrent -eq "y") {
            $OpenaiKey = $currentOpenaiKey
        }
    }
    if (-not $OpenaiKey) {
        Write-Host "`n请输入 OpenAI API Key (可选，从 https://platform.openai.com/api-keys 获取):" -ForegroundColor Yellow
        $OpenaiKey = Read-Host "OPENAI_API_KEY (直接回车跳过)"
    }
}

# 验证输入
if (-not $ApiId -or $ApiId -eq "") {
    Write-Host "`n✗ TELEGRAM_API_ID 不能为空" -ForegroundColor Red
    exit 1
}

if (-not ($ApiId -match "^\d+$")) {
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

# 读取模板文件
$templateFile = "docs/env.example"
if (Test-Path $templateFile) {
    $templateContent = Get-Content $templateFile -Raw
} else {
    Write-Host "`n⚠ 未找到模板文件，将创建基本配置" -ForegroundColor Yellow
    $templateContent = ""
}

# 更新配置
if ($templateContent) {
    $newContent = $templateContent
    
    # 替换 Telegram API 配置
    $newContent = $newContent -replace "TELEGRAM_API_ID=.*", "TELEGRAM_API_ID=$ApiId"
    $newContent = $newContent -replace "TELEGRAM_API_HASH=.*", "TELEGRAM_API_HASH=$ApiHash"
    $newContent = $newContent -replace "TELEGRAM_SESSION_NAME=.*", "TELEGRAM_SESSION_NAME=$SessionName"
    
    if ($OpenaiKey) {
        $newContent = $newContent -replace "OPENAI_API_KEY=.*", "OPENAI_API_KEY=$OpenaiKey"
    }
} else {
    # 创建基本配置
    $newContent = @"
# Telegram API 配置
TELEGRAM_API_ID=$ApiId
TELEGRAM_API_HASH=$ApiHash
TELEGRAM_SESSION_NAME=$SessionName
"@
    if ($OpenaiKey) {
        $newContent += "`nOPENAI_API_KEY=$OpenaiKey`n"
    }
}

# 保存到 .env 文件
Write-Host "`n保存配置到 .env 文件..." -ForegroundColor Yellow
$newContent | Out-File -FilePath $envFile -Encoding UTF8 -NoNewline

Write-Host "✓ 配置已保存到 .env 文件" -ForegroundColor Green
Write-Host ""
Write-Host "下一步:" -ForegroundColor Cyan
Write-Host "  1. 运行脚本同步到远程服务器:" -ForegroundColor Yellow
Write-Host "     pwsh -ExecutionPolicy Bypass -File scripts\sync_env_to_remote.ps1" -ForegroundColor Gray
Write-Host "  2. 启动远程服务器的 main.py:" -ForegroundColor Yellow
Write-Host "     pwsh -ExecutionPolicy Bypass -File scripts\fix_and_start_remote_main.ps1 -StartMain" -ForegroundColor Gray

