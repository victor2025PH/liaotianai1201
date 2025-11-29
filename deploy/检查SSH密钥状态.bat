@echo off
chcp 65001 >nul
echo ============================================================
echo 检查 SSH 密钥配置状态
echo ============================================================
echo.

echo [1] 检查本地 SSH 密钥...
if exist "%USERPROFILE%\.ssh\id_rsa.pub" (
    echo [OK] 发现 SSH 公钥
    echo.
    echo 公钥内容：
    type "%USERPROFILE%\.ssh\id_rsa.pub"
    echo.
) else (
    echo [警告] 未发现 SSH 公钥
    echo 需要先生成 SSH 密钥
    goto :end
)

echo [2] 测试 SSH 无密码登录...
ssh -o BatchMode=yes -o ConnectTimeout=5 ubuntu@165.154.233.55 "echo 'SSH密钥测试成功'" 2>&1
if errorlevel 1 (
    echo [错误] SSH 密钥未配置到服务器
    echo.
    echo 需要将公钥复制到服务器
    echo 请运行：deploy\配置SSH密钥认证.bat
) else (
    echo [OK] SSH 密钥认证已配置
    echo 可以运行自动化脚本了
)

:end
echo.
pause

