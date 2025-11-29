@echo off
chcp 65001 >nul
echo ========================================
echo 修复路由 - 直接上传文件
echo ========================================
echo.

echo [步骤 1] 上传文件到服务器...
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
echo [OK] 服务已停止
echo.

echo [步骤 3] 清理构建缓存...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && rm -rf .next node_modules/.cache"
echo [OK] 已清理
echo.

echo [步骤 4] 重新构建（这可能需要几分钟）...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\"\$HOME/.nvm\" && [ -s \"\$NVM_DIR/nvm.sh\" ] && . \"\$NVM_DIR/nvm.sh\" && nvm use 20 && npm run build"
if %errorlevel% neq 0 (
    echo [警告] 构建可能有问题
) else (
    echo [OK] 构建成功
)
echo.

echo [步骤 5] 重启服务...
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-frontend"
echo [OK] 服务已重启
echo.

echo [步骤 6] 检查服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-frontend --no-pager | head -15"
echo.

echo ========================================
echo 完成！
echo ========================================
echo.
echo 请访问: http://aikz.usdt2026.cc/group-ai/accounts
echo.
pause

