# 检查所有服务器的账号运行状态
$ErrorActionPreference = "Continue"
Import-Module Posh-SSH

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  检查所有服务器的账号运行状态" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$servers = @(
    @{IP="165.154.255.48"; Name="洛杉矶"; Pass="8iDcGrYb52Fxpzee"},
    @{IP="165.154.233.179"; Name="马尼拉"; Pass="8iDcGrYb52Fxpzee"},
    @{IP="165.154.254.99"; Name="worker-01"; Pass="Along2025!!!"}
)

foreach ($s in $servers) {
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host "$($s.Name) ($($s.IP))" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    
    try {
        $pass = ConvertTo-SecureString $s.Pass -AsPlainText -Force
        $cred = New-Object System.Management.Automation.PSCredential("ubuntu", $pass)
        $session = New-SSHSession -ComputerName $s.IP -Credential $cred -AcceptKey -ErrorAction Stop
        
        Write-Host "✓ SSH 连接成功" -ForegroundColor Green
        Write-Host ""
        
        # 1. 检查所有 main.py 进程
        Write-Host "1. 检查所有 main.py 进程..." -ForegroundColor Cyan
        $r1 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ps aux | grep '[m]ain.py'"
        if ($r1.Output) {
            $processCount = ($r1.Output -split "`n").Count
            Write-Host "  ✓ 运行中: $processCount 个进程" -ForegroundColor Green
            Write-Host $r1.Output -ForegroundColor Gray
        } else {
            Write-Host "  ✗ 没有运行中的进程" -ForegroundColor Red
        }
        Write-Host ""
        
        # 2. 检查所有日志文件
        Write-Host "2. 检查所有日志文件..." -ForegroundColor Cyan
        $r2 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ls -lh /home/ubuntu/logs/main_*.log 2>/dev/null | awk '{print `$9, `$5}'"
        if ($r2.Output) {
            Write-Host "  日志文件:" -ForegroundColor Green
            Write-Host $r2.Output -ForegroundColor Gray
        } else {
            Write-Host "  (未找到日志文件)" -ForegroundColor DarkGray
        }
        Write-Host ""
        
        # 3. 检查每个账号的状态
        Write-Host "3. 检查每个账号的状态..." -ForegroundColor Cyan
        $r3 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ls /home/ubuntu/logs/main_*.log 2>/dev/null | sed 's|.*/main_||; s|\.log$||'"
        if ($r3.Output) {
            $accounts = ($r3.Output -split "`n") | Where-Object { $_.Trim() -ne "" }
            foreach ($account in $accounts) {
                $account = $account.Trim()
                $logFile = "/home/ubuntu/logs/main_$account.log"
                
                Write-Host "  账号: $account" -ForegroundColor Yellow
                
                # 检查进程
                $r4 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ps aux | grep '[m]ain.py' | grep -i '$account' || echo 'not running'"
                if ($r4.Output -match "main.py") {
                    Write-Host "    ✓ 进程运行中" -ForegroundColor Green
                } else {
                    Write-Host "    ✗ 进程未运行" -ForegroundColor Red
                }
                
                # 检查日志
                $r5 = Invoke-SSHCommand -SessionId $session.SessionId -Command "tail -20 $logFile 2>/dev/null | grep -i '驗證成功\|Session 驗證成功\|connected\|started\|ready\|已啟動\|TG机器人\|Enter phone\|EOFError\|error\|exception' | tail -5"
                if ($r5.Output) {
                    if ($r5.Output -match "驗證成功|Session 驗證成功|connected|started|ready|已啟動|TG机器人") {
                        Write-Host "    ✓ Session 验证成功" -ForegroundColor Green
                    } elseif ($r5.Output -match "Enter phone|EOFError") {
                        Write-Host "    ✗ Session 无效" -ForegroundColor Red
                    } else {
                        Write-Host "    ⚠ 状态: $($r5.Output)" -ForegroundColor Yellow
                    }
                } else {
                    Write-Host "    ⚠ 暂无日志" -ForegroundColor Yellow
                }
                Write-Host ""
            }
        } else {
            Write-Host "  (未找到账号日志)" -ForegroundColor DarkGray
        }
        Write-Host ""
        
        Remove-SSHSession -SessionId $session.SessionId | Out-Null
        
    } catch {
        Write-Host "✗ SSH 连接失败: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  检查完成" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

