# 智能分发 Session 文件到各服务器并启动多个账号（简化版）
$ErrorActionPreference = "Continue"
Import-Module Posh-SSH

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  智能分发 Session 文件并启动多个账号（简化版）" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 真实的 API 凭证
$API_ID = "24782266"
$API_HASH = "48ccfcd14b237d4f6753c122f6a798606"

# 服务器配置（不预设每个服务器的账号数，根据可用Session文件智能分配）
$servers = @(
    @{IP="165.154.255.48"; Name="洛杉矶"; Pass="8iDcGrYb52Fxpzee"},
    @{IP="165.154.233.179"; Name="马尼拉"; Pass="8iDcGrYb52Fxpzee"},
    @{IP="165.154.254.99"; Name="worker-01"; Pass="Along2025!!!"}
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

# 2. 智能分配 Session 文件到各服务器（确保每个Session文件只使用一次）
Write-Host "2. 智能分配 Session 文件到各服务器（确保唯一性）..." -ForegroundColor Cyan
$totalSessions = $sessionFiles.Count
$totalServers = $servers.Count

# 计算每个服务器应该分配多少个Session文件
$sessionsPerServer = [math]::Floor($totalSessions / $totalServers)
$remainder = $totalSessions % $totalServers

Write-Host "  总共 $totalSessions 个 Session 文件，$totalServers 个服务器" -ForegroundColor Gray
Write-Host "  基础分配: 每个服务器 $sessionsPerServer 个" -ForegroundColor Gray
if ($remainder -gt 0) {
    Write-Host "  剩余 $remainder 个将分配给前 $remainder 个服务器" -ForegroundColor Gray
}
Write-Host ""

$sessionIndex = 0
$serverSessions = @{}

foreach ($server in $servers) {
    $serverSessions[$server.IP] = @()
    
    # 计算这个服务器应该分配多少个Session文件
    $countForThisServer = $sessionsPerServer
    $serverIndex = $servers.IndexOf($server)
    if ($serverIndex -lt $remainder) {
        $countForThisServer++  # 前几个服务器多分配一个
    }
    
    # 分配Session文件（确保不重复）
    for ($i = 0; $i -lt $countForThisServer -and $sessionIndex -lt $sessionFiles.Count; $i++) {
        $sessionFile = $sessionFiles[$sessionIndex]
        $serverSessions[$server.IP] += $sessionFile
        $sessionIndex++
    }
    
    Write-Host "  $($server.Name): $($serverSessions[$server.IP].Count) 个 Session 文件" -ForegroundColor Green
    foreach ($sess in $serverSessions[$server.IP]) {
        Write-Host "    - $($sess.Name)" -ForegroundColor Gray
    }
}
Write-Host ""

# 验证没有重复
$allAssigned = @()
foreach ($server in $servers) {
    foreach ($sess in $serverSessions[$server.IP]) {
        if ($allAssigned -contains $sess) {
            Write-Host "  ⚠ 警告: Session 文件 $($sess.Name) 被重复分配！" -ForegroundColor Red
        } else {
            $allAssigned += $sess
        }
    }
}

if ($allAssigned.Count -eq $totalSessions) {
    Write-Host "  ✓ 验证通过: 所有 $totalSessions 个 Session 文件都已分配，无重复" -ForegroundColor Green
} else {
    Write-Host "  ⚠ 警告: 分配了 $($allAssigned.Count) 个，但总共有 $totalSessions 个" -ForegroundColor Yellow
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
        
        # 3.2 准备 sessions 目录并清理旧的 Session 文件
        Write-Host "3.2 准备 sessions 目录并清理旧的 Session 文件..." -ForegroundColor Cyan
        $cleanupCmd = @"
mkdir -p /home/ubuntu/sessions
mkdir -p /home/ubuntu/logs
# 清理所有旧的 Session 文件，只保留当前分配的
rm -f /home/ubuntu/sessions/*.session
rm -f /home/ubuntu/sessions/*.session-journal
echo "已清理旧的 Session 文件"
"@
        $r2 = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command $cleanupCmd
        Write-Host "  ✓ 目录已准备，旧 Session 文件已清理" -ForegroundColor Green
        Write-Host ""
        
        # 3.3 上传 Session 文件
        Write-Host "3.3 上传 Session 文件..." -ForegroundColor Cyan
        $uploadedSessions = @()
        foreach ($sessionFile in $serverSessions[$server.IP]) {
            $localPath = $sessionFile.FullName
            $sessionName = $sessionFile.BaseName
            $remotePath = "/home/ubuntu/sessions/$($sessionFile.Name)"
            
            Write-Host "  上传: $($sessionFile.Name)..." -ForegroundColor Yellow
            
            # 使用 base64 编码传输
            $content = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($localPath))
            $uploadScript = "echo '$content' | base64 -d > '$remotePath' && chmod 600 '$remotePath' && echo 'OK'"
            $r3 = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command $uploadScript
            if ($r3.Output -match "OK") {
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
        
        # 3.4 为每个账号启动独立的 main.py 进程
        Write-Host "3.4 启动多个账号（每个 Session 一个进程）..." -ForegroundColor Cyan
        $startedCount = 0
        foreach ($sess in $uploadedSessions) {
            $sessionName = $sess.Name
            $logFile = "/home/ubuntu/logs/main_$sessionName.log"
            $pidFile = "/home/ubuntu/logs/main_$sessionName.pid"
            
            Write-Host "  启动账号: $sessionName..." -ForegroundColor Yellow
            
            # 创建启动脚本（使用 Python 脚本避免 PowerShell 解析问题）
            $pythonScript = @"
import subprocess
import os
import sys

os.chdir('/home/ubuntu')
env = os.environ.copy()
env['PATH'] = os.path.expanduser('~/.local/bin') + ':' + env.get('PATH', '')
env['TELEGRAM_API_ID'] = '$API_ID'
env['TELEGRAM_API_HASH'] = '$API_HASH'
env['OPENAI_API_KEY'] = 'sk-placeholder'
env['TELEGRAM_SESSION_FILE'] = '$($sess.Remote)'
env['TELEGRAM_SESSION_NAME'] = '$sessionName'

with open('$logFile', 'w') as log:
    process = subprocess.Popen(
        ['python3', 'main.py'],
        stdout=log,
        stderr=subprocess.STDOUT,
        env=env,
        cwd='/home/ubuntu'
    )
    with open('$pidFile', 'w') as pid_file:
        pid_file.write(str(process.pid))
    print(process.pid)
"@
            $scriptFile = "/tmp/start_$sessionName.py"
            $r4a = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command "python3 -c `"$($pythonScript -replace '"', '\"')`""
            
            if ($r4a.Output -match "^\d+$") {
                Write-Host "    ✓ 已启动 (PID: $($r4a.Output.Trim()))" -ForegroundColor Green
                $startedCount++
            } else {
                Write-Host "    ✗ 启动失败: $($r4a.Output)" -ForegroundColor Red
            }
            Start-Sleep -Seconds 3
        }
        Write-Host ""
        
        Write-Host "  ✓ 成功启动 $startedCount 个账号" -ForegroundColor Green
        Write-Host ""
        
        # 3.5 等待并检查进程状态
        Write-Host "3.5 检查进程状态（等待 20 秒）..." -ForegroundColor Cyan
        Start-Sleep -Seconds 20
        
        $r5 = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command "ps aux | grep '[m]ain.py' | wc -l"
        $processCount = [int]$r5.Output.Trim()
        Write-Host "  ✓ 当前运行 $processCount 个 main.py 进程" -ForegroundColor Green
        
        $r6 = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command "ps aux | grep '[m]ain.py'"
        if ($r6.Output) {
            Write-Host $r6.Output -ForegroundColor Gray
        }
        Write-Host ""
        
        # 3.6 检查启动日志
        Write-Host "3.6 检查启动日志..." -ForegroundColor Cyan
        foreach ($sess in $uploadedSessions) {
            $logFile = "/home/ubuntu/logs/main_$($sess.Name).log"
            $r7 = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command "tail -20 $logFile 2>/dev/null | grep -i '驗證成功\|Session 驗證成功\|connected\|started\|ready\|已啟動\|TG机器人\|Enter phone\|EOFError\|error\|exception' | tail -3"
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
Write-Host "每个服务器已启动多个账号，每个账号使用独立的 Session 文件" -ForegroundColor Green
Write-Host "日志文件位置: /home/ubuntu/logs/main_<session_name>.log" -ForegroundColor Gray

