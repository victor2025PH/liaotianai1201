# 完整業務自動化系統啟動腳本
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  🚀 完整業務自動化系統" -ForegroundColor Green
Write-Host "  功能: LLM對話 | 多群組 | 紅包遊戲 | 實時監控 | 數據分析" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# 切換到腳本目錄
Set-Location $PSScriptRoot

# 激活虛擬環境
& "$PSScriptRoot\..\\.venv\Scripts\Activate.ps1"

# 設置環境變量
$env:REDPACKET_API_URL = "https://api.usdt2026.cc"
$env:REDPACKET_API_KEY = "test-key-2024"
$env:GAME_STRATEGY = "smart"
$env:AUTO_GRAB = "true"
$env:AUTO_SEND = "false"
$env:AUTO_CHAT = "true"
$env:LOG_LEVEL = "INFO"

Write-Host "環境變量已設置:" -ForegroundColor Yellow
Write-Host "  API_URL: $env:REDPACKET_API_URL"
Write-Host "  策略: $env:GAME_STRATEGY"
Write-Host "  自動搶: $env:AUTO_GRAB"
Write-Host "  自動發: $env:AUTO_SEND"
Write-Host ""

# 運行系統
python start_full_system.py
