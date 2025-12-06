@echo off
chcp 65001 >nul
title 紅包 API 功能測試
color 0A

echo.
echo ============================================================
echo   🧧 紅包 API 功能測試
echo ============================================================
echo.

cd /d "%~dp0"

REM 檢查虛擬環境
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo [√] 虛擬環境已激活
) else (
    echo [!] 未找到虛擬環境，使用系統 Python
)

echo.
echo 開始測試...
echo.

python admin-backend\start_api_test.py

echo.
echo ============================================================
echo   測試完成
echo ============================================================
echo.
pause
