@echo off
chcp 65001 >nul
echo ============================================================
echo 一键诊断和修复 401 认证问题
echo ============================================================
echo.

cd /d "%~dp0\.."

echo [1] 上传查找脚本到服务器...
scp deploy/查找后端配置和服务.sh ubuntu@165.154.233.55:/tmp/查找配置.sh
if errorlevel 1 (
    echo [错误] 上传失败，请检查 SSH 连接
    pause
    exit /b 1
)

echo.
echo [2] 在服务器上执行查找...
ssh ubuntu@165.154.233.55 "chmod +x /tmp/查找配置.sh && bash /tmp/查找配置.sh" > deploy/查找结果.txt 2>&1

echo.
echo [3] 查找结果：
echo ============================================================
type deploy/查找结果.txt

echo.
echo ============================================================
echo [4] 上传自动修复脚本...
scp deploy/修复401认证-自动查找路径.sh ubuntu@165.154.233.55:/tmp/修复401.sh
if errorlevel 1 (
    echo [错误] 上传失败
    pause
    exit /b 1
)

echo.
echo [5] 在服务器上执行修复...
echo [提示] 修复过程可能需要几秒钟...
ssh ubuntu@165.154.233.55 "chmod +x /tmp/修复401.sh && sudo bash /tmp/修复401.sh" > deploy/修复结果.txt 2>&1

echo.
echo [6] 修复结果：
echo ============================================================
type deploy/修复结果.txt

echo.
echo ============================================================
echo 诊断和修复完成！
echo ============================================================
echo.
echo 下一步：
echo 1. 查看上面的查找结果，确认配置路径和服务名
echo 2. 查看修复结果，确认是否成功
echo 3. 在浏览器中访问 http://aikz.usdt2026.cc/login 重新登录
echo 4. 登录后访问 http://aikz.usdt2026.cc/group-ai/accounts
echo 5. 检查浏览器控制台，确认 API 请求是否成功
echo.
echo 如果修复失败，请查看 deploy/查找结果.txt 和 deploy/修复结果.txt
echo.
pause

