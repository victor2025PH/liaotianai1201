@echo off
chcp 65001 >nul
title 全自动修复 WebSocket 连接
echo.
echo ============================================================
echo           全自动修复 WebSocket 连接问题
echo ============================================================
echo.
echo 正在执行修复，请稍候...
echo 注意：可能需要输入 SSH 密码
echo.

cd /d "%~dp0\.."

echo [1] 上传修复脚本...
scp -q deploy\修复WebSocket-服务器直接执行.sh ubuntu@165.154.233.55:/tmp/修复WS.sh 2>nul
if errorlevel 1 (
    echo [错误] 上传失败
    echo.
    echo 请手动在服务器上执行以下命令：
    echo.
    echo sudo bash /tmp/修复WS.sh
    echo.
    pause
    exit /b 1
)

echo [2] 执行修复...
ssh ubuntu@165.154.233.55 "chmod +x /tmp/修复WS.sh && sudo bash /tmp/修复WS.sh"

echo.
echo [3] 验证配置...
ssh ubuntu@165.154.233.55 "sudo grep -A 5 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc | head -10"

echo.
echo ============================================================
echo 修复完成！
echo ============================================================
echo.
echo 下一步：
echo 1. 在浏览器中刷新页面（按 F5）
echo 2. 打开开发者工具（F12）→ Console
echo 3. 检查 WebSocket 错误是否消失
echo.
pause

