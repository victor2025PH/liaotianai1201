@echo off
chcp 65001 >nul
echo ============================================================
echo 一键修复 WebSocket 连接问题
echo ============================================================
echo.

cd /d "%~dp0\.."

echo [1] 上传修复脚本到服务器...
scp deploy\修复WebSocket-服务器直接执行.sh ubuntu@165.154.233.55:/tmp/修复WS.sh
if errorlevel 1 (
    echo [错误] 上传失败，请检查 SSH 连接
    pause
    exit /b 1
)

echo.
echo [2] 在服务器上执行修复...
ssh ubuntu@165.154.233.55 "chmod +x /tmp/修复WS.sh && sudo bash /tmp/修复WS.sh"

echo.
echo ============================================================
echo 修复完成！
echo ============================================================
echo.
echo 下一步：
echo 1. 在浏览器中刷新页面（F5）
echo 2. 检查浏览器控制台，WebSocket 错误应该消失
echo 3. 如果仍有问题，检查后端日志
echo.
pause

