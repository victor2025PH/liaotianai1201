@echo off
chcp 65001 >nul
echo ========================================
echo 启动后端服务 (FastAPI)
echo ========================================
echo.

cd /d "%~dp0..\admin-backend"

echo 当前目录: %CD%
echo.
echo 正在启动 FastAPI 服务...
echo 请等待服务启动完成...
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause

