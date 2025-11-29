@echo off
chcp 65001 >nul
echo ============================================================
echo 全自动修复 WebSocket 连接问题
echo ============================================================
echo.

cd /d "%~dp0\.."

echo [1/4] 上传修复脚本到服务器...
scp deploy\修复WebSocket-服务器直接执行.sh ubuntu@165.154.233.55:/tmp/修复WS.sh
if errorlevel 1 (
    echo [错误] 上传失败，请检查 SSH 连接
    echo.
    echo 提示：如果上传失败，可以直接在服务器上执行以下命令：
    echo.
    echo sudo bash /tmp/修复WS.sh
    pause
    exit /b 1
)

echo.
echo [2/4] 在服务器上执行修复...
ssh ubuntu@165.154.233.55 "chmod +x /tmp/修复WS.sh && sudo bash /tmp/修复WS.sh" > deploy\WebSocket修复结果.txt 2>&1

echo.
echo [3/4] 修复结果：
echo ============================================================
type deploy\WebSocket修复结果.txt

echo.
echo [4/4] 验证修复...
ssh ubuntu@165.154.233.55 "sudo grep -A 12 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc" > deploy\WebSocket配置验证.txt 2>&1

echo.
echo WebSocket 配置验证：
echo ============================================================
type deploy\WebSocket配置验证.txt

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
echo 如果仍有问题，请查看：
echo - deploy\WebSocket修复结果.txt
echo - deploy\WebSocket配置验证.txt
echo.
pause

