# 尝试所有可用的 Session 文件
$ErrorActionPreference = "Continue"
Import-Module Posh-SSH

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  尝试所有可用的 Session 文件" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 真实的 API 凭证
$API_ID = "24782266"
$API_HASH = "48ccfcd14b237d4f6753c122f6a798606"

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
        
        # 1. 查找所有 Session 文件
        Write-Host "1. 查找所有 Session 文件..." -ForegroundColor Cyan
        $r1 = Invoke-SSHCommand -SessionId $session.SessionId -Command "find /home/ubuntu -name '*.session' -type f -size +100c 2>/dev/null | sort"
        $sessionFiles = @()
        if ($r1.Output) {
            foreach ($line in ($r1.Output -split "`n")) {
                if ($line.Trim() -ne "" -and $line -match "\.session$") {
                    $sessionFiles += $line.Trim()
                }
            }
        }
        
        if ($sessionFiles.Count -eq 0) {
            Write-Host "  ✗ 未找到 Session 文件" -ForegroundColor Red
            Write-Host "  需要重新生成 Session 文件" -ForegroundColor Yellow
            Remove-SSHSession -SessionId $session.SessionId | Out-Null
            continue
        }
        
        Write-Host "  ✓ 找到 $($sessionFiles.Count) 个 Session 文件:" -ForegroundColor Green
        foreach ($file in $sessionFiles) {
            $size = Invoke-SSHCommand -SessionId $session.SessionId -Command "ls -lh '$file' 2>/dev/null | awk '{print `$5}'"
            Write-Host "    - $file ($($size.Output.Trim()))" -ForegroundColor Gray
        }
        Write-Host ""
        
        # 2. 确保 sessions 目录存在
        Write-Host "2. 确保 sessions 目录存在..." -ForegroundColor Cyan
        $r2 = Invoke-SSHCommand -SessionId $session.SessionId -Command "mkdir -p /home/ubuntu/sessions && echo OK"
        Write-Host "  ✓ sessions 目录已创建" -ForegroundColor Green
        Write-Host ""
        
        # 3. 尝试每个 Session 文件
        $success = $false
        foreach ($sessionFile in $sessionFiles) {
            $sessionName = [System.IO.Path]::GetFileNameWithoutExtension($sessionFile)
            Write-Host "3. 尝试 Session 文件: $sessionName" -ForegroundColor Cyan
            Write-Host "   文件路径: $sessionFile" -ForegroundColor Gray
            
            # 复制到 sessions 目录（如果不在那里）
            if ($sessionFile -notmatch "/sessions/") {
                $copyCmd = "cp '$sessionFile' /home/ubuntu/sessions/$sessionName.session 2>&1"
                $r3 = Invoke-SSHCommand -SessionId $session.SessionId -Command $copyCmd
            }
            
            # 停止旧的 main.py
            $r4 = Invoke-SSHCommand -SessionId $session.SessionId -Command "pkill -f 'python.*main.py'; sleep 2"
            
            # 启动 main.py
            Write-Host "   启动 main.py..." -ForegroundColor Yellow
            $startCmd = @"
cd /home/ubuntu
export PATH=`$HOME/.local/bin:`$PATH
export TELEGRAM_API_ID=$API_ID
export TELEGRAM_API_HASH='$API_HASH'
export OPENAI_API_KEY='sk-placeholder'
nohup python3 main.py > logs/main.log 2>&1 &
echo `$!
"@
            $r5 = Invoke-SSHCommand -SessionId $session.SessionId -Command $startCmd
            Start-Sleep -Seconds 10
            
            # 检查进程
            $r6 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ps aux | grep '[m]ain.py'"
            if (-not $r6.Output) {
                Write-Host "   ✗ main.py 未运行" -ForegroundColor Red
                # 检查错误日志
                $r7 = Invoke-SSHCommand -SessionId $session.SessionId -Command "tail -20 /home/ubuntu/logs/main.log 2>/dev/null | grep -i 'error\|exception\|EOFError' | tail -5"
                if ($r7.Output) {
                    Write-Host "   错误: $($r7.Output)" -ForegroundColor Red
                }
                Write-Host ""
                continue
            }
            
            # 检查是否成功连接
            Write-Host "   ✓ main.py 正在运行" -ForegroundColor Green
            Start-Sleep -Seconds 5
            
            $r8 = Invoke-SSHCommand -SessionId $session.SessionId -Command "grep -i '驗證成功\|connected\|started\|ready' /home/ubuntu/logs/main.log 2>/dev/null | tail -5"
            if ($r8.Output -match "驗證成功|connected|started|ready") {
                Write-Host "   ✓ Session 验证成功！" -ForegroundColor Green
                Write-Host $r8.Output -ForegroundColor Gray
                $success = $true
                Write-Host ""
                break
            } else {
                # 检查是否还在尝试交互式输入
                $r9 = Invoke-SSHCommand -SessionId $session.SessionId -Command "grep -i 'Enter phone number\|EOFError' /home/ubuntu/logs/main.log 2>/dev/null | tail -3"
                if ($r9.Output) {
                    Write-Host "   ✗ Session 无效（仍在尝试交互式输入）" -ForegroundColor Red
                    $r10 = Invoke-SSHCommand -SessionId $session.SessionId -Command "pkill -f 'python.*main.py'; sleep 2"
                } else {
                    Write-Host "   ⚠ Session 可能有效，但需要更多时间验证" -ForegroundColor Yellow
                    $success = $true
                    break
                }
            }
            Write-Host ""
        }
        
        if (-not $success) {
            Write-Host "4. 所有 Session 文件都无效，需要重新生成" -ForegroundColor Yellow
            Write-Host "   可以使用以下命令重新生成 Session:" -ForegroundColor Gray
            Write-Host "   python3 scripts/login.py" -ForegroundColor Cyan
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

