@echo off
chcp 65001 >nul
echo ========================================
echo 快速验证部署状态
echo ========================================
echo.

echo [步骤 1] 检查文件是否存在...
ssh ubuntu@165.154.233.55 "test -f /home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx && echo '文件存在' || echo '文件不存在'"
echo.

echo [步骤 2] 检查构建目录...
ssh ubuntu@165.154.233.55 "test -d /home/ubuntu/liaotian/saas-demo/.next && echo '构建目录存在' || echo '构建目录不存在'"
echo.

echo [步骤 3] 检查前端服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl is-active liaotian-frontend"
echo.

echo [步骤 4] 检查后端服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl is-active liaotian-backend"
echo.

echo [步骤 5] 检查端口监听...
ssh ubuntu@165.154.233.55 "sudo netstat -tlnp 2>/dev/null | grep ':3000' || sudo ss -tlnp 2>/dev/null | grep ':3000' || echo '端口3000未监听'"
echo.

echo [步骤 6] 查看前端服务日志（最后20行）...
ssh ubuntu@165.154.233.55 "sudo journalctl -u liaotian-frontend -n 20 --no-pager"
echo.

echo ========================================
echo 验证完成
echo ========================================
pause

