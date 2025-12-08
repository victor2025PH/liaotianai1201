@echo off
chcp 65001 >nul
echo ============================================================
echo 运行后端测试 (Backend Tests)
echo ============================================================
echo.

cd /d "%~dp0\..\..\admin-backend"

echo [1/3] 检查虚拟环境...
if not exist "venv\Scripts\activate.bat" (
    echo ❌ 虚拟环境不存在，请先创建虚拟环境
    pause
    exit /b 1
)

echo [2/3] 激活虚拟环境并运行测试...
call venv\Scripts\activate.bat
python -m pytest tests/ -v --tb=short

echo.
echo ============================================================
echo 测试完成
echo ============================================================
pause

