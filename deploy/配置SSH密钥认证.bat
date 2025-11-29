@echo off
chcp 65001 >nul
echo ============================================================
echo 配置 SSH 密钥认证
echo ============================================================
echo.

REM 检查是否已有 SSH 密钥
echo [步骤 1/4] 检查是否已有 SSH 密钥...
if exist "%USERPROFILE%\.ssh\id_rsa" (
    echo [OK] 发现现有 SSH 私钥
    if exist "%USERPROFILE%\.ssh\id_rsa.pub" (
        echo [OK] 发现现有 SSH 公钥
        echo.
        echo 公钥内容：
        type "%USERPROFILE%\.ssh\id_rsa.pub"
        echo.
        goto :copy_key
    ) else (
        echo [警告] 私钥存在但公钥不存在，将重新生成
        goto :generate_key
    )
) else (
    echo [信息] 未发现 SSH 密钥，将生成新的密钥对
    goto :generate_key
)

:generate_key
echo.
echo [步骤 2/4] 生成 SSH 密钥对...
echo 注意：如果提示输入密码，可以直接按 Enter（不设置密码）
echo.
ssh-keygen -t rsa -b 4096 -f "%USERPROFILE%\.ssh\id_rsa" -N '""'
if errorlevel 1 (
    echo [错误] 密钥生成失败
    pause
    exit /b 1
)
echo [OK] SSH 密钥对已生成

:copy_key
echo.
echo [步骤 3/4] 将公钥复制到服务器...
echo 注意：需要输入一次服务器密码
echo.
ssh-copy-id -i "%USERPROFILE%\.ssh\id_rsa.pub" ubuntu@165.154.233.55
if errorlevel 1 (
    echo.
    echo [警告] ssh-copy-id 可能不可用，尝试手动复制...
    echo.
    echo 请手动执行以下步骤：
    echo 1. 复制以下公钥内容：
    echo.
    type "%USERPROFILE%\.ssh\id_rsa.pub"
    echo.
    echo 2. 登录服务器：ssh ubuntu@165.154.233.55
    echo 3. 执行以下命令：
    echo    mkdir -p ~/.ssh
    echo    chmod 700 ~/.ssh
    echo    echo "粘贴上面的公钥内容" ^>^> ~/.ssh/authorized_keys
    echo    chmod 600 ~/.ssh/authorized_keys
    echo.
    pause
    goto :test
)

:test
echo.
echo [步骤 4/4] 测试无密码登录...
echo.
ssh -o BatchMode=yes -o ConnectTimeout=5 ubuntu@165.154.233.55 "echo 'SSH 密钥认证测试成功！'"
if errorlevel 1 (
    echo [错误] 无密码登录测试失败
    echo 请检查：
    echo 1. 公钥是否已正确复制到服务器
    echo 2. 服务器 ~/.ssh/authorized_keys 文件权限是否正确（应该是 600）
    echo 3. 服务器 ~/.ssh 目录权限是否正确（应该是 700）
    pause
    exit /b 1
) else (
    echo [OK] SSH 密钥认证配置成功！
    echo.
    echo 现在可以无密码执行 SSH 命令了
)

echo.
echo ============================================================
echo 配置完成！
echo ============================================================
echo.
echo 现在可以运行自动化脚本了：
echo - deploy\一键修复WebSocket连接.bat
echo - deploy\一键检查WebSocket配置.bat
echo.
pause

