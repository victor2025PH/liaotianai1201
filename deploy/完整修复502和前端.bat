@echo off
chcp 65001 >nul
echo ========================================
echo 完整修复 502 错误和前端代码
echo ========================================
echo.

echo [步骤 1] 上传后端文件...
scp admin-backend/app/api/workers.py ubuntu@165.154.233.55:/home/ubuntu/liaotian/admin-backend/app/api/workers.py
scp admin-backend/app/api/__init__.py ubuntu@165.154.233.55:/home/ubuntu/liaotian/admin-backend/app/api/__init__.py
echo.

echo [步骤 2] 安装 websockets 库...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/admin-backend && source .venv/bin/activate && pip install 'uvicorn[standard]' 2>&1"
echo.

echo [步骤 3] 重启后端服务...
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-backend"
timeout /t 5 /nobreak >nul
echo.

echo [步骤 4] 上传前端修改的文件...
scp saas-demo/src/app/group-ai/nodes/page.tsx ubuntu@165.154.233.55:/home/ubuntu/liaotian/saas-demo/src/app/group-ai/nodes/page.tsx
scp saas-demo/src/app/group-ai/groups/page.tsx ubuntu@165.154.233.55:/home/ubuntu/liaotian/saas-demo/src/app/group-ai/groups/page.tsx
scp saas-demo/src/app/group-ai/group-automation/page.tsx ubuntu@165.154.233.55:/home/ubuntu/liaotian/saas-demo/src/app/group-ai/group-automation/page.tsx
echo.

echo [步骤 5] 重新构建前端（这可能需要几分钟）...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nvm use 20 && rm -rf .next && npm run build 2>&1 | tail -50"
echo.

echo [步骤 6] 重启前端服务...
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-frontend"
timeout /t 5 /nobreak >nul
echo.

echo [步骤 7] 检查服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-backend --no-pager | head -10"
echo.
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-frontend --no-pager | head -10"
echo.

echo [步骤 8] 测试 Workers API...
ssh ubuntu@165.154.233.55 "curl -s http://127.0.0.1:8000/api/v1/workers/ 2>&1 | head -20"
echo.

echo ========================================
echo 修复完成！
echo ========================================
echo.
echo 下一步：
echo 1. 清除浏览器缓存（Ctrl+Shift+Delete）
echo 2. 刷新页面（Ctrl+F5）
echo 3. 检查控制台是否还有错误
echo 4. 在 computer_001 和 computer_002 上运行 Worker 客户端
echo.
pause

