# 实时监控账号管理功能日志
# 专门监控扫描账号相关的日志

$ErrorActionPreference = "Continue"

Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "📊 实时监控账号管理功能日志" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# 获取运行中的Job
$backendJob = Get-Job | Where-Object {$_.Name -eq "BackendService" -and $_.State -eq "Running"} | Select-Object -First 1
$frontendJob = Get-Job | Where-Object {$_.Name -eq "FrontendService" -and $_.State -eq "Running"} | Select-Object -First 1

if (-not $backendJob) {
    Write-Host "❌ 未找到运行中的后端服务" -ForegroundColor Red
    exit 1
}

if (-not $frontendJob) {
    Write-Host "⚠️  未找到运行中的前端服务" -ForegroundColor Yellow
}

Write-Host "✅ 找到后端服务 (Job ID: $($backendJob.Id))" -ForegroundColor Green
if ($frontendJob) {
    Write-Host "✅ 找到前端服务 (Job ID: $($frontendJob.Id))" -ForegroundColor Green
}

Write-Host "`n💡 监控重点:" -ForegroundColor Yellow
Write-Host "   - 扫描服务器账号相关日志" -ForegroundColor Gray
Write-Host "   - 账号ID提取相关日志" -ForegroundColor Gray
Write-Host "   - API调用相关日志" -ForegroundColor Gray
Write-Host "   - 前端获取账号数据相关日志" -ForegroundColor Gray
Write-Host "`n按 Ctrl+C 停止监控`n" -ForegroundColor Yellow

$backendLogCount = 0
$frontendLogCount = 0

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
                        if ($line -match "扫描服务器|scan.*account|找到.*账号|账号ID|extract_account|scan-server-accounts") {
                            Write-Host "[$timestamp] [后端] " -ForegroundColor Yellow -NoNewline
                            Write-Host $line -ForegroundColor Cyan
                        } elseif ($line -match "ERROR|错误|失败|Failed") {
                            Write-Host "[$timestamp] [后端] " -ForegroundColor Yellow -NoNewline
                            Write-Host $line -ForegroundColor Red
                        } elseif ($line -match "INFO.*account|INFO.*扫描") {
                            Write-Host "[$timestamp] [后端] " -ForegroundColor Yellow -NoNewline
                            Write-Host $line -ForegroundColor Green
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
                        if ($line -match "獲取到的服務器賬號數據|scanServerAccounts|account.*data") {
                            Write-Host "[$timestamp] [前端] " -ForegroundColor Magenta -NoNewline
                            Write-Host $line -ForegroundColor Cyan
                        } elseif ($line -match "ERROR|错误|404|500") {
                            Write-Host "[$timestamp] [前端] " -ForegroundColor Magenta -NoNewline
                            Write-Host $line -ForegroundColor Red
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
    Write-Host "`n✅ 监控已停止" -ForegroundColor Green
}

