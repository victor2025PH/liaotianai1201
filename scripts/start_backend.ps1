# 在 Cursor 终端中启动后端服务
# 直接在终端中运行，日志实时显示

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "admin-backend"

Write-Host "`n🚀 启动后端服务..." -ForegroundColor Cyan
Write-Host "   工作目录: $backendDir" -ForegroundColor Gray
Write-Host "   端口: 8000" -ForegroundColor Gray
Write-Host "   按 Ctrl+C 停止服务`n" -ForegroundColor Yellow

Set-Location $backendDir
$env:PYTHONUNBUFFERED = "1"

# 直接在终端中运行，日志实时显示
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
