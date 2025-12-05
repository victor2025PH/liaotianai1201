@echo off
chcp 65001 >nul
title 網絡連接測試
color 0E

echo.
echo ============================================================
echo   🌐 網絡連接測試
echo ============================================================
echo.

echo 1. 測試 DNS 解析...
nslookup api.usdt2026.cc
echo.

echo 2. 測試 Ping...
ping api.usdt2026.cc -n 3
echo.

echo 3. 測試 HTTPS 連接...
curl -v https://api.usdt2026.cc/api/v2/ai/status --connect-timeout 10 2>&1
echo.

echo 4. 測試 AI 帳號餘額...
curl -s "https://api.usdt2026.cc/api/v2/ai/wallet/balance" -H "Authorization: Bearer test-key-2024" -H "X-Telegram-User-Id: 639277358115"
echo.

echo.
echo ============================================================
echo   測試完成
echo ============================================================
echo.
pause
