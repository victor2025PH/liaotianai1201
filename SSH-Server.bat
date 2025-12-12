@echo off
chcp 65001 >nul
REM ============================================================
REM SSH to Server - Quick Connect (Optimized)
REM ============================================================
REM
REM Server: los-angeles node (165.154.235.170)
REM User: ubuntu
REM Authentication: Password (will prompt for password)
REM
REM One-click execution: Double-click this file
REM ============================================================

echo ============================================================
echo 🔌 Connecting to Server...
echo ============================================================
echo.
echo Server: ubuntu@165.154.235.170 (los-angeles)
echo.
echo Note: You will be prompted to enter password
echo Password: 8iDcGrYb52Fxpzee
echo.

REM Open PowerShell and execute SSH command with optimized settings
REM -q: Quiet mode (suppress most output)
REM -o LogLevel=ERROR: Only show errors
REM -o StrictHostKeyChecking=no: Skip host key verification
REM -o UserKnownHostsFile=/dev/null: Don't save host keys
REM Note: Using password authentication (no -i key file)
powershell -NoExit -Command "ssh -q -o LogLevel=ERROR -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@165.154.235.170"

