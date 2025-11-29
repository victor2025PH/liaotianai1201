@echo off
chcp 65001 >nul
title 一键配置 SSH 密钥
echo.
echo ============================================================
echo           一键配置 SSH 密钥认证
echo ============================================================
echo.

REM 检查是否已有密钥
if exist "%USERPROFILE%\.ssh\id_rsa.pub" (
    echo [OK] 发现现有 SSH 公钥
    echo.
    echo 公钥内容：
    type "%USERPROFILE%\.ssh\id_rsa.pub"
    echo.
    echo 按任意键继续复制公钥到服务器...
    pause >nul
) else (
    echo [信息] 未发现 SSH 公钥，正在生成...
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
    echo.
)

echo.
echo ============================================================
echo 将公钥复制到服务器
echo ============================================================
echo.
echo 注意：需要输入一次服务器密码
echo.
echo 正在复制公钥...
type "%USERPROFILE%\.ssh\id_rsa.pub" | ssh ubuntu@165.154.233.55 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
if errorlevel 1 (
    echo.
    echo [错误] 公钥复制失败
    echo.
    echo 请手动执行以下步骤：
    echo 1. 复制上面的公钥内容
    echo 2. 登录服务器：ssh ubuntu@165.154.233.55
    echo 3. 执行：
    echo    mkdir -p ~/.ssh
    echo    chmod 700 ~/.ssh
    echo    nano ~/.ssh/authorized_keys
    echo 4. 粘贴公钥内容，保存退出（Ctrl+O, Enter, Ctrl+X）
    echo 5. 执行：chmod 600 ~/.ssh/authorized_keys
    pause
    exit /b 1
)

echo.
echo [OK] 公钥已复制到服务器
echo.
echo ============================================================
echo 测试无密码登录
echo ============================================================
echo.
echo 正在测试...
ssh -o BatchMode=yes -o ConnectTimeout=5 ubuntu@165.154.233.55 "echo 'SSH 密钥认证测试成功！'" >nul 2>&1
if errorlevel 1 (
    echo [警告] 无密码登录测试失败
    echo.
    echo 可能原因：
    echo 1. 服务器权限设置不正确
    echo.
    echo 请在服务器上执行：
    echo   chmod 700 ~/.ssh
    echo   chmod 600 ~/.ssh/authorized_keys
    echo.
    pause
    exit /b 1
)

echo [OK] SSH 密钥认证配置成功！
echo.
echo 测试执行远程命令：
ssh ubuntu@165.154.233.55 "whoami && echo 'SSH 密钥认证工作正常！'"

echo.
echo ============================================================
echo 配置完成！
echo ============================================================
echo.
echo 现在可以无密码执行 SSH 命令了
echo 可以运行自动化脚本：
echo - deploy\一键修复WebSocket连接.bat
echo.
pause

