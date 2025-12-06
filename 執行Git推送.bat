@echo off
chcp 65001 >nul
echo ========================================
echo Git 提交和推送到 GitHub
echo ========================================
echo.

cd /d "D:\telegram-ai-system"

echo [1/4] 檢查 Git 狀態...
git status --short
echo.

echo [2/4] 添加所有變更...
git add -A
echo.

echo [3/4] 檢查遠程倉庫配置...
git remote -v
echo.

echo [4/4] 推送到 GitHub...
echo 請選擇分支:
echo 1. main
echo 2. master
echo.
set /p choice=請輸入選項 (1 或 2): 

if "%choice%"=="1" (
    echo 推送到 main 分支...
    git push -u origin main
) else (
    echo 推送到 master 分支...
    git push -u origin master
)

echo.
echo ========================================
echo 完成！
echo ========================================
pause
