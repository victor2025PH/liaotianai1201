@echo off
chcp 65001 >nul
title 安裝項目依賴
color 0E

echo.
echo ============================================================
echo   📦 安裝項目依賴
echo ============================================================
echo.

cd /d "%~dp0"

REM 檢查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] 未找到 Python，請先安裝 Python 3.9+
    pause
    exit /b 1
)

echo [√] Python 已安裝
python --version
echo.

REM 創建虛擬環境（如果不存在）
if not exist ".venv" (
    echo 創建虛擬環境...
    python -m venv .venv
    echo [√] 虛擬環境已創建
)

REM 激活虛擬環境
call .venv\Scripts\activate.bat
echo [√] 虛擬環境已激活
echo.

REM 安裝依賴
echo 安裝依賴包...
pip install -r admin-backend\requirements.txt -q

echo.
echo [√] 依賴安裝完成！
echo.

REM 驗證關鍵包
echo 驗證關鍵包...
python -c "import telethon; print('  [√] telethon')"
python -c "import httpx; print('  [√] httpx')"
python -c "import openpyxl; print('  [√] openpyxl')"
python -c "import fastapi; print('  [√] fastapi')"

echo.
echo ============================================================
echo   安裝完成！
echo   下一步: 雙擊「啟動紅包API測試.bat」測試系統
echo ============================================================
echo.
pause
