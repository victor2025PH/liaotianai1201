@echo off
chcp 65001 >nul
title SSH 连接测试
echo.
echo ============================================================
echo            SSH 连接测试
echo ============================================================
echo.

cd /d "%~dp0\.."

echo [测试 1] 基本连接测试...
ssh ubuntu@165.154.233.55 "echo 'SSH 连接测试成功 - TEST123'"
echo.

echo [测试 2] 系统信息...
ssh ubuntu@165.154.233.55 "whoami && hostname && pwd"
echo.

echo [测试 3] Nginx 配置语法检查...
ssh ubuntu@165.154.233.55 "sudo nginx -t"
echo.

echo [测试 4] WebSocket 配置检查...
ssh ubuntu@165.154.233.55 "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
echo.

echo [测试 5] 服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl is-active nginx"
ssh ubuntu@165.154.233.55 "sudo systemctl is-active liaotian-backend"
echo.

echo ============================================================
echo 测试完成
echo ============================================================
pause

