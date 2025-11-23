# 重启所有服务并监控日志
# 使用方法: .\scripts\restart_and_monitor.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  重启所有服务并监控日志" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 获取项目根目录
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "admin-backend"
$frontendDir = Join-Path $projectRoot "saas-demo"

# 停止现有服务
Write-Host "停止现有服务..." -ForegroundColor Yellow

# 停止占用8000端口的进程
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($port8000) {
    foreach ($pid in $port8000) {
        try {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Write-Host "  已停止进程 $pid (端口 8000)" -ForegroundColor Green
        } catch {
            Write-Host "  无法停止进程 $pid" -ForegroundColor Yellow
        }
    }
}

# 停止占用3000端口的进程
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($port3000) {
    foreach ($pid in $port3000) {
        try {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Write-Host "  已停止进程 $pid (端口 3000)" -ForegroundColor Green
        } catch {
            Write-Host "  无法停止进程 $pid" -ForegroundColor Yellow
        }
    }
}

# 等待端口释放
Start-Sleep -Seconds 2

# 检查依赖
Write-Host "`n检查依赖..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [错误] Python 未安装" -ForegroundColor Red
    exit 1
}

try {
    $nodeVersion = node --version
    Write-Host "  Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  [错误] Node.js 未安装" -ForegroundColor Red
    exit 1
}

# 启动后端服务
Write-Host "`n启动后端服务..." -ForegroundColor Yellow
$backendLogFile = Join-Path $projectRoot "logs" "backend_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
New-Item -ItemType Directory -Path (Split-Path $backendLogFile) -Force | Out-Null

$backendJob = Start-Job -ScriptBlock {
    param($backendDir, $logFile)
    Set-Location $backendDir
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload *> $logFile
} -ArgumentList $backendDir, $backendLogFile

Write-Host "  后端服务启动中... (Job ID: $($backendJob.Id))" -ForegroundColor Green
Write-Host "  日志文件: $backendLogFile" -ForegroundColor Gray

# 等待后端启动
Start-Sleep -Seconds 5

# 检查后端健康状态
$backendOk = $false
for ($i = 0; $i -lt 10; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        $backendOk = $true
        Write-Host "  [OK] 后端服务已启动: http://localhost:8000" -ForegroundColor Green
        break
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $backendOk) {
    Write-Host "  [警告] 后端服务可能启动失败，请检查日志" -ForegroundColor Yellow
    Write-Host "  查看日志: Get-Content $backendLogFile -Tail 50" -ForegroundColor Gray
}

# 启动前端服务
Write-Host "`n启动前端服务..." -ForegroundColor Yellow
$frontendLogFile = Join-Path $projectRoot "logs" "frontend_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
New-Item -ItemType Directory -Path (Split-Path $frontendLogFile) -Force | Out-Null

$frontendJob = Start-Job -ScriptBlock {
    param($frontendDir, $logFile)
    Set-Location $frontendDir
    $env:PORT = "3000"
    npm run dev *> $logFile
} -ArgumentList $frontendDir, $frontendLogFile

Write-Host "  前端服务启动中... (Job ID: $($frontendJob.Id))" -ForegroundColor Green
Write-Host "  日志文件: $frontendLogFile" -ForegroundColor Gray

# 等待前端启动
Start-Sleep -Seconds 5

# 检查前端健康状态
$frontendOk = $false
for ($i = 0; $i -lt 10; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        $frontendOk = $true
        Write-Host "  [OK] 前端服务已启动: http://localhost:3000" -ForegroundColor Green
        break
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $frontendOk) {
    Write-Host "  [警告] 前端服务可能启动失败，请检查日志" -ForegroundColor Yellow
    Write-Host "  查看日志: Get-Content $frontendLogFile -Tail 50" -ForegroundColor Gray
}

# 监控日志
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  服务启动完成，开始监控日志" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "后端 API:  http://localhost:8000" -ForegroundColor White
Write-Host "前端界面: http://localhost:3000" -ForegroundColor White
Write-Host "API 文档: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "监控日志文件:" -ForegroundColor Yellow
Write-Host "  后端: $backendLogFile" -ForegroundColor Gray
Write-Host "  前端: $frontendLogFile" -ForegroundColor Gray
Write-Host ""
Write-Host "按 Ctrl+C 停止监控（服务将继续运行）" -ForegroundColor Yellow
Write-Host ""

# 实时监控日志
$errorCount = 0
$lastBackendSize = 0
$lastFrontendSize = 0

try {
    while ($true) {
        # 监控后端日志
        if (Test-Path $backendLogFile) {
            $currentSize = (Get-Item $backendLogFile).Length
            if ($currentSize -gt $lastBackendSize) {
                $newLines = Get-Content $backendLogFile -Tail 10 | Select-Object -Skip ([Math]::Max(0, (Get-Content $backendLogFile).Count - 10))
                foreach ($line in $newLines) {
                    $timestamp = Get-Date -Format "HH:mm:ss"
                    if ($line -match "error|exception|traceback|failed|失败" -and $line -notmatch "INFO") {
                        Write-Host "[$timestamp] [后端] ❌ $line" -ForegroundColor Red
                        $errorCount++
                    } elseif ($line -match "started|uvicorn running|application startup") {
                        Write-Host "[$timestamp] [后端] ✅ $line" -ForegroundColor Green
                    } elseif ($line -match "INFO|WARNING") {
                        Write-Host "[$timestamp] [后端] $line" -ForegroundColor Gray
                    }
                }
                $lastBackendSize = $currentSize
            }
        }
        
        # 监控前端日志
        if (Test-Path $frontendLogFile) {
            $currentSize = (Get-Item $frontendLogFile).Length
            if ($currentSize -gt $lastFrontendSize) {
                $newLines = Get-Content $frontendLogFile -Tail 10 | Select-Object -Skip ([Math]::Max(0, (Get-Content $frontendLogFile).Count - 10))
                foreach ($line in $newLines) {
                    $timestamp = Get-Date -Format "HH:mm:ss"
                    if ($line -match "error|failed|失败|cannot|missing|not found") {
                        Write-Host "[$timestamp] [前端] ❌ $line" -ForegroundColor Red
                        $errorCount++
                    } elseif ($line -match "ready|compiled|Local:") {
                        Write-Host "[$timestamp] [前端] ✅ $line" -ForegroundColor Green
                    }
                }
                $lastFrontendSize = $currentSize
            }
        }
        
        # 检查服务状态
        if ($backendJob.State -eq "Failed" -or $frontendJob.State -eq "Failed") {
            Write-Host "`n[警告] 检测到服务失败" -ForegroundColor Red
            if ($backendJob.State -eq "Failed") {
                Write-Host "  后端服务失败，查看日志: Get-Content $backendLogFile -Tail 50" -ForegroundColor Yellow
            }
            if ($frontendJob.State -eq "Failed") {
                Write-Host "  前端服务失败，查看日志: Get-Content $frontendLogFile -Tail 50" -ForegroundColor Yellow
            }
        }
        
        Start-Sleep -Seconds 2
    }
} catch {
    Write-Host "`n监控中断: $_" -ForegroundColor Yellow
} finally {
    Write-Host "`n监控已停止" -ForegroundColor Yellow
    Write-Host "服务仍在后台运行，使用以下命令停止:" -ForegroundColor Yellow
    Write-Host "  Stop-Job -Id $($backendJob.Id),$($frontendJob.Id)" -ForegroundColor Gray
    Write-Host "  Remove-Job -Id $($backendJob.Id),$($frontendJob.Id)" -ForegroundColor Gray
}

