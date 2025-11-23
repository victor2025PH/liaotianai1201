# 在 Cursor 终端中启动前端服务
# 直接在终端中运行，日志实时显示

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $projectRoot "saas-demo"

Write-Host "`n🚀 启动前端服务..." -ForegroundColor Cyan
Write-Host "   工作目录: $frontendDir" -ForegroundColor Gray
Write-Host "   端口: 3001 (根据 package.json 配置)" -ForegroundColor Gray
Write-Host "   按 Ctrl+C 停止服务`n" -ForegroundColor Yellow

Set-Location $frontendDir
$env:NODE_ENV = "development"

# 直接在终端中运行，日志实时显示
npm run dev
