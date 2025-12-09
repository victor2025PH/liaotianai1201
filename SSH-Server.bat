@echo off
chcp 65001 >nul
REM ============================================================
REM SSH to Server - Quick Connect (Optimized)
REM ============================================================

REM Open PowerShell and execute SSH command with optimized settings
REM -q: Quiet mode (suppress most output)
REM -o LogLevel=ERROR: Only show errors
REM -o StrictHostKeyChecking=no: Skip host key verification
REM -o UserKnownHostsFile=/dev/null: Don't save host keys
powershell -NoExit -Command "ssh -q -o LogLevel=ERROR -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@165.154.233.55"

