@echo off
chcp 65001 >nul
echo ============================================================
echo 从本地 Windows 上传脚本到服务器并执行
echo ============================================================
echo.

cd /d "%~dp0\.."

echo [1] 上传修复脚本到服务器...
scp deploy\快速修复401-简单版.sh ubuntu@165.154.233.55:/tmp/修复401.sh
if errorlevel 1 (
    echo [错误] 上传失败，请检查 SSH 连接
    echo.
    echo [提示] 如果上传失败，可以直接在服务器上执行以下命令：
    echo.
    echo sudo mkdir -p /home/ubuntu/admin-backend
    echo echo "CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:8080,http://aikz.usdt2026.cc" ^| sudo tee /home/ubuntu/admin-backend/.env
    echo sudo systemctl restart liaotian-backend
    pause
    exit /b 1
)

echo.
echo [2] 在服务器上执行修复...
ssh ubuntu@165.154.233.55 "chmod +x /tmp/修复401.sh && sudo bash /tmp/修复401.sh"

echo.
echo ============================================================
echo 修复完成！
echo ============================================================
echo.
echo 下一步：
echo 1. 在浏览器中访问 http://aikz.usdt2026.cc/login 重新登录
echo 2. 登录后访问 http://aikz.usdt2026.cc/group-ai/accounts
echo 3. 检查浏览器控制台，确认 API 请求是否成功
echo.
pause

