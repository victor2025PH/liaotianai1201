@echo off
chcp 65001 >nul
echo ============================================================
echo 快速修复 401 认证问题
echo ============================================================
echo.
echo 此脚本将：
echo 1. 上传修复脚本到服务器
echo 2. 在服务器上执行修复
echo 3. 显示修复结果
echo.
pause

cd /d "%~dp0\.."

echo.
echo [1] 上传修复脚本到服务器...
scp deploy\修复401认证问题-服务器执行.sh ubuntu@10.56.130.4:/tmp/修复401认证.sh
if errorlevel 1 (
    echo [错误] 上传失败，请检查 SSH 连接
    pause
    exit /b 1
)

echo.
echo [2] 在服务器上执行修复...
ssh ubuntu@10.56.130.4 "chmod +x /tmp/修复401认证.sh && sudo bash /tmp/修复401认证.sh"

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

