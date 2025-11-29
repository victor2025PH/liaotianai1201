@echo off
chcp 65001 >nul
echo ========================================
echo 立即修复前端和检查心跳
echo ========================================
echo.

echo [步骤 1] 上传修复后的前端文件...
scp saas-demo/src/app/group-ai/nodes/page.tsx ubuntu@165.154.233.55:/home/ubuntu/liaotian/saas-demo/src/app/group-ai/nodes/page.tsx
if %errorlevel% neq 0 (
    echo [错误] 上传失败
    pause
    exit /b 1
)
echo [OK] 文件上传成功
echo.

echo [步骤 2] 上传修复后的后端文件...
scp admin-backend/app/api/workers.py ubuntu@165.154.233.55:/home/ubuntu/liaotian/admin-backend/app/api/workers.py
echo.

echo [步骤 3] 重启后端服务...
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-backend"
timeout /t 3 /nobreak >nul
echo.

echo [步骤 4] 检查后端是否收到心跳...
ssh ubuntu@165.154.233.55 "curl -s http://127.0.0.1:8000/api/v1/workers/ 2>&1 | python3 -m json.tool 2>&1 | head -50"
echo.

echo [步骤 5] 重新构建前端（这可能需要几分钟）...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nvm use 20 && npm run build 2>&1 | tail -30"
echo.

echo [步骤 6] 重启前端服务...
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-frontend"
timeout /t 3 /nobreak >nul
echo.

echo [步骤 7] 检查服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-backend --no-pager | head -10"
echo.
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-frontend --no-pager | head -10"
echo.

echo ========================================
echo 修复完成！
echo ========================================
echo.
echo 下一步：
echo 1. 清除浏览器缓存（Ctrl+Shift+Delete）
echo 2. 强制刷新页面（Ctrl+F5）
echo 3. 确认 computer_001 和 computer_002 已经重启并发送心跳
echo 4. 检查前端页面是否显示节点和账号
echo.
pause

