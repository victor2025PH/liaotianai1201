@echo off
chcp 65001 >nul
echo ========================================
echo 最终修复 401 错误
echo ========================================
echo.

echo [步骤 1] 上传修复后的 deps.py（关键修复）...
scp admin-backend/app/api/deps.py ubuntu@165.154.233.55:/home/ubuntu/liaotian/admin-backend/app/api/deps.py
if %errorlevel% neq 0 (
    echo [错误] 上传 deps.py 失败
    pause
    exit /b 1
)
echo [OK] deps.py 上传成功
echo.

echo [步骤 2] 上传修复后的 workers.py...
scp admin-backend/app/api/workers.py ubuntu@165.154.233.55:/home/ubuntu/liaotian/admin-backend/app/api/workers.py
echo.

echo [步骤 3] 上传修复后的前端文件...
scp saas-demo/src/app/group-ai/nodes/page.tsx ubuntu@165.154.233.55:/home/ubuntu/liaotian/saas-demo/src/app/group-ai/nodes/page.tsx
scp saas-demo/src/app/group-ai/groups/page.tsx ubuntu@165.154.233.55:/home/ubuntu/liaotian/saas-demo/src/app/group-ai/groups/page.tsx
echo.

echo [步骤 4] 重启后端服务（重要！）...
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-backend"
timeout /t 5 /nobreak >nul
echo [OK] 后端服务已重启
echo.

echo [步骤 5] 验证修复（测试 Workers API）...
ssh ubuntu@165.154.233.55 "curl -s http://127.0.0.1:8000/api/v1/workers/ 2>&1 | head -5"
echo.

echo [步骤 6] 检查后端服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-backend --no-pager | head -10"
echo.

echo [步骤 7] 重新构建前端...
echo 正在构建前端，请稍候...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nvm use 20 && rm -rf .next && npm run build 2>&1 | tail -30"
echo.

echo [步骤 8] 重启前端服务...
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-frontend"
timeout /t 3 /nobreak >nul
echo.

echo ========================================
echo 修复完成！
echo ========================================
echo.
echo 关键修复：
echo - deps.py: 将 oauth2_scheme 的 auto_error 改为 False
echo - 这样即使没有 token，也能在函数内检查 disable_auth 设置
echo.
echo 下一步：
echo 1. 清除浏览器缓存（Ctrl+Shift+Delete）
echo 2. 强制刷新页面（Ctrl+F5）
echo 3. 如果仍然显示 401，请重新登录
echo 4. 检查浏览器控制台的 Network 标签，确认 Authorization header 已发送
echo.
pause

