@echo off
chcp 65001 >nul
echo ========================================
echo 检查并修复前端服务
echo ========================================
echo.

echo [步骤 1] 检查服务配置文件...
ssh ubuntu@165.154.233.55 "cat /etc/systemd/system/liaotian-frontend.service"
echo.

echo [步骤 2] 检查构建目录...
ssh ubuntu@165.154.233.55 "test -d /home/ubuntu/liaotian/saas-demo/.next && echo '构建目录存在' || echo '构建目录不存在 - 需要重新构建'"
echo.

echo [步骤 3] 检查package.json中的start脚本...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && cat package.json | grep -A 3 '\"start\"'"
echo.

echo [步骤 4] 查看详细的服务日志...
ssh ubuntu@165.154.233.55 "sudo journalctl -u liaotian-frontend -n 50 --no-pager | tail -40"
echo.

echo [步骤 5] 尝试手动执行npm start查看错误...
echo 注意：这会启动一个进程，需要手动停止
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\"\$HOME/.nvm\" && [ -s \"\$NVM_DIR/nvm.sh\" ] && . \"\$NVM_DIR/nvm.sh\" && nvm use 20 && timeout 10 npm start 2>&1 || echo '命令执行完成或超时'"
echo.

echo ========================================
echo 检查完成
echo ========================================
pause

