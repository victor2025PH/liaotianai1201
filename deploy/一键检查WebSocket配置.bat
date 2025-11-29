@echo off
chcp 65001 >nul
echo ============================================================
echo 检查服务器 WebSocket 配置
echo ============================================================
echo.

cd /d "%~dp0\.."

echo [1] 上传检查脚本到服务器...
scp deploy\检查WebSocket配置.sh ubuntu@165.154.233.55:/tmp/检查WS.sh
if errorlevel 1 (
    echo [错误] 上传失败
    pause
    exit /b 1
)

echo.
echo [2] 在服务器上执行检查...
ssh ubuntu@165.154.233.55 "chmod +x /tmp/检查WS.sh && sudo bash /tmp/检查WS.sh" > deploy\WebSocket配置检查结果.txt 2>&1

echo.
echo [3] 检查结果：
echo ============================================================
type deploy\WebSocket配置检查结果.txt

echo.
echo ============================================================
echo 检查完成！
echo ============================================================
echo.
echo 如果配置不正确，请运行修复脚本：
echo - deploy\一键修复WebSocket连接.bat
echo.
pause

