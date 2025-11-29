# 检查服务器测试状态
$Server = "ubuntu@165.154.233.55"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "检查服务器测试状态" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查后端服务
Write-Host "[1] 检查后端服务..." -ForegroundColor Yellow
$health = ssh $Server "curl -s http://localhost:8000/health 2>&1"
if ($health -match "ok|status") {
    Write-Host "✅ 后端服务正常" -ForegroundColor Green
} else {
    Write-Host "❌ 后端服务未运行" -ForegroundColor Red
}
Write-Host ""

# 检查日志文件
Write-Host "[2] 检查测试日志..." -ForegroundColor Yellow
$logFile = ssh $Server "ls -t ~/liaotian/test_logs/*.log 2>/dev/null | head -1"
$logFile = $logFile.Trim()

if ($logFile) {
    Write-Host "✅ 找到日志文件: $logFile" -ForegroundColor Green
    Write-Host ""
    Write-Host "最后 30 行:" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    $logContent = ssh $Server "tail -30 '$logFile' 2>/dev/null"
    Write-Host $logContent
    Write-Host "----------------------------------------" -ForegroundColor Gray
} else {
    Write-Host "❌ 日志文件不存在" -ForegroundColor Red
}
Write-Host ""

# 检查测试进程
Write-Host "[3] 检查测试进程..." -ForegroundColor Yellow
$pidStatus = ssh $Server "if [ -f ~/liaotian/test_logs/e2e_test.pid ]; then PID=`$(cat ~/liaotian/test_logs/e2e_test.pid); ps -p `$PID > /dev/null 2>&1 && echo 'RUNNING' || echo 'STOPPED'; else echo 'NOT_RUNNING'; fi"
$pidStatus = $pidStatus.Trim()

if ($pidStatus -eq "RUNNING") {
    Write-Host "✅ 测试正在运行" -ForegroundColor Green
} elseif ($pidStatus -eq "STOPPED") {
    Write-Host "⚠️  测试进程已停止" -ForegroundColor Yellow
} else {
    Write-Host "⚠️  没有运行中的测试进程" -ForegroundColor Yellow
}
