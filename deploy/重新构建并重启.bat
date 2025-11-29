@echo off
chcp 65001 >nul
echo ========================================
echo 重新构建前端并重启服务
echo ========================================
echo.

echo [步骤 1] 重新构建前端...
echo 正在构建，请稍候...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\"\$HOME/.nvm\" && [ -s \"\$NVM_DIR/nvm.sh\" ] && . \"\$NVM_DIR/nvm.sh\" && nvm use 20 && rm -rf .next && npm run build 2>&1 | tail -40"
if %errorlevel% neq 0 (
    echo [警告] 构建可能有问题，请检查输出
) else (
    echo [OK] 构建完成
)
echo.

echo [步骤 2] 重启前端服务...
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-frontend"
timeout /t 3 /nobreak >nul
echo [OK] 服务已重启
echo.

echo [步骤 3] 检查服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-frontend --no-pager | head -20"
echo.

echo [步骤 4] 检查端口监听...
ssh ubuntu@165.154.233.55 "sudo netstat -tlnp 2>/dev/null | grep ':3000' || sudo ss -tlnp 2>/dev/null | grep ':3000' || echo '端口3000未监听'"
echo.

echo ========================================
echo 完成！
echo ========================================
echo.
echo 如果服务正常运行，请：
echo 1. 清除浏览器缓存（Ctrl+Shift+Delete）
echo 2. 强制刷新页面（Ctrl+F5）
echo.
pause

