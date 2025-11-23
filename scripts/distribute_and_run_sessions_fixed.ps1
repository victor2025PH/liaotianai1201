# 智能分发 Session 文件到各服务器并启动多个账号（修复数据库锁定问题）
$ErrorActionPreference = "Continue"
Import-Module Posh-SSH

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  智能分发 Session 文件并启动多个账号（修复版）" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 真实的 API 凭证
$API_ID = "24782266"
$API_HASH = "48ccfcd14b237d4f6753c122f6a798606"

# 服务器配置
$servers = @(
    @{IP="165.154.255.48"; Name="洛杉矶"; Pass="8iDcGrYb52Fxpzee"; SessionsPerServer=4},
    @{IP="165.154.233.179"; Name="马尼拉"; Pass="8iDcGrYb52Fxpzee"; SessionsPerServer=4},
    @{IP="165.154.254.99"; Name="worker-01"; Pass="Along2025!!!"; SessionsPerServer=4}
)

# 1. 读取本地 sessions 目录中的所有 Session 文件
Write-Host "1. 读取本地 sessions 目录..." -ForegroundColor Cyan
$localSessionsPath = "sessions"
if (-not (Test-Path $localSessionsPath)) {
    Write-Host "  ✗ sessions 目录不存在: $localSessionsPath" -ForegroundColor Red
    exit 1
}

$sessionFiles = Get-ChildItem -Path $localSessionsPath -Filter "*.session" -File | Where-Object { 
    $_.Name -notmatch "-journal$" -and $_.Length -gt 1000 
} | Sort-Object LastWriteTime -Descending

if ($sessionFiles.Count -eq 0) {
    Write-Host "  ✗ 未找到有效的 Session 文件" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ 找到 $($sessionFiles.Count) 个有效的 Session 文件" -ForegroundColor Green
Write-Host ""

# 2. 智能分配 Session 文件到各服务器
Write-Host "2. 智能分配 Session 文件到各服务器..." -ForegroundColor Cyan
$totalSessions = $sessionFiles.Count
$totalNeeded = ($servers | Measure-Object -Property SessionsPerServer -Sum).Sum

if ($totalSessions -lt $totalNeeded) {
    Write-Host "  ⚠ 警告: 只有 $totalSessions 个 Session 文件，但需要 $totalNeeded 个" -ForegroundColor Yellow
    Write-Host "  将循环使用 Session 文件" -ForegroundColor Yellow
}

$sessionIndex = 0
$serverSessions = @{}

foreach ($server in $servers) {
    $serverSessions[$server.IP] = @()
    for ($i = 0; $i -lt $server.SessionsPerServer; $i++) {
        if ($sessionIndex -lt $sessionFiles.Count) {
            $sessionFile = $sessionFiles[$sessionIndex]
            $serverSessions[$server.IP] += $sessionFile
            $sessionIndex++
            if ($sessionIndex -ge $sessionFiles.Count) {
                $sessionIndex = 0  # 循环使用
            }
        }
    }
    Write-Host "  $($server.Name): $($serverSessions[$server.IP].Count) 个 Session 文件" -ForegroundColor Green
}
Write-Host ""

# 3. 分发 Session 文件并启动服务
foreach ($server in $servers) {
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host "$($server.Name) ($($server.IP))" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    
    try {
        $pass = ConvertTo-SecureString $server.Pass -AsPlainText -Force
        $cred = New-Object System.Management.Automation.PSCredential("ubuntu", $pass)
        $sshSession = New-SSHSession -ComputerName $server.IP -Credential $cred -AcceptKey -ErrorAction Stop
        
        Write-Host "✓ SSH 连接成功" -ForegroundColor Green
        Write-Host ""
        
        # 3.1 停止所有旧的 main.py 进程
        Write-Host "3.1 停止所有旧的进程..." -ForegroundColor Cyan
        $r1 = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command "pkill -f 'python.*main.py'; sleep 3; echo 'stopped'"
        Write-Host "  ✓ 已停止" -ForegroundColor Green
        Write-Host ""
        
        # 3.2 上传 Session 文件
        Write-Host "3.2 上传 Session 文件..." -ForegroundColor Cyan
        $uploadedSessions = @()
        foreach ($sessionFile in $serverSessions[$server.IP]) {
            $localPath = $sessionFile.FullName
            $sessionName = $sessionFile.BaseName
            $remotePath = "/home/ubuntu/sessions/$($sessionFile.Name)"
            
            Write-Host "  上传: $($sessionFile.Name)..." -ForegroundColor Yellow
            
            # 使用 base64 编码传输
            $content = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($localPath))
            $uploadScript = @"
echo '$content' | base64 -d > '$remotePath' && chmod 600 '$remotePath' && echo 'OK'
"@
            $r2 = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command $uploadScript
            if ($r2.Output -match "OK") {
                Write-Host "    ✓ 上传成功" -ForegroundColor Green
                $uploadedSessions += @{
                    Name = $sessionName
                    Remote = $remotePath
                }
            } else {
                Write-Host "    ✗ 上传失败" -ForegroundColor Red
            }
        }
        Write-Host ""
        
        if ($uploadedSessions.Count -eq 0) {
            Write-Host "  ✗ 没有成功上传任何 Session 文件" -ForegroundColor Red
            Remove-SSHSession -SessionId $sshSession.SessionId | Out-Null
            continue
        }
        
        Write-Host "  ✓ 成功上传 $($uploadedSessions.Count) 个 Session 文件" -ForegroundColor Green
        Write-Host ""
        
        # 3.3 为每个账号创建独立的工作目录并启动
        Write-Host "3.3 为每个账号创建独立工作目录并启动..." -ForegroundColor Cyan
        $startedCount = 0
        foreach ($sess in $uploadedSessions) {
            $sessionName = $sess.Name
            $workDir = "/home/ubuntu/accounts/$sessionName"
            $logFile = "/home/ubuntu/logs/main_$sessionName.log"
            $pidFile = "/home/ubuntu/logs/main_$sessionName.pid"
            
            Write-Host "  启动账号: $sessionName..." -ForegroundColor Yellow
            
            # 创建独立工作目录
            $setupScript = @"
mkdir -p $workDir
mkdir -p $workDir/sessions
mkdir -p $workDir/logs
mkdir -p $workDir/data
cp '$($sess.Remote)' $workDir/sessions/$sessionName.session
chmod 600 $workDir/sessions/$sessionName.session
echo 'OK'
"@
            $r3 = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command $setupScript
            if (-not ($r3.Output -match "OK")) {
                Write-Host "    ✗ 创建工作目录失败" -ForegroundColor Red
                continue
            }
            
            # 创建必要的目录和文件链接
            $setupDirs = @"
mkdir -p $workDir/ai_models
mkdir -p $workDir/data
mkdir -p $workDir/photos
mkdir -p $workDir/voices
mkdir -p $workDir/static
# 如果项目根目录有这些文件，创建符号链接
if [ -d /home/ubuntu/ai_models ]; then
    ln -sf /home/ubuntu/ai_models/* $workDir/ai_models/ 2>/dev/null || true
fi
if [ -d /home/ubuntu/data ]; then
    ln -sf /home/ubuntu/data/* $workDir/data/ 2>/dev/null || true
fi
# 创建空的 intro_segments.yaml 如果不存在
if [ ! -f $workDir/ai_models/intro_segments.yaml ]; then
    echo '{}' > $workDir/ai_models/intro_segments.yaml
fi
echo 'OK'
"@
            $r4 = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command $setupDirs
            if (-not ($r4.Output -match "OK")) {
                Write-Host "    ✗ 设置目录失败" -ForegroundColor Red
                continue
            }
            
            # 启动 main.py（从项目根目录运行，但使用独立工作目录作为 workdir）
            # 创建启动脚本文件（避免 PowerShell 解析问题）
            $startScriptContent = @"
#!/bin/bash
cd /home/ubuntu
export PATH=`$HOME/.local/bin:`$PATH
export TELEGRAM_API_ID=$API_ID
export TELEGRAM_API_HASH='$API_HASH'
export OPENAI_API_KEY='sk-placeholder'
export TELEGRAM_SESSION_FILE='$workDir/sessions/$sessionName.session'
export TELEGRAM_SESSION_NAME='$sessionName'
nohup python3 main.py > $logFile 2>&1 &
echo `$! > $pidFile
echo `$!
"@
            $scriptFile = "/tmp/start_$sessionName.sh"
            $r4a = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command "cat > $scriptFile << 'SCRIPTEOF'
$startScriptContent
SCRIPTEOF
chmod +x $scriptFile && echo 'OK'"
            
            if (-not ($r4a.Output -match "OK")) {
                Write-Host "    ✗ 创建启动脚本失败" -ForegroundColor Red
                continue
            }
            
            # 执行启动脚本
            $r4 = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command "bash $scriptFile"
            $r4 = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command $startScript
            if ($r4.Output -match "^\d+$") {
                Write-Host "    ✓ 已启动 (PID: $($r4.Output.Trim()))" -ForegroundColor Green
                $startedCount++
            } else {
                Write-Host "    ✗ 启动失败" -ForegroundColor Red
            }
            Start-Sleep -Seconds 3
        }
        Write-Host ""
        
        Write-Host "  ✓ 成功启动 $startedCount 个账号" -ForegroundColor Green
        Write-Host ""
        
        # 3.4 等待并检查进程状态
        Write-Host "3.4 检查进程状态（等待 20 秒）..." -ForegroundColor Cyan
        Start-Sleep -Seconds 20
        
        $r5 = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command "ps aux | grep '[m]ain.py' | wc -l"
        $processCount = [int]$r5.Output.Trim()
        Write-Host "  ✓ 当前运行 $processCount 个 main.py 进程" -ForegroundColor Green
        
        $r6 = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command "ps aux | grep '[m]ain.py'"
        Write-Host $r6.Output -ForegroundColor Gray
        Write-Host ""
        
        # 3.5 检查启动日志
        Write-Host "3.5 检查启动日志..." -ForegroundColor Cyan
        foreach ($sess in $uploadedSessions) {
            $logFile = "/home/ubuntu/logs/main_$($sess.Name).log"
            $r7 = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command "tail -15 $logFile 2>/dev/null | grep -i '驗證成功\|Session 驗證成功\|connected\|started\|ready\|已啟動\|TG机器人\|Enter phone\|EOFError\|error\|exception' | tail -3"
            if ($r7.Output) {
                if ($r7.Output -match "驗證成功|Session 驗證成功|connected|started|ready|已啟動|TG机器人") {
                    Write-Host "  ✓ $($sess.Name): 验证成功" -ForegroundColor Green
                } elseif ($r7.Output -match "Enter phone|EOFError") {
                    Write-Host "  ✗ $($sess.Name): Session 无效" -ForegroundColor Red
                } else {
                    Write-Host "  ⚠ $($sess.Name): $($r7.Output)" -ForegroundColor Yellow
                }
            } else {
                Write-Host "  ⚠ $($sess.Name): 暂无日志" -ForegroundColor Yellow
            }
        }
        Write-Host ""
        
        Remove-SSHSession -SessionId $sshSession.SessionId | Out-Null
        
    } catch {
        Write-Host "✗ SSH 连接失败: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  分发和启动完成" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "每个服务器已启动多个账号，每个账号使用独立的工作目录" -ForegroundColor Green
Write-Host "工作目录: /home/ubuntu/accounts/<session_name>/" -ForegroundColor Gray
Write-Host "日志文件: /home/ubuntu/logs/main_<session_name>.log" -ForegroundColor Gray

