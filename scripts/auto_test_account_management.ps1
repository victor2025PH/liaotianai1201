# 全自动测试账号管理功能
# 启动服务、监控日志、测试功能

$ErrorActionPreference = "Continue"

$projectRoot = "E:\002-工作文件\重要程序\聊天AI群聊程序"
$backendDir = Join-Path $projectRoot "admin-backend"
$frontendDir = Join-Path $projectRoot "saas-demo"

Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🚀 全自动测试账号管理功能" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# 1. 停止现有服务
Write-Host "`n[1/6] 停止现有服务..." -ForegroundColor Yellow
Get-Process | Where-Object {
    ($_.ProcessName -eq "python" -or $_.ProcessName -eq "node") -and
    ($_.Path -like "*$projectRoot*")
} | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Job | Where-Object {$_.Name -like "*Backend*" -or $_.Name -like "*Frontend*"} | Stop-Job -ErrorAction SilentlyContinue
Get-Job | Remove-Job -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "   ✅ 已停止" -ForegroundColor Green

# 2. 启动后端服务
Write-Host "`n[2/6] 启动后端服务..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    param($backendDir)
    Set-Location $backendDir
    $env:PYTHONUNBUFFERED = "1"
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 2>&1
} -ArgumentList $backendDir -Name "BackendService"
Write-Host "   ✅ 后端服务已启动 (Job ID: $($backendJob.Id))" -ForegroundColor Green

# 3. 启动前端服务
Write-Host "`n[3/6] 启动前端服务..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
$frontendJob = Start-Job -ScriptBlock {
    param($frontendDir)
    Set-Location $frontendDir
    $env:NODE_ENV = "development"
    npm run dev 2>&1
} -ArgumentList $frontendDir -Name "FrontendService"
Write-Host "   ✅ 前端服务已启动 (Job ID: $($frontendJob.Id))" -ForegroundColor Green

# 4. 等待服务启动
Write-Host "`n[4/6] 等待服务启动（15秒）..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 5. 检查服务状态
Write-Host "`n[5/6] 检查服务状态..." -ForegroundColor Yellow
$backendOk = $false
$frontendOk = $false

for ($i = 0; $i -lt 10; $i++) {
    try {
        $backendHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
        if ($backendHealth.status -eq "healthy") {
            $backendOk = $true
            Write-Host "   ✅ 后端服务正常" -ForegroundColor Green
            break
        }
    } catch {
        if ($i -eq 9) {
            Write-Host "   ❌ 后端服务未响应: $($_.Exception.Message)" -ForegroundColor Red
        } else {
            Start-Sleep -Seconds 2
        }
    }
}

for ($i = 0; $i -lt 10; $i++) {
    try {
        $frontendCheck = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -ErrorAction Stop
        if ($frontendCheck.StatusCode -eq 200) {
            $frontendOk = $true
            Write-Host "   ✅ 前端服务正常" -ForegroundColor Green
            break
        }
    } catch {
        if ($i -eq 9) {
            Write-Host "   ❌ 前端服务未响应: $($_.Exception.Message)" -ForegroundColor Red
        } else {
            Start-Sleep -Seconds 2
        }
    }
}

# 6. 测试账号管理API
Write-Host "`n[6/6] 测试账号管理API..." -ForegroundColor Yellow

if ($backendOk) {
    # 获取认证token（需要先登录）
    Write-Host "   📝 注意: 需要先登录获取token才能测试API" -ForegroundColor Yellow
    Write-Host "   📝 请在浏览器中打开 http://localhost:3000 并登录" -ForegroundColor Yellow
    Write-Host "   📝 然后点击服务器管理 -> 账号管理按钮" -ForegroundColor Yellow
} else {
    Write-Host "   ⚠️  后端服务未就绪，跳过API测试" -ForegroundColor Yellow
}

# 显示实时日志
Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "📊 实时日志监控（按 Ctrl+C 停止）" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 提示:" -ForegroundColor Yellow
Write-Host "   - 后端日志: 查找 '扫描服务器' 相关日志" -ForegroundColor Gray
Write-Host "   - 前端日志: 查找 '獲取到的服務器賬號數據' 相关日志" -ForegroundColor Gray
Write-Host "   - 如果看到 '暫無賬號'，请查看后端日志中的扫描结果" -ForegroundColor Gray
Write-Host ""

$backendLogCount = 0
$frontendLogCount = 0

try {
    while ($true) {
        # 获取后端日志
        if ($backendJob) {
            $backendOutput = Receive-Job -Id $backendJob.Id -Keep
            if ($backendOutput -and $backendOutput.Count -gt $backendLogCount) {
                $newLines = $backendOutput[$backendLogCount..($backendOutput.Count - 1)]
                foreach ($line in $newLines) {
                    if ($line) {
                        $timestamp = Get-Date -Format "HH:mm:ss"
                        # 高亮显示扫描相关日志
                        if ($line -match "扫描|scan|account|賬號") {
                            Write-Host "[$timestamp] [后端] " -ForegroundColor Yellow -NoNewline
                            Write-Host $line -ForegroundColor Cyan
                        } else {
                            Write-Host "[$timestamp] [后端] " -ForegroundColor Yellow -NoNewline
                            Write-Host $line
                        }
                    }
                }
                $backendLogCount = $backendOutput.Count
            }
        }
        
        # 获取前端日志
        if ($frontendJob) {
            $frontendOutput = Receive-Job -Id $frontendJob.Id -Keep
            if ($frontendOutput -and $frontendOutput.Count -gt $frontendLogCount) {
                $newLines = $frontendOutput[$frontendLogCount..($frontendOutput.Count - 1)]
                foreach ($line in $newLines) {
                    if ($line) {
                        $timestamp = Get-Date -Format "HH:mm:ss"
                        # 高亮显示账号相关日志
                        if ($line -match "賬號|account|獲取到的服務器") {
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
    Write-Host "✅ 服务已停止" -ForegroundColor Green
}

