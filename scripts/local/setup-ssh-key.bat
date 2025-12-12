@echo off
chcp 65001 >nul
REM ============================================================
REM 配置 SSH 免密登录到服务器
REM ============================================================

echo ============================================================
echo 🔑 配置 SSH 免密登录
echo ============================================================
echo.

set KEY_DIR=scripts\local\keys
set KEY_FILE=%KEY_DIR%\server_key
set PUB_KEY_FILE=%KEY_DIR%\server_key.pub
set SERVER_HOST=165.154.235.170
set SERVER_USER=ubuntu
set SERVER_PASSWORD=8iDcGrYb52Fxpzee

REM 检查密钥文件是否存在
if not exist "%KEY_FILE%" (
    echo ❌ 密钥文件不存在: %KEY_FILE%
    echo.
    echo 正在生成新的 SSH 密钥对...
    echo.
    
    REM 创建 keys 目录（如果不存在）
    if not exist "%KEY_DIR%" mkdir "%KEY_DIR%"
    
    REM 使用 ssh-keygen 生成密钥对（Windows 10+ 自带 OpenSSH）
    ssh-keygen -t rsa -b 4096 -f "%KEY_FILE%" -N "" -C "telegram-ai-system-server-key"
    
    if errorlevel 1 (
        echo ❌ 密钥生成失败
        echo.
        echo 请确保已安装 OpenSSH 客户端：
        echo   1. 打开"设置" -^> "应用" -^> "可选功能"
        echo   2. 搜索"OpenSSH 客户端"并安装
        pause
        exit /b 1
    )
    
    echo ✅ 密钥对生成成功
    echo.
)

REM 读取公钥内容
echo 正在读取公钥...
set PUB_KEY=
for /f "usebackq delims=" %%a in ("%PUB_KEY_FILE%") do set PUB_KEY=!PUB_KEY!%%a

if "%PUB_KEY%"=="" (
    echo ❌ 无法读取公钥文件
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 📤 将公钥复制到服务器
echo ============================================================
echo.
echo 服务器: %SERVER_USER%@%SERVER_HOST%
echo.
echo 注意：首次连接需要输入密码
echo 密码: %SERVER_PASSWORD%
echo.

REM 使用 ssh-copy-id 或手动复制公钥
REM Windows 可能没有 ssh-copy-id，使用 PowerShell 命令

echo 正在复制公钥到服务器...
powershell -Command "$pubKey = Get-Content '%PUB_KEY_FILE%' -Raw; $pubKey = $pubKey.Trim(); $command = \"echo '$pubKey' >> ~/.ssh/authorized_keys\"; $password = ConvertTo-SecureString '%SERVER_PASSWORD%' -AsPlainText -Force; $credential = New-Object System.Management.Automation.PSCredential('%SERVER_USER%', $password); $session = New-SSHSession -ComputerName '%SERVER_HOST%' -Credential $credential -AcceptKey 2>$null; if (-not $session) { Invoke-SSHCommand -ComputerName '%SERVER_HOST%' -Credential $credential -Command \"mkdir -p ~/.ssh && chmod 700 ~/.ssh\" -AcceptKey | Out-Null; Invoke-SSHCommand -ComputerName '%SERVER_HOST%' -Credential $credential -Command \"echo '$pubKey' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys\" -AcceptKey | Out-Null; Write-Host '✅ 公钥已复制到服务器' } else { Write-Host '⚠️  SSH 会话已存在，跳过' }"

REM 如果 PowerShell SSH 模块不可用，使用 sshpass 或手动方法
if errorlevel 1 (
    echo.
    echo ⚠️  自动复制失败，使用手动方法...
    echo.
    echo 请手动执行以下步骤：
    echo.
    echo 1. 使用 SSH 连接到服务器：
    echo    ssh %SERVER_USER%@%SERVER_HOST%
    echo.
    echo 2. 在服务器上执行：
    echo    mkdir -p ~/.ssh
    echo    chmod 700 ~/.ssh
    echo    echo "%PUB_KEY%" ^>^> ~/.ssh/authorized_keys
    echo    chmod 600 ~/.ssh/authorized_keys
    echo.
    echo 或者使用以下命令（需要输入密码）：
    echo.
    
    REM 使用 plink 或 ssh 手动复制
    echo 正在尝试使用 ssh 命令复制公钥...
    type "%PUB_KEY_FILE%" | ssh %SERVER_USER%@%SERVER_HOST% "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
    
    if errorlevel 1 (
        echo.
        echo ❌ 自动复制失败
        echo.
        echo 请手动执行以下命令：
        echo.
        echo   type "%PUB_KEY_FILE%" ^| ssh %SERVER_USER%@%SERVER_HOST% "mkdir -p ~/.ssh ^&^& chmod 700 ~/.ssh ^&^& cat ^>^> ~/.ssh/authorized_keys ^&^& chmod 600 ~/.ssh/authorized_keys"
        echo.
        echo 输入密码: %SERVER_PASSWORD%
        echo.
        pause
        exit /b 1
    )
)

echo.
echo ============================================================
echo ✅ SSH 免密登录配置完成
echo ============================================================
echo.
echo 现在可以使用 ssh-server.bat 免密登录服务器了
echo.
pause

