@echo off
REM 安装 Telethon 及其依赖（Windows）

echo ========================================
echo 安装 Telethon 及其依赖
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未安装，请先安装 Python 3.9+
    pause
    exit /b 1
)

echo [1/3] 检查当前安装的包...
python -m pip list | findstr /i "telethon requests openpyxl"
echo.

echo [2/3] 安装 Telethon 及其依赖...
echo 使用清华大学镜像源（国内用户推荐）...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
python -m pip install telethon requests openpyxl -i https://pypi.tuna.tsinghua.edu.cn/simple

if errorlevel 1 (
    echo [WARN] 镜像源安装失败，尝试使用默认源...
    python -m pip install telethon requests openpyxl --upgrade
    if errorlevel 1 (
        echo [ERROR] 依赖安装失败
        pause
        exit /b 1
    )
)
echo.

echo [3/3] 验证安装...
python -c "import telethon; print(f'Telethon 版本: {telethon.__version__}')"
python -c "import requests; print(f'Requests 版本: {requests.__version__}')"
python -c "import openpyxl; print(f'OpenPyXL 版本: {openpyxl.__version__}')"
echo.

echo ========================================
echo 安装完成！
echo ========================================
echo.
pause
