# 监控服务状态的脚本
# 使用方法: .\scripts\monitor_services.ps1

param(
    [int]$Interval = 10,  # 检查间隔（秒）
    [int]$Duration = 60    # 监控时长（秒）
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$startTime = Get-Date
$endTime = $startTime.AddSeconds($Duration)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "服务状态监控" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "监控间隔: $Interval 秒" -ForegroundColor Gray
Write-Host "监控时长: $Duration 秒" -ForegroundColor Gray
Write-Host "按 Ctrl+C 可以提前停止" -ForegroundColor Yellow
Write-Host ""

$checkCount = 0

while ((Get-Date) -lt $endTime) {
    $checkCount++
    $currentTime = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[检查 #$checkCount] $currentTime" -ForegroundColor Cyan
    
    # 检查后端服务
    $port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    $backendJobs = Get-Job | Where-Object { $_.Command -like "*uvicorn*" }
    
    Write-Host "  后端服务: " -NoNewline
    if ($port8000) {
        Write-Host "✅ 运行中 (端口 8000)" -ForegroundColor Green
        try {
            $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
            Write-Host "    健康检查: $($health.status)" -ForegroundColor Gray
        } catch {
            Write-Host "    ⚠ 健康检查失败" -ForegroundColor Yellow
        }
    } elseif ($backendJobs -and ($backendJobs | Where-Object { $_.State -eq 'Running' })) {
        Write-Host "⏳ 启动中..." -ForegroundColor Yellow
    } else {
        Write-Host "❌ 已停止" -ForegroundColor Red
    }
    
    # 检查前端服务
    $port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
    $port3001 = Get-NetTCPConnection -LocalPort 3001 -ErrorAction SilentlyContinue
    $frontendJobs = Get-Job | Where-Object { $_.Command -like "*npm run dev*" -or $_.Command -like "*next dev*" }
    
    Write-Host "  前端服务: " -NoNewline
    if ($port3000) {
        Write-Host "✅ 运行中 (端口 3000)" -ForegroundColor Green
    } elseif ($port3001) {
        Write-Host "✅ 运行中 (端口 3001)" -ForegroundColor Green
    } elseif ($frontendJobs -and ($frontendJobs | Where-Object { $_.State -eq 'Running' })) {
        Write-Host "⏳ 启动中..." -ForegroundColor Yellow
    } else {
        Write-Host "❌ 已停止" -ForegroundColor Red
    }
    
    Write-Host ""
    
    Start-Sleep -Seconds $Interval
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "监控完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
