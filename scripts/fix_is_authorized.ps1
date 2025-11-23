# 修复 is_authorized 问题
$ErrorActionPreference = "Continue"
Import-Module Posh-SSH

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  修复 is_authorized 问题" -ForegroundColor Cyan
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
        
        # 修复 main.py 中的 is_authorized 问题
        Write-Host "1. 修复 main.py 中的 is_authorized 问题..." -ForegroundColor Cyan
        $fixCode = @'
import sys
main_file = "/home/ubuntu/main.py"
try:
    with open(main_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 替换 is_authorized() 调用
    old_code = '''                try:
                    if not await app.is_authorized():
                        await app.disconnect()
                        raise SessionError(f"Session {session_name} 未授權，請先登錄")
                    
                    me = await app.get_me()'''
    
    new_code = '''                try:
                    # 使用 get_me() 来检查是否已授权
                    # 如果未授权，会抛出 AuthKeyUnregistered 异常
                    me = await app.get_me()'''
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        with open(main_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("Fixed successfully")
    else:
        print("Already fixed or pattern not found")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'@
        $r1 = Invoke-SSHCommand -SessionId $session.SessionId -Command "python3 << 'PYEOF'
$fixCode
PYEOF
"
        if ($r1.Output -match "successfully|Already fixed") {
            Write-Host "  ✓ main.py 已修复" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ 修复可能失败: $($r1.Output)" -ForegroundColor Yellow
        }
        Write-Host ""
        
        # 停止旧的 main.py
        Write-Host "2. 停止旧的 main.py..." -ForegroundColor Cyan
        $r2 = Invoke-SSHCommand -SessionId $session.SessionId -Command "pkill -f 'python.*main.py'; sleep 2"
        Write-Host "  ✓ 已停止" -ForegroundColor Green
        Write-Host ""
        
        # 启动 main.py
        Write-Host "3. 启动 main.py..." -ForegroundColor Cyan
        $startCmd = @"
cd /home/ubuntu
export PATH=`$HOME/.local/bin:`$PATH
export TELEGRAM_API_ID=24782266
export TELEGRAM_API_HASH='48ccfcd14b237d4f6753c122f6a798606'
export OPENAI_API_KEY='sk-placeholder'
nohup python3 main.py > logs/main.log 2>&1 &
echo `$!
"@
        $r3 = Invoke-SSHCommand -SessionId $session.SessionId -Command $startCmd
        Write-Host "  启动命令已执行" -ForegroundColor Gray
        Start-Sleep -Seconds 8
        Write-Host ""
        
        # 检查进程状态
        Write-Host "4. 检查进程状态..." -ForegroundColor Cyan
        $r4 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ps aux | grep '[m]ain.py'"
        if ($r4.Output) {
            Write-Host "  ✓ main.py 正在运行" -ForegroundColor Green
            Write-Host $r4.Output -ForegroundColor Gray
        } else {
            Write-Host "  ✗ main.py 未运行" -ForegroundColor Red
        }
        Write-Host ""
        
        # 检查日志
        Write-Host "5. 检查启动日志..." -ForegroundColor Cyan
        $r5 = Invoke-SSHCommand -SessionId $session.SessionId -Command "tail -40 /home/ubuntu/logs/main.log 2>/dev/null | grep -i 'started\|connected\|ready\|error\|exception\|authorized\|驗證成功' | tail -15"
        if ($r5.Output) {
            Write-Host $r5.Output -ForegroundColor Gray
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
Write-Host "  修复完成" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

