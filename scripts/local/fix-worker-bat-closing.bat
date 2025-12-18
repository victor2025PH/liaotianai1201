@echo off
chcp 65001 >nul
echo ============================================================
echo Worker 部署脚本窗口关闭问题修复工具
echo ============================================================
echo.
echo 此工具将帮助诊断批处理脚本窗口立即关闭的问题
echo.

:: 查找 worker-deploy 目录
set WORKER_DEPLOY_DIR=
if exist "%~dp0..\worker-deploy-pc-001" (
    set WORKER_DEPLOY_DIR=%~dp0..\worker-deploy-pc-001
    echo 检测到 worker-deploy-pc-001
)
if exist "%~dp0..\worker-deploy-pc-002" (
    if defined WORKER_DEPLOY_DIR (
        echo 检测到 worker-deploy-pc-002
        echo.
        echo 请选择要检查的目录：
        echo   1. worker-deploy-pc-001
        echo   2. worker-deploy-pc-002
        set /p choice="请输入选择 (1/2): "
        if "%choice%"=="2" (
            set WORKER_DEPLOY_DIR=%~dp0..\worker-deploy-pc-002
        )
    ) else (
        set WORKER_DEPLOY_DIR=%~dp0..\worker-deploy-pc-002
    )
)
if exist "%~dp0..\worker-deploy-pc-003" (
    if not defined WORKER_DEPLOY_DIR (
        set WORKER_DEPLOY_DIR=%~dp0..\worker-deploy-pc-003
    )
)

if not defined WORKER_DEPLOY_DIR (
    echo ❌ 未找到 worker-deploy 目录
    echo 请确保 worker-deploy-pc-001/002/003 目录存在
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 检查目录: %WORKER_DEPLOY_DIR%
echo ============================================================
cd /d "%WORKER_DEPLOY_DIR%"

:: 列出所有 .bat 文件
echo.
echo [1/4] 查找批处理文件...
dir /b *.bat 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  未找到 .bat 文件
) else (
    echo ✅ 找到批处理文件
)

:: 检查是否有包含 "Environment Check" 的脚本
echo.
echo [2/4] 检查环境检查相关脚本...
findstr /C:"Environment Check" /C:"环境检查" *.bat *.py 2>nul
if %errorlevel% equ 0 (
    echo ✅ 找到包含环境检查的脚本
) else (
    echo ⚠️  未找到包含环境检查的脚本
)

:: 检查 Python 环境
echo.
echo [3/4] 检查 Python 环境...
python --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python 可用
    python -c "import sys; print(f'Python 版本: {sys.version}')"
) else (
    echo ❌ Python 不可用
    echo 请确保 Python 已安装并添加到 PATH
)

echo.
pip --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ pip 可用
) else (
    echo ❌ pip 不可用
)

:: 创建修复后的测试脚本
echo.
echo [4/4] 创建测试脚本（带暂停）...
(
echo @echo off
echo chcp 65001 ^>nul
echo echo ============================================================
echo echo Environment Check and Setup
echo echo ============================================================
echo echo.
echo echo [1/4] Checking Python installation...
echo python --version
echo if %%errorlevel%% neq 0 ^(
echo     echo ❌ Python not found
echo     pause
echo     exit /b 1
echo ^)
echo for /f "tokens=2" %%i in ('python --version 2^>^&1'^) do set PYTHON_VERSION=%%i
echo echo [OK] Python found: %%PYTHON_VERSION%%
echo echo.
echo echo [2/4] Checking pip...
echo pip --version ^>nul 2^>^&1
echo if %%errorlevel%% neq 0 ^(
echo     echo ❌ pip not found
echo     pause
echo     exit /b 1
echo ^)
echo echo [OK] pip is available
echo echo.
echo echo [INFO] Upgrading pip to latest version...
echo python -m pip install --upgrade pip --quiet
echo if %%errorlevel%% neq 0 ^(
echo     echo ❌ pip upgrade failed
echo     pause
echo     exit /b 1
echo ^)
echo echo [OK] pip upgraded successfully
echo echo.
echo echo [3/4] Checking required packages...
echo python -c "import sys; packages=['requests', 'telethon']; missing=[p for p in packages if not __import__('pkgutil').find_loader^(p^)]; sys.exit^(1^ if missing else 0^)" 2^>nul
echo if %%errorlevel%% neq 0 ^(
echo     echo ⚠️  Some packages are missing
echo     echo Installing required packages...
echo     pip install -r requirements.txt 2^>nul
echo ^)
echo echo.
echo echo [4/4] Final check...
echo echo ✅ Environment check complete
echo echo.
echo ============================================================
echo Environment setup completed successfully
echo ============================================================
echo.
echo 按任意键继续...
pause ^>nul
) > test-environment-check.bat

echo ✅ 已创建测试脚本: test-environment-check.bat
echo.
echo ============================================================
echo 诊断完成
echo ============================================================
echo.
echo 建议:
echo 1. 运行 test-environment-check.bat 来测试环境检查
echo 2. 如果原脚本仍然立即关闭，请在脚本末尾添加 'pause' 命令
echo 3. 检查脚本中是否有 'exit /b' 或 'exit' 命令导致提前退出
echo 4. 使用以下命令运行脚本以查看错误信息:
echo    cmd /k your-script.bat
echo.
echo 按任意键退出...
pause >nul
