@echo off
chcp 65001 >nul
REM ============================================================
REM 驗證前端功能（本地開發環境 - Windows）
REM ============================================================
REM 
REM 運行環境：本地 Windows 開發環境
REM 功能：驗證前端服務和功能是否正常
REM 
REM 一鍵執行：雙擊此文件
REM 分步執行：見下方說明
REM ============================================================

cd /d "%~dp0\..\..\admin-backend"

echo ============================================================
echo 🧪 執行前端功能自動化驗證
echo ============================================================
echo.

echo 檢查服務狀態...
echo.

curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 後端服務未運行
    echo.
    echo 請先啟動後端服務：
    echo   cd admin-backend
    echo   set DATABASE_URL=sqlite:///./admin.db
    echo   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
    echo.
    echo 或運行：scripts\local\start-all-services.bat
    echo.
    pause
    exit /b 1
) else (
    echo ✅ 後端服務運行中
)

curl -s http://localhost:3000 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 前端服務未運行
    echo.
    echo 請先啟動前端服務：
    echo   cd saas-demo
    echo   npm run dev
    echo.
    echo 或運行：scripts\local\start-all-services.bat
    echo.
    pause
    exit /b 1
) else (
    echo ✅ 前端服務運行中
)

echo.
echo ============================================================
echo 執行自動化驗證...
echo ============================================================
echo.

python scripts\auto_frontend_verification.py

echo.
echo ============================================================
echo 📊 驗證完成
echo ============================================================
echo.
echo 下一步：
echo   1. 查看上述驗證結果
echo   2. 訪問 http://localhost:3000 進行手動驗證
echo   3. 參考：admin-backend\前端功能驗證清單.md
echo.
pause

REM ============================================================
REM 分步執行說明：
REM ============================================================
REM 
REM 步驟 1: 確保服務運行
REM   後端: http://localhost:8000
REM   前端: http://localhost:3000
REM 
REM 步驟 2: 運行自動化驗證
REM   python scripts\auto_frontend_verification.py
REM 
REM 步驟 3: 手動驗證
REM   訪問 http://localhost:3000
REM   參考前端功能驗證清單
REM ============================================================

