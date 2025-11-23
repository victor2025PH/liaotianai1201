# 更新所有服务器的 API 凭证
$ErrorActionPreference = "Continue"
Import-Module Posh-SSH

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  更新所有服务器的 API 凭证" -ForegroundColor Cyan
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
        
        # 1. 更新 config.py 使用真实的 API 凭证
        Write-Host "1. 更新 config.py 使用真实的 API 凭证..." -ForegroundColor Cyan
        $updateConfig = @"
import sys
config_file = "/home/ubuntu/config.py"
try:
    with open(config_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 更新为真实的 API 凭证
    content = content.replace(
        'API_ID = _get_int_env("TELEGRAM_API_ID", default=12345, required=False)',
        'API_ID = _get_int_env("TELEGRAM_API_ID", default=24782266, required=False)'
    )
    content = content.replace(
        'API_HASH = _get_env("TELEGRAM_API_HASH", default="abc123def456", required=False)',
        'API_HASH = _get_env("TELEGRAM_API_HASH", default="48ccfcd14b237d4f6753c122f6a798606", required=False)'
    )
    
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(content)
    print("Config updated successfully")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"@
        $r1 = Invoke-SSHCommand -SessionId $session.SessionId -Command "python3 << 'PYEOF'
$updateConfig
PYEOF
"
        if ($r1.Output -match "successfully") {
            Write-Host "  ✓ config.py 已更新" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ 更新可能失败: $($r1.Output)" -ForegroundColor Yellow
        }
        Write-Host ""
        
        # 2. 检查 Session 文件
        Write-Host "2. 检查 Session 文件..." -ForegroundColor Cyan
        $r2 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ls -lh /home/ubuntu/sessions/*.session 2>/dev/null | head -10"
        if ($r2.Output) {
            Write-Host "  ✓ 找到 Session 文件:" -ForegroundColor Green
            Write-Host $r2.Output -ForegroundColor Gray
        } else {
            Write-Host "  ⚠ 未找到 Session 文件" -ForegroundColor Yellow
        }
        Write-Host ""
        
        # 3. 停止旧的 main.py
        Write-Host "3. 停止旧的 main.py..." -ForegroundColor Cyan
        $r3 = Invoke-SSHCommand -SessionId $session.SessionId -Command "pkill -f 'python.*main.py'; sleep 2"
        Write-Host "  ✓ 已停止" -ForegroundColor Green
        Write-Host ""
        
        # 4. 启动 main.py 使用真实的 API 凭证
        Write-Host "4. 启动 main.py 使用真实的 API 凭证..." -ForegroundColor Cyan
        $startCmd = @"
cd /home/ubuntu
export PATH=`$HOME/.local/bin:`$PATH
export TELEGRAM_API_ID=$API_ID
export TELEGRAM_API_HASH='$API_HASH'
export OPENAI_API_KEY='sk-placeholder'
nohup python3 main.py > logs/main.log 2>&1 &
echo `$!
"@
        $r4 = Invoke-SSHCommand -SessionId $session.SessionId -Command $startCmd
        Write-Host "  启动命令已执行" -ForegroundColor Gray
        Start-Sleep -Seconds 8
        Write-Host ""
        
        # 5. 检查进程状态
        Write-Host "5. 检查进程状态..." -ForegroundColor Cyan
        $r5 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ps aux | grep '[m]ain.py'"
        if ($r5.Output) {
            Write-Host "  ✓ main.py 正在运行" -ForegroundColor Green
            Write-Host $r5.Output -ForegroundColor Gray
        } else {
            Write-Host "  ✗ main.py 未运行" -ForegroundColor Red
            Write-Host "  查看错误日志..." -ForegroundColor Yellow
            $r6 = Invoke-SSHCommand -SessionId $session.SessionId -Command "tail -40 /home/ubuntu/logs/main.log 2>/dev/null"
            Write-Host $r6.Output -ForegroundColor Red
        }
        Write-Host ""
        
        # 6. 检查启动日志
        Write-Host "6. 检查启动日志..." -ForegroundColor Cyan
        $r7 = Invoke-SSHCommand -SessionId $session.SessionId -Command "tail -30 /home/ubuntu/logs/main.log 2>/dev/null | grep -i 'started\|connected\|ready\|error\|exception\|authorized' | tail -15"
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
Write-Host "  更新完成" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "API 凭证已更新:" -ForegroundColor Green
Write-Host "  API_ID: $API_ID" -ForegroundColor Gray
Write-Host "  API_HASH: $API_HASH" -ForegroundColor Gray
Write-Host ""
Write-Host "提示: 运行测试脚本查看详细状态" -ForegroundColor Yellow
Write-Host "  pwsh -ExecutionPolicy Bypass -File scripts\test_remote_sessions.ps1 -Detailed" -ForegroundColor Gray

