# 重新构建前端并重启服务
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "重新构建前端并重启服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[步骤 1] 重新构建前端..." -ForegroundColor Yellow
Write-Host "正在构建，请稍候..." -ForegroundColor Gray
$buildCmd = @"
cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR="\$HOME/.nvm" && [ -s "\$NVM_DIR/nvm.sh" ] && . "\$NVM_DIR/nvm.sh" && nvm use 20 && rm -rf .next && npm run build 2>&1 | tail -40
"@
ssh ubuntu@165.154.233.55 $buildCmd
Write-Host ""

Write-Host "[步骤 2] 重启前端服务..." -ForegroundColor Yellow
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-frontend"
Start-Sleep -Seconds 3
Write-Host "[OK] 服务已重启" -ForegroundColor Green
Write-Host ""

Write-Host "[步骤 3] 检查服务状态..." -ForegroundColor Yellow
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-frontend --no-pager | head -20"
Write-Host ""

Write-Host "[步骤 4] 检查端口监听..." -ForegroundColor Yellow
ssh ubuntu@165.154.233.55 "sudo netstat -tlnp 2>/dev/null | grep ':3000' || sudo ss -tlnp 2>/dev/null | grep ':3000' || echo '端口3000未监听'"
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "如果服务正常运行，请：" -ForegroundColor Yellow
Write-Host "1. 清除浏览器缓存（Ctrl+Shift+Delete）" -ForegroundColor White
Write-Host "2. 强制刷新页面（Ctrl+F5）" -ForegroundColor White
Write-Host ""

