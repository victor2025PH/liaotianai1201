# 测试远程服务器的 session 文件是否能自动回复
param(
    [switch]$Detailed = $true
)

$ErrorActionPreference = "Continue"
Import-Module Posh-SSH

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  测试远程服务器的 Session 文件自动回复功能" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$servers = @(
    @{IP="165.154.255.48"; Name="洛杉矶"; Pass="8iDcGrYb52Fxpzee"},
    @{IP="165.154.233.179"; Name="马尼拉"; Pass="8iDcGrYb52Fxpzee"},
    @{IP="165.154.254.99"; Name="worker-01"; Pass="Along2025!!!"}
)

foreach ($s in $servers) {
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host "服务器: $($s.Name) ($($s.IP))" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    
    try {
        $pass = ConvertTo-SecureString $s.Pass -AsPlainText -Force
        $cred = New-Object System.Management.Automation.PSCredential("ubuntu", $pass)
        $session = New-SSHSession -ComputerName $s.IP -Credential $cred -AcceptKey -ErrorAction Stop
        
        Write-Host "✓ SSH 连接成功" -ForegroundColor Green
        Write-Host ""
        
        # 1. 检查 session 文件
        Write-Host "1. 检查 Session 文件..." -ForegroundColor Cyan
        $r1 = Invoke-SSHCommand -SessionId $session.SessionId -Command "find /home/ubuntu -name '*.session' -o -name '*.session.*' 2>/dev/null | head -20"
        if ($r1.Output) {
            Write-Host "  ✓ 找到 Session 文件:" -ForegroundColor Green
            $sessionFiles = $r1.Output -split "`n" | Where-Object { $_ -match "\.session" }
            foreach ($file in $sessionFiles) {
                $file = $file.Trim()
                if ($file) {
                    Write-Host "    - $file" -ForegroundColor Gray
                    # 检查文件大小
                    $sizeCmd = "ls -lh '$file' 2>/dev/null | awk '{print `$5}'"
                    $size = Invoke-SSHCommand -SessionId $session.SessionId -Command $sizeCmd
                    if ($size.Output) {
                        Write-Host "      大小: $($size.Output.Trim())" -ForegroundColor DarkGray
                    }
                }
            }
        } else {
            Write-Host "  ✗ 未找到 Session 文件" -ForegroundColor Red
        }
        Write-Host ""
        
        # 2. 检查 main.py 进程
        Write-Host "2. 检查 main.py 进程..." -ForegroundColor Cyan
        $r2 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ps aux | grep '[m]ain.py'"
        if ($r2.Output) {
            Write-Host "  ✓ main.py 正在运行" -ForegroundColor Green
            $processInfo = $r2.Output -split "`n" | Where-Object { $_ -match "main.py" }
            foreach ($proc in $processInfo) {
                Write-Host "    $proc" -ForegroundColor Gray
            }
        } else {
            Write-Host "  ✗ main.py 未运行" -ForegroundColor Red
            Write-Host "    尝试启动 main.py..." -ForegroundColor Yellow
            $startCmd = "cd /home/ubuntu && nohup python3 main.py > logs/main.log 2>&1 &"
            $r2a = Invoke-SSHCommand -SessionId $session.SessionId -Command $startCmd
            Start-Sleep -Seconds 3
            $r2b = Invoke-SSHCommand -SessionId $session.SessionId -Command "ps aux | grep '[m]ain.py'"
            if ($r2b.Output) {
                Write-Host "    ✓ main.py 已启动" -ForegroundColor Green
            } else {
                Write-Host "    ✗ main.py 启动失败" -ForegroundColor Red
            }
        }
        Write-Host ""
        
        # 3. 检查日志文件
        Write-Host "3. 检查日志文件..." -ForegroundColor Cyan
        $r3 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ls -lh /home/ubuntu/logs/*.log 2>/dev/null | head -10"
        if ($r3.Output) {
            Write-Host "  ✓ 找到日志文件:" -ForegroundColor Green
            $logFiles = $r3.Output -split "`n" | Where-Object { $_ -match "\.log" }
            foreach ($log in $logFiles) {
                $log = $log.Trim()
                if ($log) {
                    Write-Host "    - $log" -ForegroundColor Gray
                }
            }
        } else {
            Write-Host "  ✗ 未找到日志文件" -ForegroundColor Red
        }
        Write-Host ""
        
        # 4. 检查 Telegram 连接状态
        Write-Host "4. 检查 Telegram 连接状态..." -ForegroundColor Cyan
        $r4 = Invoke-SSHCommand -SessionId $session.SessionId -Command "grep -i 'connected\|ready\|started\|Client.*started' /home/ubuntu/logs/*.log 2>/dev/null | tail -10"
        if ($r4.Output) {
            Write-Host "  ✓ 找到连接记录:" -ForegroundColor Green
            Write-Host $r4.Output -ForegroundColor Gray
        } else {
            Write-Host "  ✗ 未找到连接记录" -ForegroundColor Red
        }
        Write-Host ""
        
        # 5. 检查最近的自动回复记录
        Write-Host "5. 检查最近的自动回复记录..." -ForegroundColor Cyan
        $r5 = Invoke-SSHCommand -SessionId $session.SessionId -Command "grep -i 'reply\|回复\|message.*sent\|发送' /home/ubuntu/logs/*.log 2>/dev/null | tail -10"
        if ($r5.Output) {
            Write-Host "  ✓ 找到回复记录:" -ForegroundColor Green
            Write-Host $r5.Output -ForegroundColor Gray
        } else {
            Write-Host "  ✗ 未找到回复记录" -ForegroundColor Yellow
            Write-Host "    (可能是新启动的服务，还没有回复记录)" -ForegroundColor DarkGray
        }
        Write-Host ""
        
        # 6. 检查错误日志
        Write-Host "6. 检查错误日志..." -ForegroundColor Cyan
        $r6 = Invoke-SSHCommand -SessionId $session.SessionId -Command "grep -i 'error\|exception\|failed\|失败' /home/ubuntu/logs/*.log 2>/dev/null | tail -10"
        if ($r6.Output) {
            Write-Host "  ⚠ 找到错误记录:" -ForegroundColor Yellow
            Write-Host $r6.Output -ForegroundColor Red
        } else {
            Write-Host "  ✓ 未找到错误记录" -ForegroundColor Green
        }
        Write-Host ""
        
        # 7. 检查最近的日志（最后30行）
        if ($Detailed) {
            Write-Host "7. 最近的日志（最后30行）..." -ForegroundColor Cyan
            $r7 = Invoke-SSHCommand -SessionId $session.SessionId -Command "tail -30 /home/ubuntu/logs/*.log 2>/dev/null | tail -30"
            if ($r7.Output) {
                Write-Host $r7.Output -ForegroundColor Gray
            } else {
                Write-Host "  ✗ 无法读取日志" -ForegroundColor Red
            }
            Write-Host ""
        }
        
        # 8. 检查系统资源
        Write-Host "8. 检查系统资源..." -ForegroundColor Cyan
        $r8 = Invoke-SSHCommand -SessionId $session.SessionId -Command "free -h && echo '---' && df -h / | tail -1"
        if ($r8.Output) {
            Write-Host $r8.Output -ForegroundColor Gray
        }
        Write-Host ""
        
        Remove-SSHSession -SessionId $session.SessionId | Out-Null
        
    } catch {
        Write-Host "✗ SSH 连接失败: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  测试完成" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示: 要测试自动回复功能，请在 Telegram 群组中发送消息" -ForegroundColor Yellow
Write-Host "     然后再次运行此脚本查看回复记录" -ForegroundColor Yellow

