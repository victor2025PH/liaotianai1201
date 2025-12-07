@echo off
chcp 65001 >nul
REM ============================================================
REM 執行所有部署準備任務（本地開發環境 - Windows）
REM ============================================================
REM 
REM 運行環境：本地 Windows 開發環境
REM 功能：執行安全配置、環境變量檢查、前端驗證等所有任務
REM 
REM 一鍵執行：雙擊此文件
REM 分步執行：見下方說明
REM ============================================================

cd /d "%~dp0\..\..\admin-backend"

echo ============================================================
echo 🚀 自動執行所有部署準備任務
echo ============================================================
echo.

echo [1/3] 🔒 檢查安全配置...
python scripts\check_security_config.py
set CHECK_RESULT=%ERRORLEVEL%
if %CHECK_RESULT% NEQ 0 (
    echo.
    echo ⚠️  發現安全問題，正在設置生產環境安全配置...
    echo.
    python scripts\setup_production_security.py
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ 安全配置設置失敗
        pause
        exit /b 1
    )
    echo.
    echo 等待配置生效...
    timeout /t 1 /nobreak >nul
    echo.
    echo 再次檢查安全配置...
    python scripts\check_security_config.py
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ⚠️  注意：配置已保存到 .env 文件，但需要重啟服務才能生效
        echo ⚠️  或者設置系統環境變量以立即生效
    ) else (
        echo ✅ 安全配置檢查通過！
    )
)

echo.
echo [2/3] 📋 檢查環境變量文檔...
if not exist ".env.example" (
    echo ⚠️  .env.example 不存在
    echo 請參考 config\worker.env.example 創建 .env.example
    echo 或查看：環境變量設置指南.md
) else (
    echo ✅ .env.example 已存在
)

echo.
echo [3/3] 🧪 前端功能驗證...
echo 注意：此步驟需要後端和前端服務都在運行
echo.
python scripts\auto_frontend_verification.py

echo.
echo ============================================================
echo 📊 任務執行完成
echo ============================================================
echo.
echo 下一步：
echo   1. 檢查上述輸出，確保所有檢查通過
echo   2. 如果安全配置有問題，請運行: python scripts\setup_production_security.py
echo   3. 完成前端手動驗證（參考：前端功能驗證清單.md）
echo.
pause

REM ============================================================
REM 分步執行說明：
REM ============================================================
REM 
REM 步驟 1: 檢查安全配置
REM   python scripts\check_security_config.py
REM   python scripts\setup_production_security.py
REM 
REM 步驟 2: 檢查環境變量文檔
REM   確認 .env.example 存在
REM   參考：環境變量設置指南.md
REM 
REM 步驟 3: 前端功能驗證
REM   確保服務運行
REM   python scripts\auto_frontend_verification.py
REM ============================================================

