# 在Cursor终端中启动并监控前后端服务
# 所有日志都在Cursor终端中实时显示

$ErrorActionPreference = "Continue"

$projectRoot = "E:\002-工作文件\重要程序\聊天AI群聊程序"
$backendDir = Join-Path $projectRoot "admin-backend"
$frontendDir = Join-Path $projectRoot "saas-demo"

Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🚀 启动服务并实时监控（Cursor终端）" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# 1. 启动后端服务
Write-Host "`n[1/2] 启动后端服务..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    param($backendDir)
    Set-Location $backendDir
    $env:PYTHONUNBUFFERED = "1"
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 2>&1
} -ArgumentList $backendDir -Name "BackendService"

Write-Host "   ✅ 后端服务已启动 (Job ID: $($backendJob.Id))" -ForegroundColor Green
Write-Host "   地址: http://localhost:8000" -ForegroundColor Gray

# 2. 启动前端服务
Write-Host "`n[2/2] 启动前端服务..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
$frontendJob = Start-Job -ScriptBlock {
    param($frontendDir)
    Set-Location $frontendDir
    $env:NODE_ENV = "development"
    npm run dev 2>&1
} -ArgumentList $frontendDir -Name "FrontendService"

Write-Host "   ✅ 前端服务已启动 (Job ID: $($frontendJob.Id))" -ForegroundColor Green
Write-Host "   地址: http://localhost:3000" -ForegroundColor Gray

# 3. 等待服务启动
Write-Host "`n⏳ 等待服务启动（15秒）..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 4. 检查服务状态
Write-Host "`n🔍 检查服务状态..." -ForegroundColor Cyan
$backendOk = $false
$frontendOk = $false

for ($i = 0; $i -lt 5; $i++) {
    try {
        $backendHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 3 -ErrorAction Stop
        if ($backendHealth.status -eq "ok") {
            $backendOk = $true
            Write-Host "   ✅ 后端服务正常" -ForegroundColor Green
            break
        }
    } catch {
        if ($i -eq 4) {
            Write-Host "   ⚠️  后端服务可能还在启动中" -ForegroundColor Yellow
        } else {
            Start-Sleep -Seconds 2
        }
    }
}

for ($i = 0; $i -lt 5; $i++) {
    try {
        $frontendCheck = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        if ($frontendCheck.StatusCode -eq 200) {
            $frontendOk = $true
            Write-Host "   ✅ 前端服务正常" -ForegroundColor Green
            break
        }
    } catch {
        if ($i -eq 4) {
            Write-Host "   ⚠️  前端服务可能还在启动中" -ForegroundColor Yellow
        } else {
            Start-Sleep -Seconds 2
        }
    }
}

# 5. 实时监控日志
Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "📊 实时日志监控（按 Ctrl+C 停止）" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

$backendLogCount = 0
$frontendLogCount = 0
$errorCount = 0
$errors = @()

try {
    while ($true) {
        # 监控后端日志
        if ($backendJob) {
            $backendOutput = Receive-Job -Id $backendJob.Id -Keep
            if ($backendOutput -and $backendOutput.Count -gt $backendLogCount) {
                $newLines = $backendOutput[$backendLogCount..($backendOutput.Count - 1)]
                foreach ($line in $newLines) {
                    if ($line) {
                        $timestamp = Get-Date -Format "HH:mm:ss"
                        # 高亮显示关键日志
                        if ($line -match "ERROR|错误|Exception|Traceback|Failed") {
                            Write-Host "[$timestamp] [后端] " -ForegroundColor Yellow -NoNewline
                            Write-Host $line -ForegroundColor Red
                            $errorCount++
                            $errors += "[后端] $line"
                        } elseif ($line -match "扫描服务器|scan.*account|找到.*账号|账号ID") {
                            Write-Host "[$timestamp] [后端] " -ForegroundColor Yellow -NoNewline
                            Write-Host $line -ForegroundColor Cyan
                        } elseif ($line -match "INFO|启动|ready|Running") {
                            Write-Host "[$timestamp] [后端] " -ForegroundColor Yellow -NoNewline
                            Write-Host $line -ForegroundColor Green
                        } else {
                            Write-Host "[$timestamp] [后端] " -ForegroundColor Yellow -NoNewline
                            Write-Host $line
                        }
                    }
                }
                $backendLogCount = $backendOutput.Count
            }
        }
        
        # 监控前端日志
        if ($frontendJob) {
            $frontendOutput = Receive-Job -Id $frontendJob.Id -Keep
            if ($frontendOutput -and $frontendOutput.Count -gt $frontendLogCount) {
                $newLines = $frontendOutput[$frontendLogCount..($frontendOutput.Count - 1)]
                foreach ($line in $newLines) {
                    if ($line) {
                        $timestamp = Get-Date -Format "HH:mm:ss"
                        # 高亮显示关键日志
                        if ($line -match "ERROR|错误|404|500|Failed") {
                            Write-Host "[$timestamp] [前端] " -ForegroundColor Magenta -NoNewline
                            Write-Host $line -ForegroundColor Red
                            $errorCount++
                            $errors += "[前端] $line"
                        } elseif ($line -match "Ready|compiled|account|賬號") {
                            Write-Host "[$timestamp] [前端] " -ForegroundColor Magenta -NoNewline
                            Write-Host $line -ForegroundColor Cyan
                        } else {
                            Write-Host "[$timestamp] [前端] " -ForegroundColor Magenta -NoNewline
                            Write-Host $line
                        }
                    }
                }
                $frontendLogCount = $frontendOutput.Count
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
    
    Write-Host "`n📊 错误统计:" -ForegroundColor Cyan
    Write-Host "   总错误数: $errorCount" -ForegroundColor $(if ($errorCount -eq 0) { "Green" } else { "Red" })
    if ($errors.Count -gt 0) {
        Write-Host "`n   错误列表:" -ForegroundColor Yellow
        $errors | Select-Object -Last 10 | ForEach-Object {
            Write-Host "      $_" -ForegroundColor Gray
        }
    }
    
    Write-Host "`n✅ 服务已停止" -ForegroundColor Green
}

