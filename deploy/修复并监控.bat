@echo off
chcp 65001 >nul
echo ========================================
echo 修复构建并监控服务
echo ========================================
echo.

echo [步骤 1] 上传文件...
scp saas-demo/src/app/group-ai/accounts/page.tsx ubuntu@165.154.233.55:/home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx
if %errorlevel% neq 0 (
    echo [错误] 文件上传失败
    pause
    exit /b 1
)
echo [OK] 文件已上传
echo.

echo [步骤 2] 停止服务...
ssh ubuntu@165.154.233.55 "sudo systemctl stop liaotian-frontend"
timeout /t 2 /nobreak >nul
echo.

echo [步骤 3] 清理并重新构建...
echo 正在构建，请耐心等待...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && source \$HOME/.nvm/nvm.sh && nvm use 20 && rm -rf .next node_modules/.cache && npm run build 2>&1 | tail -30"
if %errorlevel% neq 0 (
    echo [错误] 构建失败，查看上面的错误信息
    pause
    exit /b 1
)
echo.

echo [步骤 4] 验证构建...
ssh ubuntu@165.154.233.55 "test -f /home/ubuntu/liaotian/saas-demo/.next/BUILD_ID && echo '构建成功' || echo '构建失败'"
echo.

echo [步骤 5] 重启服务...
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-frontend"
timeout /t 5 /nobreak >nul
echo.

echo [步骤 6] 检查服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-frontend --no-pager | head -20"
echo.

echo [步骤 7] 检查端口...
ssh ubuntu@165.154.233.55 "sudo netstat -tlnp 2>/dev/null | grep ':3000' || sudo ss -tlnp 2>/dev/null | grep ':3000' || echo '端口3000未监听'"
echo.

echo ========================================
echo 修复完成！
echo ========================================
echo.
echo 请清除浏览器缓存并刷新页面测试。
echo.
pause

