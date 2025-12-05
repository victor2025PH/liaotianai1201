@echo off
chcp 65001 >nul
title 完整業務自動化系統
color 0B

echo.
echo ============================================================
echo   🚀 完整業務自動化系統
echo   功能: LLM對話 ^| 多群組 ^| 紅包遊戲 ^| 實時監控 ^| 數據分析
echo ============================================================
echo.

cd /d "%~dp0"

REM 檢查虛擬環境
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo [√] 虛擬環境已激活
) else (
    echo [!] 未找到虛擬環境，使用系統 Python
)

REM 設置環境變量
set REDPACKET_API_URL=https://api.usdt2026.cc
set REDPACKET_API_KEY=test-key-2024
set GAME_STRATEGY=smart
set AUTO_GRAB=true
set AUTO_SEND=false
set AUTO_CHAT=true
set LOG_LEVEL=INFO

echo.
echo 環境配置:
echo   API: %REDPACKET_API_URL%
echo   策略: %GAME_STRATEGY%
echo   自動搶紅包: %AUTO_GRAB%
echo   智能聊天: %AUTO_CHAT%
echo.

echo 啟動系統...
echo.

python admin-backend\start_full_system.py

echo.
pause
