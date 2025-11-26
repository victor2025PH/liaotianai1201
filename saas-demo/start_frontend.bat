@echo off
chcp 65001 >nul
title 聊天 AI 控制台 - 前端

echo ========================================
echo   聊天 AI 控制台 前端
echo   後端: http://jblt.usdt2026.cc
echo ========================================

cd /d "%~dp0"

REM 設置環境變量指向域名
set NEXT_PUBLIC_API_BASE_URL=http://jblt.usdt2026.cc/api/v1
set NEXT_PUBLIC_API_URL=http://jblt.usdt2026.cc/api/v1/group-ai

echo.
echo 環境配置:
echo   API_BASE_URL: %NEXT_PUBLIC_API_BASE_URL%
echo   API_URL: %NEXT_PUBLIC_API_URL%
echo.

echo 檢查依賴...
if not exist "node_modules" (
    echo 安裝依賴中...
    call npm install
)

echo.
echo 啟動前端服務...
echo 訪問地址: http://localhost:3000
echo.

call npm run dev

