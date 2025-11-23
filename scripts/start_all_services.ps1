# 启动所有服务脚本
Write-Host "🚀 启动所有服务..." -ForegroundColor Cyan

$projectRoot = "E:\002-工作文件\重要程序\聊天AI群聊程序"

# 启动后端服务（新窗口）
Write-Host "`n📡 启动后端服务..." -ForegroundColor Yellow
$backendScript = Join-Path $projectRoot "scripts\start_backend.ps1"
Start-Process powershell -ArgumentList "-NoExit", "-File", $backendScript

Start-Sleep -Seconds 3

# 启动前端服务（新窗口）
Write-Host "🌐 启动前端服务..." -ForegroundColor Yellow
$frontendScript = Join-Path $projectRoot "scripts\start_frontend.ps1"
Start-Process powershell -ArgumentList "-NoExit", "-File", $frontendScript

Write-Host "`n✅ 服务启动中..." -ForegroundColor Green
Write-Host "   后端: http://localhost:8000" -ForegroundColor Gray
Write-Host "   前端: http://localhost:3000" -ForegroundColor Gray
Write-Host "`n   等待服务启动后，在浏览器中打开 http://localhost:3000" -ForegroundColor Yellow
