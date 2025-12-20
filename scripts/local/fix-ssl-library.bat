@echo off
REM ============================================================
REM Worker Node SSL 庫修復腳本 (Windows)
REM ============================================================

echo.
echo ========================================
echo Worker Node SSL 庫修復
echo ========================================
echo.

REM 檢查 Python
echo [1/4] 檢查 Python 安裝...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未找到！
    echo 請先安裝 Python 3.9 或更高版本
    echo 下載地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python 版本: %PYTHON_VERSION%
echo.

REM 檢查 SSL 庫
echo [2/4] 檢查 SSL 庫...
python -c "import ssl; print('SSL 版本:', ssl.OPENSSL_VERSION)" 2>nul
if errorlevel 1 (
    echo [WARN] SSL 庫不可用
    echo [INFO] 嘗試修復...
    echo.
    
    REM 升級 pip
    echo [INFO] 升級 pip...
    python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
    if errorlevel 1 (
        python -m pip install --upgrade pip >nul 2>&1
    )
    
    REM 安裝 SSL 相關包
    echo [INFO] 安裝 SSL 相關依賴...
    python -m pip install --upgrade certifi pyopenssl cryptography -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo [WARN] 鏡像源失敗，嘗試默認源...
        python -m pip install --upgrade certifi pyopenssl cryptography
    )
    
    REM 再次檢查
    echo.
    echo [INFO] 驗證修復結果...
    python -c "import ssl; print('SSL 版本:', ssl.OPENSSL_VERSION)" 2>nul
    if errorlevel 1 (
        echo.
        echo [ERROR] SSL 庫修復失敗！
        echo.
        echo 解決方案：
        echo 1. 重新安裝完整版 Python（推薦）
        echo    - 訪問 https://www.python.org/downloads/
        echo    - 下載並安裝 Python 3.11 或更高版本
        echo    - 安裝時勾選 "Add Python to PATH"
        echo.
        echo 2. 或安裝 OpenSSL for Windows
        echo    - 下載: https://slproweb.com/products/Win32OpenSSL.html
        echo    - 安裝到 C:\OpenSSL-Win64
        echo    - 將 C:\OpenSSL-Win64\bin 添加到系統 PATH
        echo.
        pause
        exit /b 1
    ) else (
        echo [OK] SSL 庫修復成功！
    )
) else (
    echo [OK] SSL 庫可用
)
echo.

REM 檢查 cryptg（可選）
echo [3/4] 檢查 cryptg 模組（可選但推薦）...
python -c "import cryptg" >nul 2>&1
if errorlevel 1 (
    echo [INFO] cryptg 未安裝，正在安裝...
    python -m pip install cryptg -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
    if errorlevel 1 (
        python -m pip install cryptg >nul 2>&1
    )
    python -c "import cryptg" >nul 2>&1
    if errorlevel 1 (
        echo [INFO] cryptg 安裝失敗，將使用較慢的 Python 加密
    ) else (
        echo [OK] cryptg 安裝成功
    )
) else (
    echo [OK] cryptg: 已安裝
)
echo.

REM 測試 HTTPS 連接
echo [4/4] 測試 HTTPS 連接...
python -c "import requests; r = requests.get('https://www.google.com', timeout=5); print('HTTPS 連接成功' if r.status_code == 200 else '連接失敗')" 2>nul
if errorlevel 1 (
    echo [WARN] HTTPS 連接測試失敗（可能是網絡問題）
) else (
    echo [OK] HTTPS 連接測試成功
)
echo.

echo ========================================
echo ✅ SSL 庫檢查完成
echo ========================================
echo.
echo 如果仍有問題，請查看文檔: docs\WORKER_SSL_FIX.md
echo.
pause
