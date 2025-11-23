# 在 Cursor 终端中启动并监控前后端服务
# 所有日志都会在 Cursor 终端中实时显示

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$ErrorActionPreference = "Stop"

# 项目根目录
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "admin-backend"
$frontendDir = Join-Path $projectRoot "saas-demo"

Write-Host "`n🚀 在 Cursor 终端中启动服务..." -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray

# 停止现有服务
Write-Host "`n1️⃣ 停止现有服务..." -ForegroundColor Yellow
Get-Process | Where-Object {
    ($_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*") -and
    ($_.Path -like "*$projectRoot*" -or $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*npm*")
} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 启动后端服务（后台任务，但输出到终端）
if (-not $FrontendOnly) {
    Write-Host "`n2️⃣ 启动后端服务（后台任务）..." -ForegroundColor Yellow
    
    $backendJob = Start-Job -ScriptBlock {
        param($backendDir)
        Set-Location $backendDir
        $env:PYTHONUNBUFFERED = "1"
        python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 2>&1
    } -ArgumentList $backendDir
    
    Write-Host "   后端服务已启动（Job ID: $($backendJob.Id)）" -ForegroundColor Green
    Write-Host "   日志将实时显示在下方..." -ForegroundColor Gray
}

# 启动前端服务（后台任务，但输出到终端）
if (-not $BackendOnly) {
    Write-Host "`n3️⃣ 启动前端服务（后台任务）..." -ForegroundColor Yellow
    
    $frontendJob = Start-Job -ScriptBlock {
        param($frontendDir)
        Set-Location $frontendDir
        $env:NODE_ENV = "development"
        npm run dev 2>&1
    } -ArgumentList $frontendDir
    
    Write-Host "   前端服务已启动（Job ID: $($frontendJob.Id)）" -ForegroundColor Green
    Write-Host "   日志将实时显示在下方..." -ForegroundColor Gray
}

# 等待服务启动
Write-Host "`n⏳ 等待服务启动（10秒）..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 检查服务状态
Write-Host "`n4️⃣ 检查服务状态..." -ForegroundColor Yellow
if (-not $FrontendOnly) {
    try {
        $backendHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "   后端: ✅ $($backendHealth.status)" -ForegroundColor Green
    } catch {
        Write-Host "   后端: ❌ $($_.Exception.Message)" -ForegroundColor Red
    }
}

if (-not $BackendOnly) {
    try {
        $frontendCheck = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "   前端: ✅ HTTP $($frontendCheck.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "   前端: ❌ $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 实时监控日志
Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host "📊 实时日志监控（按 Ctrl+C 停止）" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

$lastBackendOutput = ""
$lastFrontendOutput = ""

try {
    while ($true) {
        # 获取后端日志
        if (-not $FrontendOnly -and $backendJob) {
            $backendOutput = Receive-Job -Id $backendJob.Id -Keep
            if ($backendOutput -and $backendOutput.Count -gt 0) {
                $newBackendOutput = $backendOutput | Select-Object -Last 5
                foreach ($line in $newBackendOutput) {
                    if ($line -and $line -ne $lastBackendOutput) {
                        $timestamp = Get-Date -Format "HH:mm:ss"
                        Write-Host "[$timestamp] [后端] " -ForegroundColor Yellow -NoNewline
                        Write-Host $line
                        $lastBackendOutput = $line
                    }
                }
            }
        }
        
        # 获取前端日志
        if (-not $BackendOnly -and $frontendJob) {
            $frontendOutput = Receive-Job -Id $frontendJob.Id -Keep
            if ($frontendOutput -and $frontendOutput.Count -gt 0) {
                $newFrontendOutput = $frontendOutput | Select-Object -Last 5
                foreach ($line in $newFrontendOutput) {
                    if ($line -and $line -ne $lastFrontendOutput) {
                        $timestamp = Get-Date -Format "HH:mm:ss"
                        Write-Host "[$timestamp] [前端] " -ForegroundColor Magenta -NoNewline
                        Write-Host $line
                        $lastFrontendOutput = $line
                    }
                }
            }
        }
        
        Start-Sleep -Milliseconds 500
    }
} catch {
    Write-Host "`n⚠️  监控中断: $($_.Exception.Message)" -ForegroundColor Yellow
} finally {
    Write-Host "`n🛑 正在停止服务..." -ForegroundColor Yellow
    if ($backendJob) {
        Stop-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
    }
    if ($frontendJob) {
        Stop-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
    }
    Write-Host "✅ 服务已停止" -ForegroundColor Green
}

