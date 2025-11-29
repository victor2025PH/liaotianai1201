# 完整自动执行和监控系统
# 启动测试，持续监控，自动修复，直到完成

$Server = "ubuntu@165.154.233.55"
$MaxChecks = 400  # 最多监控100分钟
$CheckInterval = 15  # 每15秒检查一次

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "完整自动执行和监控系统" -ForegroundColor Cyan
Write-Host "开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function Invoke-SSHWithOutput {
    param($Command)
    try {
        $result = ssh $Server $Command 2>&1
        return $result -join "`n"
    } catch {
        return "Error: $_"
    }
}

function Write-Status {
    param($Message, $Type = "Info")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $icons = @{"Success" = "✅"; "Error" = "❌"; "Warning" = "⚠️"; "Info" = "ℹ️"}
    $colors = @{"Success" = "Green"; "Error" = "Red"; "Warning" = "Yellow"; "Info" = "Cyan"}
    Write-Host "[$timestamp] $($icons[$Type]) $Message" -ForegroundColor $colors[$Type]
}

# 准备阶段
Write-Status "准备环境..." "Info"
Invoke-SSHWithOutput "cd ~/liaotian/saas-demo && git pull origin master > /dev/null 2>&1" | Out-Null
Invoke-SSHWithOutput "cd ~/liaotian/saas-demo && chmod +x *.sh 2>/dev/null || true" | Out-Null
Write-Status "环境准备完成" "Success"
Write-Host ""

# 检查后端
Write-Status "检查后端服务..." "Info"
$health = Invoke-SSHWithOutput "curl -s http://localhost:8000/health 2>&1"
if ($health -match "ok|status") {
    Write-Status "后端服务正常" "Success"
} else {
    Write-Status "后端服务未运行" "Error"
    Write-Status "请先启动后端服务" "Warning"
    exit 1
}
Write-Host ""

# 修复用户
Write-Status "准备测试用户..." "Info"
$fixCmd = "cd ~/liaotian/admin-backend && source .venv/bin/activate && export ADMIN_DEFAULT_PASSWORD=testpass123 && python reset_admin_user.py > /dev/null 2>&1"
Invoke-SSHWithOutput $fixCmd | Out-Null
Start-Sleep -Seconds 2
Write-Status "测试用户准备完成" "Success"
Write-Host ""

# 启动测试
Write-Status "启动测试执行..." "Info"
$startCmd = "cd ~/liaotian/saas-demo && nohup bash 直接执行并反馈.sh > ~/liaotian/test_logs/direct_exec.log 2>&1 & echo `$!"
$pidOutput = Invoke-SSHWithOutput $startCmd
Write-Status "测试已启动" "Success"
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "开始持续监控（每 $CheckInterval 秒检查）" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 持续监控
$iteration = 0
$lastLogSize = 0

while ($iteration -lt $MaxChecks) {
    $iteration++
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] 检查 #$iteration" -ForegroundColor Cyan
    
    # 读取日志文件
    $logFile = "~/liaotian/test_logs/direct_exec.log"
    $logContent = Invoke-SSHWithOutput "tail -100 $logFile 2>/dev/null || echo ''"
    
    if ($logContent) {
        $currentSize = $logContent.Length
        
        if ($currentSize -ne $lastLogSize) {
            # 显示新内容
            $newContent = if ($currentSize -gt $lastLogSize) {
                $logContent.Substring($lastLogSize)
            } else {
                $logContent
            }
            
            $lines = $newContent -split "`n"
            foreach ($line in $lines) {
                if ($line.Trim()) {
                    if ($line -match '✅|成功|通过|SUCCESS|完成') {
                        Write-Host "  $line" -ForegroundColor Green
                    } elseif ($line -match '❌|失败|错误|ERROR|FAILED') {
                        Write-Host "  $line" -ForegroundColor Red
                    } elseif ($line -match '⚠️|警告|WARNING') {
                        Write-Host "  $line" -ForegroundColor Yellow
                    } else {
                        Write-Host "  $line" -ForegroundColor Gray
                    }
                }
            }
            
            $lastLogSize = $currentSize
        }
        
        # 检查完成状态
        if ($logContent -match "所有任务完成|所有测试通过|✅.*成功|测试.*成功") {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Status "所有任务成功完成！" "Success"
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
            
            Write-Host "最终日志:"
            Write-Host "----------------------------------------"
            Write-Host $logContent
            Write-Host "----------------------------------------"
            
            exit 0
        }
        elseif ($logContent -match "测试失败|❌|错误|error|failed") {
            Write-Host ""
            Write-Host "检测到错误，尝试修复..." -ForegroundColor Yellow
            
            # 修复并重启
            Invoke-SSHWithOutput $fixCmd | Out-Null
            Start-Sleep -Seconds 2
            Invoke-SSHWithOutput $startCmd | Out-Null
            Start-Sleep -Seconds 5
            
            $lastLogSize = 0
            Write-Host ""
        }
    } else {
        Write-Host "  等待日志生成..." -ForegroundColor Gray
    }
    
    Write-Host ""
    Start-Sleep -Seconds $CheckInterval
}

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "达到最大检查次数" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

$finalLog = Invoke-SSHWithOutput "tail -100 $logFile 2>/dev/null"
if ($finalLog) {
    Write-Host "`n最终日志:"
    Write-Host $finalLog
}

exit 1
