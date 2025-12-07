# 验证并推送脚本
cd D:\telegram-ai-system
Write-Host "检查文件是否存在..." -ForegroundColor Yellow
if (Test-Path "deploy\fix_and_deploy_frontend_complete.sh") {
    Write-Host "文件存在" -ForegroundColor Green
    
    Write-Host "添加到Git..." -ForegroundColor Yellow
    git add deploy/fix_and_deploy_frontend_complete.sh
    
    Write-Host "提交..." -ForegroundColor Yellow
    git commit -m "Add fix_and_deploy_frontend_complete.sh deployment script"
    
    Write-Host "推送到GitHub..." -ForegroundColor Yellow
    git push origin main
    
    Write-Host "完成！" -ForegroundColor Green
} else {
    Write-Host "文件不存在！" -ForegroundColor Red
}
