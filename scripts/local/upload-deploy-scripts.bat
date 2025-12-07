@echo off
REM ============================================================
REM Upload Deploy Scripts to GitHub (Local Execution)
REM ============================================================
REM 
REM Function: Upload all deployment-related scripts to GitHub
REM Running Environment: Local Windows Environment
REM 
REM One-click execution: scripts\local\upload-deploy-scripts.bat
REM ============================================================

REM Set UTF-8 encoding
chcp 65001 >nul

echo ============================================================
echo Upload Deploy Scripts to GitHub
echo ============================================================
echo.

REM Switch to project root
cd /d "%~dp0\..\.."

REM Check if in project root
if not exist "scripts\server\" (
    echo Error: Please run from project root directory
    pause
    exit /b 1
)

echo [1/4] Checking file status...
git status --short | findstr /i "diagnose fix-service NEXT_STEPS"

echo.
echo [2/4] Adding deployment scripts...
git add scripts/server/diagnose-service.sh
git add scripts/server/fix-service.sh
git add scripts/server/manual-fix-service.sh
git add scripts/server/fix-and-pull.sh
git add scripts/server/resolve-local-changes.sh
git add scripts/server/force-pull-latest.sh
git add scripts/server/complete-setup.sh
git add scripts/server/quick-deploy-setup.sh
git add NEXT_STEPS.md
git add DEPLOY_GUIDE.md
git add DEPLOY_QUICK_START.md

echo.
echo [3/4] Committing changes...
git commit -m "Add service diagnosis and fix scripts for deployment"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Warning: Commit failed. Checking if files are already committed...
    git status --short
    pause
)

echo.
echo [4/4] Pushing to GitHub...
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo Upload successful!
    echo ============================================================
    echo.
    echo Next steps on server:
    echo   1. cd ~/telegram-ai-system
    echo   2. git pull origin main
    echo   3. bash scripts/server/fix-service.sh
) else (
    echo.
    echo ============================================================
    echo Upload failed!
    echo ============================================================
    echo.
    echo Please check:
    echo   1. Git remote is configured: git remote -v
    echo   2. You have push permissions
    echo   3. Network connection is working
)

echo.
pause

