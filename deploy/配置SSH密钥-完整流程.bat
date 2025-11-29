@echo off
chcp 65001 >nul
title 配置 SSH 密钥认证
echo.
echo ============================================================
echo           配置 SSH 密钥认证（解决密码问题）
echo ============================================================
echo.

REM 步骤 1: 检查是否已有 SSH 密钥
echo [步骤 1/5] 检查是否已有 SSH 密钥...
if exist "%USERPROFILE%\.ssh\id_rsa.pub" (
    echo [OK] 发现现有 SSH 公钥
    echo.
    echo 公钥内容：
    type "%USERPROFILE%\.ssh\id_rsa.pub"
    echo.
    set HAS_KEY=1
) else (
    echo [信息] 未发现 SSH 公钥
    set HAS_KEY=0
)

REM 步骤 2: 生成 SSH 密钥（如果没有）
if "%HAS_KEY%"=="0" (
    echo.
    echo [步骤 2/5] 生成 SSH 密钥对...
    echo 注意：如果提示输入密码，可以直接按 Enter（不设置密码）
    echo.
    if not exist "%USERPROFILE%\.ssh" mkdir "%USERPROFILE%\.ssh"
    ssh-keygen -t rsa -b 4096 -f "%USERPROFILE%\.ssh\id_rsa" -N ""
    if errorlevel 1 (
        echo [错误] 密钥生成失败
        pause
        exit /b 1
    )
    echo [OK] SSH 密钥对已生成
    echo.
    echo 公钥内容：
    type "%USERPROFILE%\.ssh\id_rsa.pub"
) else (
    echo [步骤 2/5] 跳过（已有密钥）
)

REM 步骤 3: 将公钥复制到服务器
echo.
echo [步骤 3/5] 将公钥复制到服务器...
echo 注意：需要输入一次服务器密码
echo.

REM 尝试使用 ssh-copy-id（如果可用）
where ssh-copy-id >nul 2>&1
if %errorlevel%==0 (
    echo 使用 ssh-copy-id 复制公钥...
    ssh-copy-id -i "%USERPROFILE%\.ssh\id_rsa.pub" ubuntu@165.154.233.55
    if errorlevel 1 (
        echo [警告] ssh-copy-id 失败，使用手动方法...
        goto :manual_copy
    ) else (
        echo [OK] 公钥已复制到服务器
        goto :test
    )
) else (
    echo ssh-copy-id 不可用，使用手动方法...
    goto :manual_copy
)

:manual_copy
echo.
echo 使用手动方法复制公钥...
echo.
echo 方法：将公钥内容追加到服务器的 ~/.ssh/authorized_keys 文件
echo.
type "%USERPROFILE%\.ssh\id_rsa.pub" | ssh ubuntu@165.154.233.55 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
if errorlevel 1 (
    echo [错误] 公钥复制失败
    echo.
    echo 请手动执行以下步骤：
    echo 1. 复制上面的公钥内容
    echo 2. 登录服务器：ssh ubuntu@165.154.233.55
    echo 3. 执行：
    echo    mkdir -p ~/.ssh
    echo    chmod 700 ~/.ssh
    echo    nano ~/.ssh/authorized_keys
    echo 4. 粘贴公钥内容，保存退出
    echo 5. 执行：chmod 600 ~/.ssh/authorized_keys
    pause
    exit /b 1
)
echo [OK] 公钥已复制到服务器

:test
REM 步骤 4: 测试无密码登录
echo.
echo [步骤 4/5] 测试无密码登录...
ssh -o BatchMode=yes -o ConnectTimeout=5 ubuntu@165.154.233.55 "echo 'SSH 密钥认证测试成功！'" >nul 2>&1
if errorlevel 1 (
    echo [错误] 无密码登录测试失败
    echo.
    echo 可能原因：
    echo 1. 公钥未正确复制到服务器
    echo 2. 服务器权限设置不正确
    echo.
    echo 请检查服务器上的权限：
    echo   ssh ubuntu@165.154.233.55
    echo   ls -la ~/.ssh/
    echo   chmod 700 ~/.ssh
    echo   chmod 600 ~/.ssh/authorized_keys
    pause
    exit /b 1
) else (
    echo [OK] SSH 密钥认证配置成功！
)

REM 步骤 5: 验证配置
echo.
echo [步骤 5/5] 验证配置...
echo.
echo 测试执行远程命令（应该不需要密码）：
ssh ubuntu@165.154.233.55 "whoami && pwd && echo 'SSH 密钥认证工作正常！'"

echo.
echo ============================================================
echo 配置完成！
echo ============================================================
echo.
echo 现在可以无密码执行 SSH 命令了
echo 可以运行自动化脚本：
echo - deploy\一键修复WebSocket连接.bat
echo - deploy\一键检查WebSocket配置.bat
echo.
pause

