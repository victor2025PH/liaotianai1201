@echo off
chcp 65001 >nul
REM ============================================================
REM SSH to Server - Quick Connect
REM ============================================================
REM
REM Running Environment: Local Windows Environment
REM Function: Open PowerShell and SSH to server (165.154.233.55)
REM
REM One-click execution: Double-click this file
REM ============================================================

echo ============================================================
echo 🔌 Connecting to Server...
echo ============================================================
echo.
echo Server: ubuntu@165.154.233.55
echo.

REM Open PowerShell and execute SSH command
powershell -NoExit -Command "ssh -o StrictHostKeyChecking=no ubuntu@165.154.233.55"

