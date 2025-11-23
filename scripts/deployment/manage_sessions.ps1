# Session 管理脚本
# 使用方法: .\manage_sessions.ps1 -Action <list|start|stop|status> [-ServerIP <ip>]

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("list", "start", "stop", "status", "upload")]
    [string]$Action,
    
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "",
    
    [Parameter(Mandatory=$false)]
    [string]$SessionFile = ""
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

# 检查 Posh-SSH 模块
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Install-Module -Name Posh-SSH -Force -Scope CurrentUser
}

Import-Module Posh-SSH

# 选择服务器
$targetServers = if ($ServerIP) {
    $servers | Where-Object { $_.IP -eq $ServerIP }
} else {
    $servers
}

foreach ($server in $targetServers) {
    Write-Host "`n$($server.Name) ($($server.IP))" -ForegroundColor Yellow
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
    
    switch ($Action) {
        "list" {
            Write-Host "Session 文件列表:" -ForegroundColor Cyan
            $result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
ls -lh ~/telegram-ai-system/sessions/*.session ~/telegram-ai-system/sessions/*.enc 2>/dev/null | awk '{print `$9, `$5}'
"@
            if ($result.Output) {
                $result.Output | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            } else {
                Write-Host "  无 Session 文件" -ForegroundColor Gray
            }
        }
        
        "status" {
            Write-Host "运行中的 Session:" -ForegroundColor Cyan
            $result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
ps aux | grep -E 'python.*session|uvicorn.*session' | grep -v grep || echo '无运行中的 Session'
"@
            if ($result.Output -and $result.Output -notmatch "无运行中的") {
                $result.Output | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            } else {
                Write-Host "  无运行中的 Session" -ForegroundColor Gray
            }
            
            # 检查 systemd 服务
            $result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
if command -v systemctl &> /dev/null; then
    sudo systemctl status telegram-ai-sessions.service --no-pager 2>/dev/null | head -10 || echo '服务未安装'
else
    echo 'systemctl 不可用'
fi
"@
            Write-Host "`nSystemd 服务状态:" -ForegroundColor Cyan
            $result.Output | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        }
        
        "start" {
            Write-Host "启动自动运行服务..." -ForegroundColor Cyan
            $result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
if [ -f ~/telegram-ai-system/auto_start_sessions.sh ]; then
    bash ~/telegram-ai-system/auto_start_sessions.sh
    echo '启动完成'
else
    echo '自动运行脚本不存在'
fi
"@
            Write-Host $result.Output
        }
        
        "stop" {
            Write-Host "停止所有 Session..." -ForegroundColor Cyan
            $result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
pkill -f 'python.*session' || true
if [ -d ~/telegram-ai-system/pids ]; then
    kill `$(cat ~/telegram-ai-system/pids/*.pid 2>/dev/null) 2>/dev/null || true
fi
echo '已停止所有 Session'
"@
            Write-Host $result.Output
        }
        
        "upload" {
            if (-not $SessionFile -or -not (Test-Path $SessionFile)) {
                Write-Host "✗ Session 文件不存在: $SessionFile" -ForegroundColor Red
                Remove-SSHSession -SessionId $session.SessionId | Out-Null
                continue
            }
            
            Write-Host "上传 Session 文件: $(Split-Path $SessionFile -Leaf)..." -ForegroundColor Cyan
            try {
                Set-SCPFile -SessionId $session.SessionId `
                    -LocalFile $SessionFile `
                    -RemotePath "~/telegram-ai-system/sessions/" `
                    -ErrorAction Stop
                
                Invoke-SSHCommand -SessionId $session.SessionId -Command @"
chmod 600 ~/telegram-ai-system/sessions/$(Split-Path $SessionFile -Leaf)
"@ | Out-Null
                
                Write-Host "✓ 上传成功" -ForegroundColor Green
            } catch {
                Write-Host "✗ 上传失败: $_" -ForegroundColor Red
            }
        }
    }
    
    Remove-SSHSession -SessionId $session.SessionId | Out-Null
}

