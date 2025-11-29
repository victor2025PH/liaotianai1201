@echo off
chcp 65001 >nul
echo ========================================
echo 修复前端服务配置
echo ========================================
echo.

echo [步骤 1] 检查当前服务配置...
ssh ubuntu@165.154.233.55 "cat /etc/systemd/system/liaotian-frontend.service"
echo.

echo [步骤 2] 检查构建是否成功...
ssh ubuntu@165.154.233.55 "test -f /home/ubuntu/liaotian/saas-demo/.next/BUILD_ID && echo '构建成功' || echo '构建失败或未构建'"
echo.

echo [步骤 3] 如果构建失败，重新构建...
ssh ubuntu@165.154.233.55 "bash -c 'cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\"\$HOME/.nvm\" && [ -s \"\$NVM_DIR/nvm.sh\" ] && . \"\$NVM_DIR/nvm.sh\" && nvm use 20 && rm -rf .next && npm run build 2>&1 | tail -20'"
echo.

echo [步骤 4] 检查服务配置是否正确...
echo 如果服务配置使用 npm start，但构建失败，服务将无法启动
echo 需要确保：
echo 1. 构建成功（.next目录存在）
echo 2. 服务配置正确（使用next start而不是npm run dev）
echo.

echo [步骤 5] 重启服务...
ssh ubuntu@165.154.233.55 "sudo systemctl daemon-reload && sudo systemctl restart liaotian-frontend"
timeout /t 5 /nobreak >nul
echo.

echo [步骤 6] 检查服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-frontend --no-pager | head -20"
echo.

echo ========================================
echo 修复完成
echo ========================================
pause

