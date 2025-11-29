@echo off
chcp 65001 >nul
echo ========================================
echo 修复所有前端认证问题
echo ========================================
echo.

echo [步骤 1] 上传修复后的 nodes 页面...
scp saas-demo/src/app/group-ai/nodes/page.tsx ubuntu@165.154.233.55:/home/ubuntu/liaotian/saas-demo/src/app/group-ai/nodes/page.tsx
echo.

echo [步骤 2] 上传修复后的 groups 页面...
scp saas-demo/src/app/group-ai/groups/page.tsx ubuntu@165.154.233.55:/home/ubuntu/liaotian/saas-demo/src/app/group-ai/groups/page.tsx
echo.

echo [步骤 3] 上传修复后的后端文件...
scp admin-backend/app/api/workers.py ubuntu@165.154.233.55:/home/ubuntu/liaotian/admin-backend/app/api/workers.py
echo.

echo [步骤 4] 重启后端服务...
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-backend"
timeout /t 3 /nobreak >nul
echo.

echo [步骤 5] 重新构建前端（这可能需要几分钟）...
echo 正在构建前端，请稍候...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nvm use 20 && rm -rf .next && npm run build 2>&1 | tail -30"
echo.

echo [步骤 6] 重启前端服务...
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-frontend"
timeout /t 3 /nobreak >nul
echo.

echo [步骤 7] 检查服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-backend --no-pager | head -8"
echo.
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-frontend --no-pager | head -8"
echo.

echo ========================================
echo 修复完成！
echo ========================================
echo.
echo 重要提示：
echo 1. 清除浏览器缓存（Ctrl+Shift+Delete）
echo 2. 强制刷新页面（Ctrl+F5）
echo 3. 如果仍然显示 401，请重新登录
echo 4. 确保 computer_001 和 computer_002 已使用修复后的代码重启
echo.
pause

