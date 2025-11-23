# 设置自动运行 Session 脚本
# 使用方法: .\setup_auto_sessions.ps1 [-SessionsPerServer <count>]

param(
    [Parameter(Mandatory=$false)]
    [int]$SessionsPerServer = 4
)

$ErrorActionPreference = "Continue"

# 服务器配置
$servers = @(
    @{
        Name = "洛杉矶服务器"
        IP = "165.154.255.48"
        Username = "ubuntu"
        Password = "8iDcGrYb52Fxpzee"
    },
    @{
        Name = "马尼拉服务器"
        IP = "165.154.233.179"
        Username = "ubuntu"
        Password = "8iDcGrYb52Fxpzee"
    }
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "设置自动运行 Session" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 检查 Posh-SSH 模块
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Write-Host "安装 Posh-SSH 模块..." -ForegroundColor Yellow
    Install-Module -Name Posh-SSH -Force -Scope CurrentUser
}

Import-Module Posh-SSH

foreach ($server in $servers) {
    Write-Host "`n设置: $($server.Name) ($($server.IP))" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    
    # 建立 SSH 连接
    try {
        $securePassword = ConvertTo-SecureString $server.Password -AsPlainText -Force
        $credential = New-Object System.Management.Automation.PSCredential($server.Username, $securePassword)
        $session = New-SSHSession -ComputerName $server.IP -Credential $credential -AcceptKey
        
        if (-not $session) {
            Write-Host "✗ SSH 连接失败" -ForegroundColor Red
            continue
        }
    } catch {
        Write-Host "✗ 连接错误: $_" -ForegroundColor Red
        continue
    }
    
    # 获取 Session 文件列表
    $result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
ls ~/telegram-ai-system/sessions/*.session ~/telegram-ai-system/sessions/*.enc 2>/dev/null | head -$SessionsPerServer
"@
    
    $sessionFiles = $result.Output | Where-Object { $_ -match "\.(session|enc)$" }
    
    if ($sessionFiles.Count -eq 0) {
        Write-Host "✗ 未找到 Session 文件" -ForegroundColor Red
        Remove-SSHSession -SessionId $session.SessionId | Out-Null
        continue
    }
    
    Write-Host "找到 $($sessionFiles.Count) 个 Session 文件" -ForegroundColor Green
    
    # 创建自动运行脚本
    $autoRunScript = @"
#!/bin/bash
# 自动运行 Session 脚本
# 由 setup_auto_sessions.ps1 生成

cd ~/telegram-ai-system

# Session 文件列表
SESSIONS=(
$($sessionFiles | ForEach-Object { "    `"$(Split-Path $_ -Leaf)`"" } | Join-String -Separator "`n")
)

# 运行每个 Session
for SESSION in `"`${SESSIONS[@]}`"; do
    SESSION_NAME=`$(basename `"`$SESSION`" .session | sed 's/.enc$//')
    echo "启动 Session: `$SESSION_NAME"
    
    # 使用 Python 脚本启动（需要根据实际项目调整）
    cd admin-backend
    nohup python3 -c "
import sys
sys.path.insert(0, '..')
from group_ai_service.account_manager import AccountManager
from group_ai_service.config import get_group_ai_config

config = get_group_ai_config()
manager = AccountManager(config)
account = manager.get_account('`$SESSION_NAME')
if account:
    account.start()
" > ../logs/session_`$SESSION_NAME.log 2>&1 &
    
    echo `$! > ../pids/session_`$SESSION_NAME.pid
    cd ..
    
    sleep 2
done

echo "所有 Session 已启动"
"@
    
    # 上传自动运行脚本
    $scriptPath = [System.IO.Path]::GetTempFileName()
    $autoRunScript | Out-File -FilePath $scriptPath -Encoding UTF8
    
    try {
        Set-SCPFile -SessionId $session.SessionId `
            -LocalFile $scriptPath `
            -RemotePath "~/telegram-ai-system/auto_start_sessions.sh" `
            -ErrorAction Stop
        
        # 设置执行权限
        Invoke-SSHCommand -SessionId $session.SessionId -Command @"
chmod +x ~/telegram-ai-system/auto_start_sessions.sh
mkdir -p ~/telegram-ai-system/pids
mkdir -p ~/telegram-ai-system/logs
"@ | Out-Null
        
        Write-Host "✓ 自动运行脚本已创建" -ForegroundColor Green
    } catch {
        Write-Host "✗ 上传脚本失败: $_" -ForegroundColor Red
    }
    
    # 创建 systemd 服务（可选）
    $systemdService = @"
[Unit]
Description=Telegram AI Auto Sessions
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/telegram-ai-system
ExecStart=/home/ubuntu/telegram-ai-system/auto_start_sessions.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"@
    
    $servicePath = [System.IO.Path]::GetTempFileName()
    $systemdService | Out-File -FilePath $servicePath -Encoding UTF8
    
    try {
        Set-SCPFile -SessionId $session.SessionId `
            -LocalFile $servicePath `
            -RemotePath "/tmp/telegram-ai-sessions.service" `
            -ErrorAction Stop
        
        # 安装 systemd 服务（需要 sudo）
        Invoke-SSHCommand -SessionId $session.SessionId -Command @"
sudo mv /tmp/telegram-ai-sessions.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-ai-sessions.service
sudo systemctl start telegram-ai-sessions.service
"@ | Out-Null
        
        Write-Host "✓ Systemd 服务已安装" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Systemd 服务安装失败（可能需要手动配置）" -ForegroundColor Yellow
    }
    
    # 清理临时文件
    Remove-Item $scriptPath -ErrorAction SilentlyContinue
    Remove-Item $servicePath -ErrorAction SilentlyContinue
    
    # 验证服务状态
    $result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
if command -v systemctl &> /dev/null; then
    sudo systemctl status telegram-ai-sessions.service --no-pager | head -5
else
    echo "systemctl 不可用"
fi
"@
    Write-Host "服务状态:" -ForegroundColor Gray
    $result.Output | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    
    # 断开连接
    Remove-SSHSession -SessionId $session.SessionId | Out-Null
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "自动运行 Session 设置完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "每个服务器将自动运行 $SessionsPerServer 个 Session" -ForegroundColor Green
Write-Host "`n管理命令:" -ForegroundColor Yellow
Write-Host "  查看状态: ssh ubuntu@<ip> 'sudo systemctl status telegram-ai-sessions'" -ForegroundColor Gray
Write-Host "  启动服务: ssh ubuntu@<ip> 'sudo systemctl start telegram-ai-sessions'" -ForegroundColor Gray
Write-Host "  停止服务: ssh ubuntu@<ip> 'sudo systemctl stop telegram-ai-sessions'" -ForegroundColor Gray
Write-Host "  查看日志: ssh ubuntu@<ip> 'tail -f ~/telegram-ai-system/logs/session_*.log'" -ForegroundColor Gray

