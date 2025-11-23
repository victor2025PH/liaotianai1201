# 检查所有服务器状态并修复问题
$ErrorActionPreference = "Continue"
Import-Module Posh-SSH

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  检查所有服务器状态并修复问题" -ForegroundColor Cyan
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
        
        # 1. 检查 main.py 进程
        Write-Host "1. 检查 main.py 进程..." -ForegroundColor Cyan
        $r1 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ps aux | grep main.py | grep -v grep"
        if ($r1.Output) {
            Write-Host "  ✓ main.py 正在运行" -ForegroundColor Green
            Write-Host $r1.Output -ForegroundColor Gray
        } else {
            Write-Host "  ✗ main.py 未运行" -ForegroundColor Red
        }
        Write-Host ""
        
        # 2. 查看 main.log
        Write-Host "2. 查看 main.log (最后50行)..." -ForegroundColor Cyan
        $r2 = Invoke-SSHCommand -SessionId $session.SessionId -Command "tail -50 /home/ubuntu/logs/main.log 2>/dev/null"
        if ($r2.Output) {
            Write-Host $r2.Output -ForegroundColor Gray
        } else {
            Write-Host "  (日志文件为空或不存在)" -ForegroundColor DarkGray
        }
        Write-Host ""
        
        # 3. 检查错误
        Write-Host "3. 检查错误..." -ForegroundColor Cyan
        $r3 = Invoke-SSHCommand -SessionId $session.SessionId -Command "grep -i error /home/ubuntu/logs/main.log 2>/dev/null | tail -10"
        if ($r3.Output) {
            Write-Host "  发现错误:" -ForegroundColor Yellow
            Write-Host $r3.Output -ForegroundColor Red
        } else {
            Write-Host "  ✓ 未发现错误" -ForegroundColor Green
        }
        Write-Host ""
        
        # 4. 检查 Telegram 连接
        Write-Host "4. 检查 Telegram 连接..." -ForegroundColor Cyan
        $r4 = Invoke-SSHCommand -SessionId $session.SessionId -Command "grep -i 'connected\|started\|ready\|authorized' /home/ubuntu/logs/main.log 2>/dev/null | tail -10"
        if ($r4.Output) {
            Write-Host "  ✓ 找到连接记录:" -ForegroundColor Green
            Write-Host $r4.Output -ForegroundColor Gray
        } else {
            Write-Host "  (未找到连接记录)" -ForegroundColor Yellow
        }
        Write-Host ""
        
        # 5. 如果是 worker-01 且缺少依赖，安装
        if ($s.Name -eq "worker-01") {
            Write-Host "5. 安装缺失的依赖 (worker-01)..." -ForegroundColor Cyan
            $r5 = Invoke-SSHCommand -SessionId $session.SessionId -Command "python3 -m pip install --user --upgrade --break-system-packages pandas openpyxl 2>&1"
            if ($r5.Output -match "Successfully|already satisfied") {
                Write-Host "  ✓ 依赖已安装" -ForegroundColor Green
            } else {
                Write-Host "  ⚠ 安装可能有问题" -ForegroundColor Yellow
                Write-Host $r5.Output -ForegroundColor Gray
            }
            Write-Host ""
            
            # 重新启动
            Write-Host "6. 重新启动 main.py..." -ForegroundColor Cyan
            $sessionFile = "/home/ubuntu/utils/639641842001.session"
            $sessionName = "639641842001"
            $startCmd = "cd /home/ubuntu && export PATH=`$HOME/.local/bin:`$PATH && export TELEGRAM_SESSION_FILE='$sessionFile' && export TELEGRAM_SESSION_NAME='$sessionName' && export TELEGRAM_API_ID=12345 && export TELEGRAM_API_HASH='abc123def456' && export OPENAI_API_KEY='sk-placeholder' && pkill -f 'python.*main.py' && sleep 2 && nohup python3 main.py > logs/main.log 2>&1 & sleep 5 && ps aux | grep '[m]ain.py'"
            $r6 = Invoke-SSHCommand -SessionId $session.SessionId -Command $startCmd
            if ($r6.Output -match "main.py") {
                Write-Host "  ✓ main.py 已启动" -ForegroundColor Green
            } else {
                Write-Host "  ✗ main.py 启动失败" -ForegroundColor Red
            }
            Write-Host ""
        }
        
        Remove-SSHSession -SessionId $session.SessionId | Out-Null
        
    } catch {
        Write-Host "✗ SSH 连接失败: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  检查完成" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

