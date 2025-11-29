@echo off
chcp 65001 >nul
echo ========================================
echo 部署角色选择功能
echo ========================================
echo.

echo [1] 上传修改后的文件到服务器...
scp saas-demo/src/app/group-ai/accounts/page.tsx ubuntu@165.154.233.55:/tmp/accounts_page.tsx
if %errorlevel% neq 0 (
    echo 上传失败！
    pause
    exit /b 1
)

echo.
echo [2] 在服务器上替换文件并重新构建...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && sudo systemctl stop liaotian-frontend && cp /tmp/accounts_page.tsx src/app/group-ai/accounts/page.tsx && export NVM_DIR=\"\$HOME/.nvm\" && [ -s \"\$NVM_DIR/nvm.sh\" ] && . \"\$NVM_DIR/nvm.sh\" && nvm use 20 && npm run build && sudo systemctl start liaotian-frontend && sleep 5 && sudo systemctl status liaotian-frontend --no-pager | head -15"

if %errorlevel% neq 0 (
    echo 部署失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo 部署完成！
echo ========================================
echo.
echo 请访问 http://aikz.usdt2026.cc/group-ai/accounts 测试功能
echo.
pause

