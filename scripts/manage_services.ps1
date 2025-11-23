# 服务管理脚本
# 使用方法: .\scripts\manage_services.ps1 [start|stop|status|restart]

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "status", "restart", "logs")]
    [string]$Action = "status"
)

$projectRoot = Split-Path -Parent $PSScriptRoot

function Get-ServiceJobs {
    Get-Job | Where-Object { 
        $_.Command -like "*uvicorn*" -or 
        $_.Command -like "*npm run dev*" -or 
        $_.Command -like "*next dev*" 
    }
}

function Start-Services {
    Write-Host "启动所有服务..." -ForegroundColor Cyan
    
    # 启动后端
    $backendLog = "$projectRoot\logs\backend-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
    $backendJob = Start-Job -ScriptBlock {
        Set-Location "$using:projectRoot\admin-backend"
        python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 *> "..\$using:backendLog" 2>&1
    }
    Write-Host "  ✓ 后端服务已启动 (Job ID: $($backendJob.Id))" -ForegroundColor Green
    
    # 启动前端（使用更可靠的方法）
    Start-Sleep -Seconds 3
    $frontendLog = "$projectRoot\logs\frontend-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
    $frontendScript = @"
Set-Location "$projectRoot\saas-demo"
npm run dev 2>&1 | Tee-Object -FilePath "$frontendLog"
"@
    $frontendScript | Out-File -FilePath "$env:TEMP\start-frontend.ps1" -Encoding UTF8
    $frontendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "& '$env:TEMP\start-frontend.ps1'" -WindowStyle Hidden -PassThru
    Write-Host "  ✓ 前端服务已启动 (PID: $($frontendProcess.Id))" -ForegroundColor Green
    
    Write-Host "`n等待服务启动（15秒）..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    Show-Status
}

function Stop-Services {
    Write-Host "停止所有服务..." -ForegroundColor Cyan
    
    # 停止后台任务
    Get-ServiceJobs | Stop-Job -ErrorAction SilentlyContinue
    Get-ServiceJobs | Remove-Job -ErrorAction SilentlyContinue
    
    # 停止后端进程
    Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object { 
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)" -ErrorAction SilentlyContinue).CommandLine
            $cmdLine -like "*uvicorn*"
        } catch {
            $false
        }
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # 停止前端进程
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { 
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)" -ErrorAction SilentlyContinue).CommandLine
            $cmdLine -like "*next*" -or $cmdLine -like "*npm*"
        } catch {
            $false
        }
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "  ✓ 所有服务已停止" -ForegroundColor Green
}

function Show-Status {
    Write-Host "`n服务状态:" -ForegroundColor Cyan
    
    $port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    $port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
    $port3001 = Get-NetTCPConnection -LocalPort 3001 -ErrorAction SilentlyContinue
    
    Write-Host "`n后端服务:" -ForegroundColor Yellow
    if ($port8000) {
        Write-Host "  ✅ 运行中 (端口 8000)" -ForegroundColor Green
        try {
            $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 2
            Write-Host "  ✅ 健康检查: $($health.status)" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠ 健康检查失败" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ❌ 未运行" -ForegroundColor Red
    }
    
    Write-Host "`n前端服务:" -ForegroundColor Yellow
    if ($port3000) {
        Write-Host "  ✅ 运行中 (端口 3000)" -ForegroundColor Green
    } elseif ($port3001) {
        Write-Host "  ✅ 运行中 (端口 3001)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 未运行" -ForegroundColor Red
    }
    
    Write-Host "`n后台任务:" -ForegroundColor Yellow
    $jobs = Get-ServiceJobs
    if ($jobs) {
        $jobs | ForEach-Object {
            Write-Host "  • Job $($_.Id): $($_.State)" -ForegroundColor $(if ($_.State -eq 'Running') { 'Green' } else { 'Red' })
        }
    } else {
        Write-Host "  没有运行中的后台任务" -ForegroundColor Gray
    }
}

function Show-Logs {
    Write-Host "`n查看服务日志..." -ForegroundColor Cyan
    
    $backendLogs = Get-ChildItem "$projectRoot\logs\backend-*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $frontendLogs = Get-ChildItem "$projectRoot\logs\frontend-*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    
    if ($backendLogs) {
        Write-Host "`n后端服务日志 (最后20行):" -ForegroundColor Yellow
        Get-Content $backendLogs[0].FullName -Tail 20
    }
    
    if ($frontendLogs) {
        Write-Host "`n前端服务日志 (最后20行):" -ForegroundColor Yellow
        Get-Content $frontendLogs[0].FullName -Tail 20
    }
}

switch ($Action) {
    "start" { Start-Services }
    "stop" { Stop-Services }
    "status" { Show-Status }
    "restart" { Stop-Services; Start-Sleep -Seconds 2; Start-Services }
    "logs" { Show-Logs }
}
