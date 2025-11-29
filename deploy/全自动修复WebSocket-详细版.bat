@echo off
chcp 65001 >nul
title 全自动修复 WebSocket 连接
echo.
echo ============================================================
echo           全自动修复 WebSocket 连接问题
echo ============================================================
echo.

cd /d "%~dp0\.."

echo [步骤 1/5] 检查 SSH 连接...
ssh -o BatchMode=yes -o ConnectTimeout=5 ubuntu@165.154.233.55 "echo test" >nul 2>&1
if errorlevel 1 (
    echo [错误] SSH 密钥未配置，需要先配置 SSH 密钥
    echo.
    echo 请先运行：deploy\配置SSH密钥认证.bat
    echo.
    pause
    exit /b 1
)
echo [OK] SSH 连接正常

echo.
echo [步骤 2/5] 上传修复脚本到服务器...
scp deploy\修复WebSocket-服务器直接执行.sh ubuntu@165.154.233.55:/tmp/修复WS.sh
if errorlevel 1 (
    echo [错误] 上传失败
    echo 可能原因：SSH 需要密码，请先配置 SSH 密钥
    pause
    exit /b 1
)
echo [OK] 脚本已上传

echo.
echo [步骤 3/5] 在服务器上执行修复...
ssh ubuntu@165.154.233.55 "chmod +x /tmp/修复WS.sh && sudo bash /tmp/修复WS.sh"
if errorlevel 1 (
    echo [错误] 修复执行失败
    pause
    exit /b 1
)

echo.
echo [步骤 4/5] 验证修复结果...
ssh ubuntu@165.154.233.55 "sudo grep -A 12 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"

echo.
echo [步骤 5/5] 检查 Nginx 状态...
ssh ubuntu@165.154.233.55 "sudo systemctl status nginx --no-pager | head -5"

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

