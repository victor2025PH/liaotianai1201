@echo off
REM ============================================================
REM 立即同步腳本到服務器 (本地執行)
REM ============================================================
REM 
REM 功能：將新創建的服務器腳本上傳到 GitHub
REM 運行環境：本地 Windows 環境
REM 
REM 一鍵執行：scripts\local\sync-scripts-to-server.bat
REM ============================================================

REM 設置 UTF-8 編碼，避免中文亂碼
chcp 65001 >nul

echo ============================================================
echo 同步服務器腳本到 GitHub
echo ============================================================
echo.

REM 切換到項目根目錄
cd /d "%~dp0\..\.."

REM 檢查是否在項目根目錄
if not exist "scripts\server\" (
    echo ❌ 錯誤：請在項目根目錄執行此腳本
    pause
    exit /b 1
)

echo [1/3] 檢查 Git 狀態...
git status

echo.
echo [2/3] 添加服務器腳本文件...
REM 添加所有服務器腳本（包括新創建的）
git add scripts/server/*.sh
git add scripts/server/*.md
git add scripts/server/README.md
REM 添加相關文檔（如果存在，已重命名為英文）
if exist "server-deployment-quick-guide.md" git add server-deployment-quick-guide.md
if exist "server-download-scripts-guide.md" git add server-download-scripts-guide.md
REM 添加規則文件
git add .cursor/rules/file-organization.mdc
REM 檢查是否有未跟蹤的文件
git add -f scripts/server/

echo.
echo [3/3] 提交並推送到 GitHub...
REM 使用英文提交信息，避免亂碼
git commit -m "Add server deployment scripts: install-dependencies, setup-server, quick-start, sync guide"

echo.
echo 正在推送到 GitHub...
git push origin main

REM 驗證推送是否成功
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo 推送成功！
    echo ============================================================
    echo.
    echo 已上傳的文件：
    git log -1 --name-only --pretty=format:""
) else (
    echo.
    echo ============================================================
    echo 推送失敗！請檢查錯誤信息
    echo ============================================================
)

echo.
echo ============================================================
echo ✅ 同步完成！
echo ============================================================
echo.
echo 📋 下一步：在服務器上執行以下命令
echo.
echo    cd ~/telegram-ai-system
echo    git pull origin main
echo    chmod +x scripts/server/*.sh
echo    bash scripts/server/quick-start.sh
echo.
pause

