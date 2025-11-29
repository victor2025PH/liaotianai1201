# 完整自动监控系统 - PowerShell版本
# 实时监控服务器测试执行，自动修复问题

$Server = "ubuntu@165.154.233.55"
$MaxIterations = 360  # 最多监控1小时
$CheckInterval = 10  # 每10秒检查一次

function Write-Status {
    param($Message, $Type = "Info")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $icons = @{
        "Success" = "✅"
        "Error" = "❌"
        "Warning" = "⚠️"
        "Info" = "ℹ️"
    }
    $colors = @{
        "Success" = "Green"
        "Error" = "Red"
        "Warning" = "Yellow"
        "Info" = "Cyan"
    }
    $icon = $icons[$Type]
    $color = $colors[$Type]
    Write-Host "[$timestamp] $icon $Message" -ForegroundColor $color
}

function Invoke-SSHCommand {
    param($Command, $Timeout = 30)
    try {
        $result = ssh $Server $Command 2>&1
        return $result -join "`n"
    } catch {
        return "Error: $_"
    }
}

function Get-StatusFile {
    $output = Invoke-SSHCommand "cat ~/liaotian/test_logs/current_status.txt 2>/dev/null || echo ''"
    return $output.Trim()
}

function Get-LatestLog {
    $output = Invoke-SSHCommand "ls -t ~/liaotian/test_logs/realtime_monitor_*.log 2>/dev/null | head -1"
    return $output.Trim()
}

function Get-LogTail {
    param($LogFile, $Lines = 50)
    if (-not $LogFile) { return $null }
    $output = Invoke-SSHCommand "tail -$Lines '$LogFile' 2>/dev/null"
    return $output
}

function Check-Backend {
    $output = Invoke-SSHCommand "curl -s --max-time 5 http://localhost:8000/health 2>&1"
    return $output -match "ok|status"
}

function Fix-User {
    Write-Status "修复测试用户..." "Info"
    $cmd = "cd ~/liaotian/admin-backend && source .venv/bin/activate && export ADMIN_DEFAULT_PASSWORD=testpass123 && python reset_admin_user.py > /dev/null 2>&1"
    Invoke-SSHCommand $cmd | Out-Null
    Start-Sleep -Seconds 2
}

function Start-Monitor {
    Write-Status "启动实时监控执行..." "Info"
    $cmd = "cd ~/liaotian/saas-demo && nohup bash 服务器端实时监控执行.sh > /dev/null 2>&1 & echo `$!"
    $output = Invoke-SSHCommand $cmd
    if ($output -match '\d+') {
        Write-Status "监控脚本已启动" "Success"
        Start-Sleep -Seconds 5
        return $true
    }
    return $false
}

# 主程序
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "完整自动监控系统" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "服务器: $Server" -ForegroundColor Gray
Write-Host "开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# 准备
Write-Status "准备环境..." "Info"
Invoke-SSHCommand "cd ~/liaotian/saas-demo && git pull origin master > /dev/null 2>&1" | Out-Null
Invoke-SSHCommand "cd ~/liaotian/saas-demo && chmod +x *.sh 2>/dev/null || true" | Out-Null
Write-Status "环境准备完成" "Success"
Write-Host ""

# 检查后端
Write-Status "检查后端服务..." "Info"
if (-not (Check-Backend)) {
    Write-Status "后端服务未运行" "Error"
    Write-Status "请先启动后端服务" "Warning"
    exit 1
}
Write-Status "后端服务正常" "Success"
Write-Host ""

# 准备用户
Write-Status "准备测试用户..." "Info"
Fix-User
Write-Status "测试用户准备完成" "Success"
Write-Host ""

# 启动监控
Write-Status "启动实时监控执行系统..." "Info"
if (-not (Start-Monitor)) {
    Write-Status "无法启动监控脚本" "Error"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "开始实时监控（每 $CheckInterval 秒检查）" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 持续监控
$iteration = 0
$lastLogSize = 0
$lastLogFile = $null
$consecutiveErrors = 0

while ($iteration -lt $MaxIterations) {
    $iteration++
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    # 获取状态
    $status = Get-StatusFile
    if ($status) {
        Write-Host "[$timestamp] $status" -ForegroundColor Gray
    }
    
    # 获取日志文件
    $logFile = Get-LatestLog
    
    if ($logFile -and $logFile -ne $lastLogFile) {
        Write-Status "找到日志文件: $([System.IO.Path]::GetFileName($logFile))" "Info"
        $lastLogFile = $logFile
        $lastLogSize = 0
    }
    
    if ($logFile) {
        # 获取日志内容
        $logContent = Get-LogTail $logFile 100
        
        if ($logContent) {
            $lines = $logContent -split "`n"
            $newLines = $lines | Select-Object -Skip $lastLogSize
            
            foreach ($line in $newLines) {
                if ($line -and $line.Trim()) {
                    if ($line -match '✅|成功|通过|SUCCESS') {
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
            
            $lastLogSize = $lines.Count
            
            # 检查完成状态
            if ($logContent -match "所有任务成功完成|所有测试通过|✅.*成功") {
                Write-Host ""
                Write-Host "========================================" -ForegroundColor Green
                Write-Status "所有任务成功完成！" "Success"
                Write-Host "========================================" -ForegroundColor Green
                Write-Host ""
                
                $finalLog = Get-LogTail $logFile 50
                if ($finalLog) {
                    Write-Host "最终日志摘要:"
                    Write-Host "----------------------------------------"
                    Write-Host $finalLog
                    Write-Host "----------------------------------------"
                }
                
                exit 0
            }
            elseif ($logContent -match "测试失败|❌|错误|error|failed") {
                $consecutiveErrors++
                
                if ($consecutiveErrors -ge 3) {
                    Write-Host ""
                    Write-Host "========================================" -ForegroundColor Yellow
                    Write-Status "检测到错误，尝试修复..." "Warning"
                    Write-Host "========================================" -ForegroundColor Yellow
                    
                    Fix-User
                    Start-Sleep -Seconds 2
                    
                    Write-Status "重新启动监控..." "Info"
                    Invoke-SSHCommand "pkill -f '服务器端实时监控执行.sh' 2>/dev/null || true" | Out-Null
                    Start-Sleep -Seconds 2
                    Start-Monitor
                    
                    $consecutiveErrors = 0
                    $lastLogSize = 0
                    $lastLogFile = $null
                    Write-Host ""
                }
            } else {
                $consecutiveErrors = 0
            }
        }
    } else {
        Write-Host "  等待日志文件..." -ForegroundColor Gray
    }
    
    Write-Host ""
    Start-Sleep -Seconds $CheckInterval
}

Write-Host "========================================" -ForegroundColor Yellow
Write-Status "达到最大检查次数" "Warning"
Write-Host "========================================" -ForegroundColor Yellow

$finalLog = Get-LatestLog
if ($finalLog) {
    $content = Get-LogTail $finalLog 50
    if ($content) {
        Write-Host "`n最终日志:"
        Write-Host $content
    }
}

exit 1
