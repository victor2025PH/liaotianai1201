# 修复远程服务器的环境变量并启动 main.py
param(
    [switch]$StartMain = $true
)

$ErrorActionPreference = "Continue"
Import-Module Posh-SSH

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  修复远程服务器环境变量并启动 main.py" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 读取本地环境变量作为参考
$localEnvFile = "docs/env.example"
if (Test-Path $localEnvFile) {
    Write-Host "读取本地环境变量模板..." -ForegroundColor Yellow
    $envTemplate = Get-Content $localEnvFile -Raw
    Write-Host "✓ 已读取环境变量模板" -ForegroundColor Green
} else {
    Write-Host "⚠ 未找到环境变量模板文件" -ForegroundColor Yellow
}

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
        
        # 1. 检查 .env 文件
        Write-Host "1. 检查 .env 文件..." -ForegroundColor Cyan
        $r1 = Invoke-SSHCommand -SessionId $session.SessionId -Command "test -f /home/ubuntu/.env && echo 'exists' || echo 'not exists'"
        if ($r1.Output -match "exists") {
            Write-Host "  ✓ .env 文件存在" -ForegroundColor Green
            $r1a = Invoke-SSHCommand -SessionId $session.SessionId -Command "grep -E 'TELEGRAM_API_ID|TELEGRAM_API_HASH' /home/ubuntu/.env 2>/dev/null | head -2"
            if ($r1a.Output) {
                Write-Host "  当前配置:" -ForegroundColor Gray
                Write-Host $r1a.Output -ForegroundColor Gray
            } else {
                Write-Host "  ⚠ 未找到 TELEGRAM_API_ID 或 TELEGRAM_API_HASH" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  ✗ .env 文件不存在" -ForegroundColor Red
            Write-Host "  提示: 需要在服务器上创建 .env 文件并配置 TELEGRAM_API_ID 和 TELEGRAM_API_HASH" -ForegroundColor Yellow
        }
        Write-Host ""
        
        # 2. 检查 config.py 中的默认值
        Write-Host "2. 检查 config.py..." -ForegroundColor Cyan
        $r2 = Invoke-SSHCommand -SessionId $session.SessionId -Command "test -f /home/ubuntu/config.py && echo 'exists' || echo 'not exists'"
        if ($r2.Output -match "exists") {
            Write-Host "  ✓ config.py 存在" -ForegroundColor Green
            $r2a = Invoke-SSHCommand -SessionId $session.SessionId -Command "grep -A 2 'TELEGRAM_API_ID' /home/ubuntu/config.py | head -5"
            if ($r2a.Output) {
                Write-Host "  配置要求:" -ForegroundColor Gray
                Write-Host $r2a.Output -ForegroundColor Gray
            }
        } else {
            Write-Host "  ✗ config.py 不存在" -ForegroundColor Red
        }
        Write-Host ""
        
        # 3. 检查是否有环境变量设置脚本
        Write-Host "3. 检查环境变量..." -ForegroundColor Cyan
        $r3 = Invoke-SSHCommand -SessionId $session.SessionId -Command "env | grep -E 'TELEGRAM_API_ID|TELEGRAM_API_HASH' || echo 'not set'"
        if ($r3.Output -notmatch "not set") {
            Write-Host "  ✓ 环境变量已设置" -ForegroundColor Green
            Write-Host $r3.Output -ForegroundColor Gray
        } else {
            Write-Host "  ✗ 环境变量未设置" -ForegroundColor Red
        }
        Write-Host ""
        
        # 4. 尝试启动 main.py（如果环境变量已配置）
        if ($StartMain) {
            Write-Host "4. 尝试启动 main.py..." -ForegroundColor Cyan
            $r4 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ps aux | grep '[m]ain.py'"
            if ($r4.Output) {
                Write-Host "  ✓ main.py 已在运行" -ForegroundColor Green
                Write-Host $r4.Output -ForegroundColor Gray
            } else {
                Write-Host "  启动 main.py..." -ForegroundColor Yellow
                # 创建启动脚本，包含环境变量
                $startScript = @'
#!/bin/bash
cd /home/ubuntu
export PATH=$HOME/.local/bin:$PATH
# 如果 .env 文件存在，加载它
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi
nohup python3 main.py > logs/main.log 2>&1 &
echo $!
'@
                $r4a = Invoke-SSHCommand -SessionId $session.SessionId -Command "cat > /tmp/start_main.sh << 'SCRIPTEOF'
$startScript
SCRIPTEOF
chmod +x /tmp/start_main.sh"
                
                $r4b = Invoke-SSHCommand -SessionId $session.SessionId -Command "bash /tmp/start_main.sh"
                Start-Sleep -Seconds 3
                
                $r4c = Invoke-SSHCommand -SessionId $session.SessionId -Command "ps aux | grep '[m]ain.py'"
                if ($r4c.Output) {
                    Write-Host "  ✓ main.py 已启动" -ForegroundColor Green
                    Write-Host $r4c.Output -ForegroundColor Gray
                } else {
                    Write-Host "  ✗ main.py 启动失败，查看日志:" -ForegroundColor Red
                    $r4d = Invoke-SSHCommand -SessionId $session.SessionId -Command "tail -20 /home/ubuntu/logs/main.log 2>/dev/null"
                    Write-Host $r4d.Output -ForegroundColor Red
                }
            }
            Write-Host ""
        }
        
        # 5. 显示当前状态
        Write-Host "5. 当前状态..." -ForegroundColor Cyan
        $r5 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ps aux | grep -E '[m]ain.py|[u]vicorn' | head -5"
        if ($r5.Output) {
            Write-Host "  运行中的进程:" -ForegroundColor Green
            Write-Host $r5.Output -ForegroundColor Gray
        } else {
            Write-Host "  ✗ 没有相关进程运行" -ForegroundColor Red
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
Write-Host ""
Write-Host "注意: 如果 main.py 启动失败，请检查:" -ForegroundColor Yellow
Write-Host "  1. .env 文件中是否配置了 TELEGRAM_API_ID 和 TELEGRAM_API_HASH" -ForegroundColor Yellow
Write-Host "  2. Session 文件是否有效" -ForegroundColor Yellow
Write-Host "  3. 网络连接是否正常" -ForegroundColor Yellow

