@echo off
chcp 65001 >nul
echo ========================================
echo 修复前端和 Worker 节点问题
echo ========================================
echo.

echo [步骤 1] 上传修复后的前端文件...
scp saas-demo/src/app/group-ai/nodes/page.tsx ubuntu@165.154.233.55:/home/ubuntu/liaotian/saas-demo/src/app/group-ai/nodes/page.tsx
echo.

echo [步骤 2] 重新构建前端...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nvm use 20 && npm run build 2>&1 | tail -30"
echo.

echo [步骤 3] 重启前端服务...
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-frontend"
timeout /t 3 /nobreak >nul
echo.

echo [步骤 4] 检查后端日志（查看是否有心跳请求）...
ssh ubuntu@165.154.233.55 "sudo journalctl -u liaotian-backend -n 50 --no-pager | grep -i 'worker\|heartbeat' | tail -20"
echo.

echo ========================================
echo 前端修复完成！
echo ========================================
echo.
echo 下一步（需要在 computer_001 和 computer_002 上执行）：
echo 1. 检查 Worker 节点配置中的主节点 URL
echo 2. 将 jblt.usdt2026.cc 改为 aikz.usdt2026.cc
echo 3. 重启 Worker 节点
echo 4. 检查日志确认心跳成功
echo.
echo 参考文档：deploy/修复Worker节点配置.md
echo.
pause

