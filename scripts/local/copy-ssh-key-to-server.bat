@echo off
chcp 65001 >nul
REM ============================================================
REM 将 SSH 公钥复制到服务器（一键配置免密登录）
REM ============================================================

set KEY_FILE=scripts\local\keys\server_key.pub
set SERVER_HOST=165.154.235.170
set SERVER_USER=ubuntu
set SERVER_PASSWORD=8iDcGrYb52Fxpzee

echo ============================================================
echo 📤 将 SSH 公钥复制到服务器
echo ============================================================
echo.

if not exist "%KEY_FILE%" (
    echo ❌ 公钥文件不存在: %KEY_FILE%
    echo.
    echo 请先运行: scripts\local\setup-ssh-key.bat
    pause
    exit /b 1
)

echo 服务器: %SERVER_USER%@%SERVER_HOST%
echo 公钥文件: %KEY_FILE%
echo.

REM 读取公钥内容
set PUB_KEY=
for /f "usebackq delims=" %%a in ("%KEY_FILE%") do set PUB_KEY=%%a

echo 正在复制公钥到服务器...
echo 注意：首次连接需要输入密码
echo 密码: %SERVER_PASSWORD%
echo.

REM 使用 ssh 命令复制公钥（Windows 10+ OpenSSH）
type "%KEY_FILE%" | ssh %SERVER_USER%@%SERVER_HOST% "mkdir -p ~/.ssh 2>nul && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

if errorlevel 1 (
    echo.
    echo ❌ 公钥复制失败
    echo.
    echo 请手动执行以下命令：
    echo   type "%KEY_FILE%" ^| ssh %SERVER_USER%@%SERVER_HOST% "mkdir -p ~/.ssh ^&^& chmod 700 ~/.ssh ^&^& cat ^>^> ~/.ssh/authorized_keys ^&^& chmod 600 ~/.ssh/authorized_keys"
    echo.
    echo 输入密码: %SERVER_PASSWORD%
    pause
    exit /b 1
)

echo.
echo ============================================================
echo ✅ 公钥已成功复制到服务器
echo ============================================================
echo.
echo 现在可以使用 ssh-server.bat 免密登录了
echo.
pause

