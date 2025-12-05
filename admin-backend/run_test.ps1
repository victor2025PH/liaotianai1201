# 紅包 API 功能測試腳本
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  紅包 API 功能測試" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 切換到腳本目錄
Set-Location $PSScriptRoot

# 激活虛擬環境
& "$PSScriptRoot\..\\.venv\Scripts\Activate.ps1"

# 運行測試
python start_api_test.py

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  測試完成" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
