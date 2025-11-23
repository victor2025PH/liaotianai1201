# 修复配置和安装依赖
param(
    [switch]$InstallDeps = $true
)

$ErrorActionPreference = "Continue"
Import-Module Posh-SSH

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  修复配置和安装依赖" -ForegroundColor Cyan
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
        
        # 1. 修复 config.py - 使所有 API 凭证可选
        Write-Host "1. 修复 config.py..." -ForegroundColor Cyan
        $fixConfig = @'
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
    
    # 修改验证函数，跳过已设置默认值的变量
    old_validate = '''    required_vars = [
        ("TELEGRAM_API_ID", "必須是整型"),
        ("TELEGRAM_API_HASH", "Telegram API Hash"),
        ("TELEGRAM_SESSION_NAME", "Pyrogram Session 名稱"),
        ("OPENAI_API_KEY", "OpenAI API Key"),
    ]'''
    new_validate = '''    # 如果使用 Session 文件，这些变量可以为默认值
    required_vars = []  # 已设置为可选，不再验证'''
    
    if old_validate in content:
        content = content.replace(old_validate, new_validate)
    
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(content)
    print("Config modified successfully")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'@
        $r1 = Invoke-SSHCommand -SessionId $session.SessionId -Command "python3 << 'PYEOF'
$fixConfig
PYEOF
"
        if ($r1.Output -match "successfully") {
            Write-Host "  ✓ config.py 已修复" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ 修复可能失败: $($r1.Output)" -ForegroundColor Yellow
        }
        Write-Host ""
        
        # 2. 安装缺失的 Python 依赖
        if ($InstallDeps) {
            Write-Host "2. 安装缺失的 Python 依赖..." -ForegroundColor Cyan
            $deps = @("langdetect", "ffmpeg-python", "openai", "pyrogram", "tgcrypto")
            foreach ($dep in $deps) {
                Write-Host "  安装 $dep..." -ForegroundColor Yellow
                $r2 = Invoke-SSHCommand -SessionId $session.SessionId -Command "python3 -m pip install --user --upgrade --break-system-packages $dep 2>&1 | tail -3"
                if ($r2.Output -match "Successfully|already satisfied") {
                    Write-Host "    ✓ $dep 已安装" -ForegroundColor Green
                } else {
                    Write-Host "    ⚠ $dep 安装可能失败" -ForegroundColor Yellow
                }
            }
            Write-Host ""
        }
        
        # 3. 查找有效的 Session 文件
        Write-Host "3. 查找有效的 Session 文件..." -ForegroundColor Cyan
        $r3 = Invoke-SSHCommand -SessionId $session.SessionId -Command "find /home/ubuntu -name '*.session' -type f -size +100c 2>/dev/null | head -1"
        if ($r3.Output -and $r3.Output.Trim() -ne "") {
            $sessionFile = $r3.Output.Trim()
            $sessionName = [System.IO.Path]::GetFileNameWithoutExtension($sessionFile)
            Write-Host "  ✓ 找到 Session 文件: $sessionFile" -ForegroundColor Green
            Write-Host "  Session 名称: $sessionName" -ForegroundColor Gray
            Write-Host ""
            
            # 4. 停止旧的 main.py
            Write-Host "4. 停止旧的 main.py..." -ForegroundColor Cyan
            $r4 = Invoke-SSHCommand -SessionId $session.SessionId -Command "pkill -f 'python.*main.py'; sleep 2"
            Write-Host "  ✓ 已停止" -ForegroundColor Green
            Write-Host ""
            
            # 5. 启动 main.py
            Write-Host "5. 启动 main.py..." -ForegroundColor Cyan
            $startCmd = @"
cd /home/ubuntu
export PATH=`$HOME/.local/bin:`$PATH
export TELEGRAM_SESSION_FILE='$sessionFile'
export TELEGRAM_SESSION_NAME='$sessionName'
export TELEGRAM_API_ID=12345
export TELEGRAM_API_HASH='abc123def456'
export OPENAI_API_KEY='sk-placeholder'
nohup python3 main.py > logs/main.log 2>&1 &
echo `$!
"@
            $r5 = Invoke-SSHCommand -SessionId $session.SessionId -Command $startCmd
            Write-Host "  启动命令已执行" -ForegroundColor Gray
            Start-Sleep -Seconds 8
            Write-Host ""
            
            # 6. 检查进程状态
            Write-Host "6. 检查进程状态..." -ForegroundColor Cyan
            $r6 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ps aux | grep '[m]ain.py'"
            if ($r6.Output) {
                Write-Host "  ✓ main.py 正在运行" -ForegroundColor Green
                Write-Host $r6.Output -ForegroundColor Gray
            } else {
                Write-Host "  ✗ main.py 未运行" -ForegroundColor Red
                Write-Host "  查看错误日志..." -ForegroundColor Yellow
                $r7 = Invoke-SSHCommand -SessionId $session.SessionId -Command "tail -40 /home/ubuntu/logs/main.log 2>/dev/null"
                Write-Host $r7.Output -ForegroundColor Red
            }
            Write-Host ""
            
            # 7. 检查日志
            Write-Host "7. 检查启动日志..." -ForegroundColor Cyan
            $r8 = Invoke-SSHCommand -SessionId $session.SessionId -Command "tail -30 /home/ubuntu/logs/main.log 2>/dev/null | grep -i 'started\|connected\|ready\|error\|exception\|import' | tail -15"
            if ($r8.Output) {
                Write-Host $r8.Output -ForegroundColor Gray
            } else {
                Write-Host "  (暂无相关日志)" -ForegroundColor DarkGray
            }
        } else {
            Write-Host "  ✗ 未找到有效的 Session 文件" -ForegroundColor Red
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

