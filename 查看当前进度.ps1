# 立即查看当前进度

$Server = "ubuntu@165.154.233.55"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "当前进度报告" -ForegroundColor Cyan
Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function Invoke-SSH {
    param($Cmd)
    try {
        $result = ssh $Server $Cmd 2>&1
        return $result -join "`n"
    } catch {
        return ""
    }
}

# 检查后端服务
Write-Host "[1] 后端服务状态..." -ForegroundColor Cyan
$health = Invoke-SSH "curl -s http://localhost:8000/health 2>&1"
if ($health -match "ok|status") {
    Write-Host "  ✅ 后端服务正常运行" -ForegroundColor Green
} else {
    Write-Host "  ❌ 后端服务: $health" -ForegroundColor Red
}
Write-Host ""

# 检查进程
Write-Host "[2] 测试进程状态..." -ForegroundColor Cyan
$processes = Invoke-SSH "ps aux | grep -E '直接执行|playwright|test|服务器端实时监控' | grep -v grep"
if ($processes) {
    Write-Host "  ✅ 发现运行中的进程:" -ForegroundColor Green
    $processes -split "`n" | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
} else {
    Write-Host "  ⚠️  未发现测试进程" -ForegroundColor Yellow
}
Write-Host ""

# 检查日志
Write-Host "[3] 日志文件状态..." -ForegroundColor Cyan
$logFiles = Invoke-SSH "ls -lht ~/liaotian/test_logs/*.log 2>/dev/null | head -5"
if ($logFiles) {
    Write-Host "  📄 日志文件列表:" -ForegroundColor Gray
    $logFiles -split "`n" | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    
    $latestLog = Invoke-SSH "ls -t ~/liaotian/test_logs/*.log 2>/dev/null | head -1"
    if ($latestLog.Trim()) {
        Write-Host ""
        Write-Host "  📝 最新日志内容 (最后30行):" -ForegroundColor Cyan
        $logContent = Invoke-SSH "tail -30 '$($latestLog.Trim())' 2>/dev/null"
        if ($logContent) {
            $logContent -split "`n" | ForEach-Object {
                if ($_ -match '✅|成功|通过|SUCCESS') {
                    Write-Host "    $_" -ForegroundColor Green
                } elseif ($_ -match '❌|失败|错误|ERROR|FAILED') {
                    Write-Host "    $_" -ForegroundColor Red
                } elseif ($_ -match '⚠️|警告|WARNING') {
                    Write-Host "    $_" -ForegroundColor Yellow
                } else {
                    Write-Host "    $_" -ForegroundColor Gray
                }
            }
        }
    }
} else {
    Write-Host "  ⚠️  未找到日志文件" -ForegroundColor Yellow
}
Write-Host ""

# 检查状态文件
Write-Host "[4] 当前状态..." -ForegroundColor Cyan
$status = Invoke-SSH "cat ~/liaotian/test_logs/current_status.txt 2>/dev/null"
if ($status.Trim()) {
    Write-Host "  📋 状态: $($status.Trim())" -ForegroundColor Gray
} else {
    Write-Host "  ⚠️  状态文件不存在" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "报告完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
