# 使用 /opt/group-ai/sessions/ 中的 Session 文件
$ErrorActionPreference = "Continue"
Import-Module Posh-SSH

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  使用 /opt/group-ai/sessions/ 中的 Session 文件" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 真实的 API 凭证
$API_ID = "24782266"
$API_HASH = "48ccfcd14b237d4f6753c122f6a798606"

$servers = @(
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
        
        # 1. 查找 /opt/group-ai/sessions/ 中的所有 Session 文件
        Write-Host "1. 查找 /opt/group-ai/sessions/ 中的 Session 文件..." -ForegroundColor Cyan
        $r1 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ls -lh /opt/group-ai/sessions/*.session 2>/dev/null | awk '{print `$9, `$5}'"
        if (-not $r1.Output -or $r1.Output.Trim() -eq "") {
            Write-Host "  ✗ 未找到 Session 文件" -ForegroundColor Red
            Remove-SSHSession -SessionId $session.SessionId | Out-Null
            continue
        }
        
        Write-Host "  ✓ 找到 Session 文件:" -ForegroundColor Green
        Write-Host $r1.Output -ForegroundColor Gray
        
        # 解析文件列表
        $sessionFiles = @()
        foreach ($line in ($r1.Output -split "`n")) {
            if ($line -match "^/opt/group-ai/sessions/([^/]+)\.session") {
                $sessionFiles += $line.Trim()
            }
        }
        
        if ($sessionFiles.Count -eq 0) {
            Write-Host "  ✗ 无法解析 Session 文件列表" -ForegroundColor Red
            Remove-SSHSession -SessionId $session.SessionId | Out-Null
            continue
        }
        
        Write-Host ""
        
        # 2. 确保 sessions 目录存在
        Write-Host "2. 准备 sessions 目录..." -ForegroundColor Cyan
        $r2 = Invoke-SSHCommand -SessionId $session.SessionId -Command "mkdir -p /home/ubuntu/sessions && echo OK"
        Write-Host "  ✓ sessions 目录已准备" -ForegroundColor Green
        Write-Host ""
        
        # 3. 尝试每个 Session 文件
        $success = $false
        foreach ($sessionFile in $sessionFiles) {
            $sessionName = [System.IO.Path]::GetFileNameWithoutExtension($sessionFile)
            Write-Host "3. 尝试 Session: $sessionName" -ForegroundColor Cyan
            Write-Host "   文件: $sessionFile" -ForegroundColor Gray
            
            # 复制到 sessions 目录
            $copyCmd = "cp '$sessionFile' /home/ubuntu/sessions/$sessionName.session 2>&1 && ls -lh /home/ubuntu/sessions/$sessionName.session"
            $r3 = Invoke-SSHCommand -SessionId $session.SessionId -Command $copyCmd
            if ($r3.Output -match "\.session") {
                Write-Host "   ✓ 已复制到 sessions 目录" -ForegroundColor Green
            } else {
                Write-Host "   ⚠ 复制可能失败" -ForegroundColor Yellow
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
            Start-Sleep -Seconds 15
            
            # 检查进程
            $r6 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ps aux | grep '[m]ain.py'"
            if (-not $r6.Output) {
                Write-Host "   ✗ main.py 未运行" -ForegroundColor Red
                $r7 = Invoke-SSHCommand -SessionId $session.SessionId -Command "tail -20 /home/ubuntu/logs/main.log 2>/dev/null | grep -i 'error\|exception\|EOFError' | tail -3"
                if ($r7.Output) {
                    Write-Host "   错误: $($r7.Output)" -ForegroundColor Red
                }
                Write-Host ""
                continue
            }
            
            Write-Host "   ✓ main.py 正在运行" -ForegroundColor Green
            Start-Sleep -Seconds 10
            
            # 检查是否成功连接
            $r8 = Invoke-SSHCommand -SessionId $session.SessionId -Command "grep -i '驗證成功\|Session 驗證成功\|connected\|started\|ready\|已啟動\|TG机器人运营主控已啟動' /home/ubuntu/logs/main.log 2>/dev/null | tail -5"
            if ($r8.Output -match "驗證成功|Session 驗證成功|connected|started|ready|已啟動|TG机器人运营主控已啟動") {
                Write-Host "   ✓✓✓ Session 验证成功！" -ForegroundColor Green
                Write-Host $r8.Output -ForegroundColor Gray
                $success = $true
                Write-Host ""
                Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
                Write-Host "✓ 成功使用 Session: $sessionName" -ForegroundColor Green
                Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
                Write-Host ""
                break
            } else {
                # 检查是否还在尝试交互式输入
                $r9 = Invoke-SSHCommand -SessionId $session.SessionId -Command "grep -i 'Enter phone number\|EOFError' /home/ubuntu/logs/main.log 2>/dev/null | tail -3"
                if ($r9.Output) {
                    Write-Host "   ✗ Session 无效（仍在尝试交互式输入）" -ForegroundColor Red
                    $r10 = Invoke-SSHCommand -SessionId $session.SessionId -Command "pkill -f 'python.*main.py'; sleep 2"
                } else {
                    # 再等待一下
                    Write-Host "   ⏳ 等待验证中..." -ForegroundColor Yellow
                    Start-Sleep -Seconds 15
                    $r11 = Invoke-SSHCommand -SessionId $session.SessionId -Command "grep -i '驗證成功\|Session 驗證成功\|connected\|started\|ready\|已啟動\|TG机器人运营主控已啟動\|Enter phone\|EOFError' /home/ubuntu/logs/main.log 2>/dev/null | tail -5"
                    if ($r11.Output -match "驗證成功|Session 驗證成功|connected|started|ready|已啟動|TG机器人运营主控已啟動") {
                        Write-Host "   ✓✓✓ Session 验证成功！" -ForegroundColor Green
                        Write-Host $r11.Output -ForegroundColor Gray
                        $success = $true
                        Write-Host ""
                        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
                        Write-Host "✓ 成功使用 Session: $sessionName" -ForegroundColor Green
                        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
                        Write-Host ""
                        break
                    } elseif ($r11.Output -match "Enter phone|EOFError") {
                        Write-Host "   ✗ Session 无效" -ForegroundColor Red
                        $r10 = Invoke-SSHCommand -SessionId $session.SessionId -Command "pkill -f 'python.*main.py'; sleep 2"
                    } else {
                        Write-Host "   ⚠ 状态不明确，继续尝试下一个" -ForegroundColor Yellow
                        $r10 = Invoke-SSHCommand -SessionId $session.SessionId -Command "pkill -f 'python.*main.py'; sleep 2"
                    }
                }
            }
            Write-Host ""
        }
        
        if (-not $success) {
            Write-Host "4. 所有 Session 文件都无效" -ForegroundColor Yellow
            Write-Host "   已尝试 $($sessionFiles.Count) 个 Session 文件" -ForegroundColor Gray
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

