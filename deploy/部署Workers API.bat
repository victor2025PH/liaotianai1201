@echo off
chcp 65001 >nul
echo ========================================
echo 部署 Workers API 到服务器
echo ========================================
echo.

cd /d "%~dp0"
python deploy_workers_api.py

echo.
echo 按任意键退出...
pause >nul

