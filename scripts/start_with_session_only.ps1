# 直接使用 Session 文件启动，不需要 API 凭证
param(
    [string]$SessionPath = "",
    [switch]$AutoFind = $true
)

$ErrorActionPreference = "Continue"
Import-Module Posh-SSH

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  使用 Session 文件直接启动（无需 API 凭证）" -ForegroundColor Cyan
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
        
        # 1. 查找有效的 Session 文件
        Write-Host "1. 查找有效的 Session 文件..." -ForegroundColor Cyan
        $r1 = Invoke-SSHCommand -SessionId $session.SessionId -Command "find /home/ubuntu -name '*.session' -type f -size +100c 2>/dev/null | head -5"
        if ($r1.Output) {
            $sessionFiles = @()
            foreach ($line in ($r1.Output -split "`n")) {
                if ($line -match "\.session" -and $line.Trim() -ne "") {
                    $sessionFiles += $line.Trim()
                }
            }
            if ($sessionFiles.Count -gt 0) {
                Write-Host "  ✓ 找到有效的 Session 文件:" -ForegroundColor Green
                foreach ($file in $sessionFiles) {
                    $sizeCmd = "ls -lh '$file' 2>/dev/null | awk '{print `$5}'"
                    $size = Invoke-SSHCommand -SessionId $session.SessionId -Command $sizeCmd
                    Write-Host "    - $file ($($size.Output.Trim()))" -ForegroundColor Gray
                }
                $firstSession = $sessionFiles[0]
            } else {
                Write-Host "  ✗ 未找到有效的 Session 文件（文件太小）" -ForegroundColor Red
                Remove-SSHSession -SessionId $session.SessionId | Out-Null
                continue
            }
        } else {
            Write-Host "  ✗ 未找到 Session 文件" -ForegroundColor Red
            Remove-SSHSession -SessionId $session.SessionId | Out-Null
            continue
        }
        Write-Host ""
        
        # 2. 修改 config.py 使 API 凭证和 OpenAI Key 可选
        Write-Host "2. 修改配置使 API 凭证可选..." -ForegroundColor Cyan
        $modifyConfig = @'
import sys
config_file = "/home/ubuntu/config.py"
try:
    with open(config_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 修改 API_ID 和 API_HASH 为可选
    content = content.replace(
        'API_ID = _get_int_env("TELEGRAM_API_ID", default=None, required=True)',
        'API_ID = _get_int_env("TELEGRAM_API_ID", default=12345, required=False)'
    )
    content = content.replace(
        'API_HASH = _get_env("TELEGRAM_API_HASH", required=True)',
        'API_HASH = _get_env("TELEGRAM_API_HASH", default="abc123def456", required=False)'
    )
    content = content.replace(
        'SESSION_NAME = _get_env("TELEGRAM_SESSION_NAME", required=True)',
        'SESSION_NAME = _get_env("TELEGRAM_SESSION_NAME", default="session", required=False)'
    )
    # 修改 OPENAI_API_KEY 为可选
    content = content.replace(
        'OPENAI_API_KEY = _get_env("OPENAI_API_KEY", required=True)',
        'OPENAI_API_KEY = _get_env("OPENAI_API_KEY", default="sk-placeholder", required=False)'
    )
    
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(content)
    print("Config modified successfully")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
'@
        $r2 = Invoke-SSHCommand -SessionId $session.SessionId -Command "python3 << 'PYEOF'
$modifyConfig
PYEOF
"
        if ($r2.Output -match "successfully") {
            Write-Host "  ✓ 配置已修改" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ 配置修改可能失败: $($r2.Output)" -ForegroundColor Yellow
        }
        Write-Host ""
        
        # 3. 设置环境变量指向 Session 文件
        Write-Host "3. 设置环境变量..." -ForegroundColor Cyan
        $sessionName = [System.IO.Path]::GetFileNameWithoutExtension($firstSession)
        $sessionDir = [System.IO.Path]::GetDirectoryName($firstSession)
        Write-Host "  Session 文件: $firstSession" -ForegroundColor Gray
        Write-Host "  Session 名称: $sessionName" -ForegroundColor Gray
        Write-Host ""
        
        # 4. 停止旧的 main.py 进程
        Write-Host "4. 停止旧的 main.py 进程..." -ForegroundColor Cyan
        $r3 = Invoke-SSHCommand -SessionId $session.SessionId -Command "pkill -f 'python.*main.py'; sleep 2"
        Write-Host "  ✓ 已停止" -ForegroundColor Green
        Write-Host ""
        
        # 5. 启动 main.py
        Write-Host "5. 启动 main.py..." -ForegroundColor Cyan
        $startScript = @"
cd /home/ubuntu
export PATH=`$HOME/.local/bin:`$PATH
export TELEGRAM_SESSION_FILE='$firstSession'
export TELEGRAM_SESSION_NAME='$sessionName'
export TELEGRAM_API_ID=12345
export TELEGRAM_API_HASH='abc123def456'
export OPENAI_API_KEY='sk-placeholder'
nohup python3 main.py > logs/main.log 2>&1 &
echo `$!
"@
        $r4 = Invoke-SSHCommand -SessionId $session.SessionId -Command $startScript
        Write-Host "  启动命令已执行" -ForegroundColor Gray
        Start-Sleep -Seconds 5
        Write-Host ""
        
        # 6. 检查进程状态
        Write-Host "6. 检查进程状态..." -ForegroundColor Cyan
        $r5 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ps aux | grep '[m]ain.py'"
        if ($r5.Output) {
            Write-Host "  ✓ main.py 正在运行" -ForegroundColor Green
            Write-Host $r5.Output -ForegroundColor Gray
        } else {
            Write-Host "  ✗ main.py 未运行" -ForegroundColor Red
            Write-Host "  查看错误日志..." -ForegroundColor Yellow
            $r6 = Invoke-SSHCommand -SessionId $session.SessionId -Command "tail -30 /home/ubuntu/logs/main.log 2>/dev/null"
            Write-Host $r6.Output -ForegroundColor Red
        }
        Write-Host ""
        
        # 7. 检查日志
        Write-Host "7. 检查启动日志..." -ForegroundColor Cyan
        $r7 = Invoke-SSHCommand -SessionId $session.SessionId -Command "tail -20 /home/ubuntu/logs/main.log 2>/dev/null | grep -i 'started\|connected\|ready\|error\|exception' | tail -10"
        if ($r7.Output) {
            Write-Host $r7.Output -ForegroundColor Gray
        } else {
            Write-Host "  (暂无相关日志)" -ForegroundColor DarkGray
        }
        Write-Host ""
        
        Remove-SSHSession -SessionId $session.SessionId | Out-Null
        
    } catch {
        Write-Host "✗ SSH 连接失败: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  启动完成" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示: 运行测试脚本查看详细状态" -ForegroundColor Yellow
Write-Host "  pwsh -ExecutionPolicy Bypass -File scripts\test_remote_sessions.ps1 -Detailed" -ForegroundColor Gray

