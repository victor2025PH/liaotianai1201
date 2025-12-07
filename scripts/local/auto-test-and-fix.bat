@echo off
chcp 65001 >nul
REM ============================================================
REM 全自動測試和修復（本地開發環境 - Windows）
REM ============================================================
REM 
REM 運行環境：本地 Windows 開發環境
REM 功能：自動測試所有功能，檢測錯誤並自動修復
REM 
REM 一鍵執行：雙擊此文件
REM 分步執行：見下方說明
REM ============================================================

cd /d "%~dp0\..\..\admin-backend"

echo ============================================================
echo 🚀 全自動測試和修復系統
echo ============================================================
echo.

echo [步驟 1/5] 修復配置...
python scripts\check_security_config.py >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 設置安全配置...
    python scripts\setup_production_security.py
)

echo.
echo [步驟 2/5] 初始化數據庫...
set DATABASE_URL=sqlite:///./admin.db
python init_db_tables.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 數據庫初始化失敗
    pause
    exit /b 1
)

echo.
echo [步驟 3/5] 啟動後端服務...
start "後端服務" cmd /k "set DATABASE_URL=sqlite:///./admin.db && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo 等待服務啟動...
timeout /t 15 /nobreak >nul

echo.
echo [步驟 4/5] 驗證服務...
curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ 後端服務運行正常
) else (
    echo ⚠️ 後端服務可能仍在啟動中
)

echo.
echo [步驟 5/5] 運行自動化測試...
python scripts\auto_test_and_fix.py

echo.
echo ============================================================
echo 📊 測試完成
echo ============================================================
echo.
echo 服務地址：
echo   後端: http://localhost:8000
echo   前端: http://localhost:3000
echo   API 文檔: http://localhost:8000/docs
echo.
echo 查看詳細報告: admin-backend\最終測試報告.md
echo.
pause

REM ============================================================
REM 分步執行說明：
REM ============================================================
REM 
REM 步驟 1: 修復配置
REM   python scripts\check_security_config.py
REM   python scripts\setup_production_security.py
REM 
REM 步驟 2: 初始化數據庫
REM   set DATABASE_URL=sqlite:///./admin.db
REM   python init_db_tables.py
REM 
REM 步驟 3: 啟動服務
REM   set DATABASE_URL=sqlite:///./admin.db
REM   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
REM 
REM 步驟 4: 驗證服務
REM   curl http://localhost:8000/health
REM 
REM 步驟 5: 運行測試
REM   python scripts\auto_test_and_fix.py
REM ============================================================

