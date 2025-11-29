@echo off
chcp 65001 >nul
title SSH 快速测试
echo.
echo ============================================================
echo            SSH 连接快速测试
echo ============================================================
echo.

echo [测试 1] 基本连接...
ssh ubuntu@165.154.233.55 "echo 'SSH 连接测试成功 - TEST123'"
if errorlevel 1 (
    echo [错误] 连接失败
) else (
    echo [成功] 连接正常
)
echo.

echo [测试 2] 系统信息...
ssh ubuntu@165.154.233.55 "whoami"
ssh ubuntu@165.154.233.55 "hostname"
echo.

echo [测试 3] Nginx 配置...
ssh ubuntu@165.154.233.55 "sudo nginx -t"
echo.

echo [测试 4] WebSocket 配置...
ssh ubuntu@165.154.233.55 "sudo grep -A 10 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
echo.

echo [测试 5] 服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl is-active nginx"
ssh ubuntu@165.154.233.55 "sudo systemctl is-active liaotian-backend"
echo.

echo ============================================================
echo 测试完成
echo ============================================================
pause

