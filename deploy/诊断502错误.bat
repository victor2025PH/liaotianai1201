@echo off
chcp 65001 >nul
echo ========================================
echo 诊断并修复 502 Bad Gateway 错误
echo ========================================
echo.

echo [1] 检查后端服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-backend --no-pager | head -20"
echo.

echo [2] 检查后端是否在运行...
ssh ubuntu@165.154.233.55 "sudo systemctl is-active liaotian-backend"
echo.

echo [3] 检查后端端口监听...
ssh ubuntu@165.154.233.55 "sudo ss -tlnp | grep :8000"
echo.

echo [4] 检查后端错误日志...
ssh ubuntu@165.154.233.55 "sudo journalctl -u liaotian-backend -n 50 --no-pager | grep -i 'error\|exception\|traceback' | tail -20"
echo.

echo [5] 检查 workers.py 文件...
ssh ubuntu@165.154.233.55 "test -f /home/ubuntu/liaotian/admin-backend/app/api/workers.py && echo '文件存在' || echo '文件不存在'"
echo.

echo [6] 测试 Workers API...
ssh ubuntu@165.154.233.55 "curl -s http://127.0.0.1:8000/api/v1/workers/ 2>&1 | head -20"
echo.

echo [7] 检查 Nginx 502 错误...
ssh ubuntu@165.154.233.55 "sudo tail -20 /var/log/nginx/error.log | grep -i '502\|upstream'"
echo.

echo [8] 检查 websockets 库...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/admin-backend && source .venv/bin/activate && pip list | grep -i websocket"
echo.

echo ========================================
echo 诊断完成
echo ========================================
echo.
pause

