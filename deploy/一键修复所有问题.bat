@echo off
chcp 65001 >nul
echo ========================================
echo 一键修复所有问题
echo ========================================
echo.

echo [步骤 1/6] 上传前端修复文件...
scp saas-demo/src/app/group-ai/nodes/page.tsx ubuntu@165.154.233.55:/home/ubuntu/liaotian/saas-demo/src/app/group-ai/nodes/page.tsx
if %errorlevel% neq 0 (
    echo [错误] 上传前端文件失败
    pause
    exit /b 1
)
echo [OK] 前端文件上传成功
echo.

echo [步骤 2/6] 上传后端修复文件...
scp admin-backend/app/api/workers.py ubuntu@165.154.233.55:/home/ubuntu/liaotian/admin-backend/app/api/workers.py
if %errorlevel% neq 0 (
    echo [警告] 上传后端文件失败，继续...
)
echo.

echo [步骤 3/6] 重启后端服务...
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-backend"
timeout /t 5 /nobreak >nul
echo [OK] 后端服务已重启
echo.

echo [步骤 4/6] 检查后端是否收到心跳...
echo 正在检查 Workers API...
ssh ubuntu@165.154.233.55 "curl -s http://127.0.0.1:8000/api/v1/workers/ 2>&1 | python3 -m json.tool 2>&1 | head -20"
echo.

echo [步骤 5/6] 重新构建前端（这可能需要几分钟）...
echo 正在构建前端...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nvm use 20 && rm -rf .next && npm run build 2>&1 | tail -30"
if %errorlevel% neq 0 (
    echo [警告] 前端构建可能失败，请检查日志
)
echo.

echo [步骤 6/6] 重启前端服务...
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-frontend"
timeout /t 3 /nobreak >nul
echo [OK] 前端服务已重启
echo.

echo ========================================
echo 修复完成！
echo ========================================
echo.
echo 重要提示：
echo 1. 确保 computer_001 和 computer_002 已经使用修复后的代码重启
echo 2. 检查 Worker 节点日志，确认心跳发送成功
echo 3. 清除浏览器缓存（Ctrl+Shift+Delete）
echo 4. 强制刷新页面（Ctrl+F5）
echo 5. 如果仍然显示 401，请检查是否已登录
echo.
echo 如果问题仍然存在，请检查：
echo - Worker 节点是否已重启并使用修复后的代码
echo - Worker 节点日志中是否有心跳发送成功的消息
echo - 后端日志中是否收到心跳请求
echo.
pause
