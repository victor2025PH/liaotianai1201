# 本地监控服务器测试执行
# 持续检查直到所有任务完成

$Server = "ubuntu@165.154.233.55"
$MaxChecks = 120  # 最多检查30分钟
$CheckInterval = 15  # 每15秒检查一次

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "本地监控服务器测试系统" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "服务器: $Server" -ForegroundColor Gray
Write-Host "开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# 函数：执行SSH命令
function Invoke-SSHCommand {
    param($Command)
    try {
        $result = ssh $Server $Command 2>&1
        return $result -join "`n"
    } catch {
        return "Error: $_"
    }
}

# 准备阶段
Write-Host "[准备] 更新服务器代码..." -ForegroundColor Yellow
Invoke-SSHCommand "cd ~/liaotian/saas-demo && git pull origin master > /dev/null 2>&1" | Out-Null
Invoke-SSHCommand "cd ~/liaotian/saas-demo && chmod +x *.sh 2>/dev/null || true" | Out-Null
Write-Host "✅ 代码已更新" -ForegroundColor Green
Write-Host ""

# 检查后端服务
Write-Host "[检查] 后端服务..." -ForegroundColor Yellow
$health = Invoke-SSHCommand "curl -s http://localhost:8000/health 2>&1"
if ($health -match "ok|status") {
    Write-Host "✅ 后端服务正常" -ForegroundColor Green
} else {
    Write-Host "❌ 后端服务未运行" -ForegroundColor Red
    Write-Host "请先启动后端服务" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# 修复测试用户
Write-Host "[准备] 测试用户..." -ForegroundColor Yellow
Invoke-SSHCommand "cd ~/liaotian/admin-backend && source .venv/bin/activate && export ADMIN_DEFAULT_PASSWORD=testpass123 && python reset_admin_user.py > /dev/null 2>&1" | Out-Null
Start-Sleep -Seconds 2

$login = Invoke-SSHCommand "curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=admin@example.com&password=testpass123' 2>&1"
if ($login -match "access_token") {
    Write-Host "✅ 测试用户正常" -ForegroundColor Green
} else {
    Write-Host "❌ 测试用户登录失败" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 启动测试
Write-Host "[启动] 测试任务..." -ForegroundColor Yellow
$pidCheck = Invoke-SSHCommand "if [ -f ~/liaotian/test_logs/e2e_test.pid ]; then PID=`$(cat ~/liaotian/test_logs/e2e_test.pid); ps -p `$PID > /dev/null 2>&1 && echo 'RUNNING'; else echo 'NOT_RUNNING'; fi"

if ($pidCheck -notmatch "RUNNING") {
    Write-Host "启动新的测试..." -ForegroundColor Yellow
    Invoke-SSHCommand "cd ~/liaotian/saas-demo && nohup bash 简化执行-分步进行.sh > ~/liaotian/test_logs/ps_monitor.log 2>&1 &" | Out-Null
    Start-Sleep -Seconds 5
    Write-Host "✅ 测试已启动" -ForegroundColor Green
} else {
    Write-Host "✅ 测试已在运行" -ForegroundColor Green
}
Write-Host ""

# 持续监控
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "开始持续监控（每 $CheckInterval 秒检查一次）" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$checkCount = 0

while ($checkCount -lt $MaxChecks) {
    $checkCount++
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[检查 $checkCount] $timestamp" -ForegroundColor Cyan
    
    # 获取最新日志
    $logFile = Invoke-SSHCommand "ls -t ~/liaotian/test_logs/*.log 2>/dev/null | head -1"
    $logFile = $logFile.Trim()
    
    if ($logFile) {
        $logContent = Invoke-SSHCommand "tail -100 '$logFile' 2>/dev/null"
        
        if ($logContent -match "所有任务成功完成|所有测试通过|✅.*成功") {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "✅ 所有任务成功完成！" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
            
            Write-Host "最终日志摘要:" -ForegroundColor Yellow
            Write-Host "----------------------------------------" -ForegroundColor Gray
            $finalLog = Invoke-SSHCommand "tail -50 '$logFile' 2>/dev/null"
            Write-Host $finalLog
            Write-Host "----------------------------------------" -ForegroundColor Gray
            
            exit 0
        }
        elseif ($logContent -match "测试失败|❌|错误|error|failed") {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Red
            Write-Host "❌ 测试失败" -ForegroundColor Red
            Write-Host "========================================" -ForegroundColor Red
            Write-Host ""
            
            Write-Host "错误信息:" -ForegroundColor Yellow
            $errors = $logContent -split "`n" | Where-Object { $_ -match "error|失败|错误|failed" } | Select-Object -Last 10
            foreach ($err in $errors) {
                Write-Host "  $err" -ForegroundColor Red
            }
            
            # 尝试修复
            Write-Host ""
            Write-Host "[修复] 尝试修复问题..." -ForegroundColor Yellow
            Invoke-SSHCommand "cd ~/liaotian/admin-backend && source .venv/bin/activate && export ADMIN_DEFAULT_PASSWORD=testpass123 && python reset_admin_user.py > /dev/null 2>&1" | Out-Null
            Start-Sleep -Seconds 2
            
            Write-Host "[重启] 重新启动测试..." -ForegroundColor Yellow
            Invoke-SSHCommand "cd ~/liaotian/saas-demo && nohup bash 简化执行-分步进行.sh > ~/liaotian/test_logs/ps_monitor.log 2>&1 &" | Out-Null
            Start-Sleep -Seconds 5
        }
        else {
            $lastLine = ($logContent -split "`n")[-1]
            if ($lastLine) {
                Write-Host "  进度: $($lastLine.Substring(0, [Math]::Min(60, $lastLine.Length)))" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "  等待日志文件..." -ForegroundColor Gray
    }
    
    Write-Host ""
    Start-Sleep -Seconds $CheckInterval
}

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "⚠️  达到最大检查次数" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

$finalLog = Invoke-SSHCommand "ls -t ~/liaotian/test_logs/*.log 2>/dev/null | head -1"
if ($finalLog) {
    Write-Host "`n请查看日志: $($finalLog.Trim())" -ForegroundColor Yellow
    Write-Host "`n最后30行:" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    $logContent = Invoke-SSHCommand "tail -30 '$($finalLog.Trim())' 2>/dev/null"
    Write-Host $logContent
}

exit 1
