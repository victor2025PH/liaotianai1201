# 分布式 Session 文件上传脚本
# 使用方法: .\distribute_sessions.ps1 -SessionDir <dir> [-SessionsPerServer <count>]

param(
    [Parameter(Mandatory=$false)]
    [string]$SessionDir = "sessions",
    
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
Write-Host "分布式 Session 文件上传" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 检查 Posh-SSH 模块
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Write-Host "安装 Posh-SSH 模块..." -ForegroundColor Yellow
    Install-Module -Name Posh-SSH -Force -Scope CurrentUser
}

Import-Module Posh-SSH

# 获取所有 Session 文件
$sessionFiles = Get-ChildItem -Path $SessionDir -Filter "*.session" -ErrorAction SilentlyContinue
$encFiles = Get-ChildItem -Path $SessionDir -Filter "*.enc" -ErrorAction SilentlyContinue
$allSessions = @($sessionFiles) + @($encFiles)

if ($allSessions.Count -eq 0) {
    Write-Host "✗ 未找到 Session 文件" -ForegroundColor Red
    exit 1
}

Write-Host "找到 $($allSessions.Count) 个 Session 文件`n" -ForegroundColor Green

# 分配 Session 文件到服务器
$serverIndex = 0
$sessionIndex = 0
$serverSessions = @{}

foreach ($server in $servers) {
    $serverSessions[$server.IP] = @()
}

foreach ($session in $allSessions) {
    $server = $servers[$serverIndex]
    $serverSessions[$server.IP] += $session
    
    $sessionIndex++
    if ($sessionIndex -ge $SessionsPerServer) {
        $sessionIndex = 0
        $serverIndex = ($serverIndex + 1) % $servers.Count
    }
}

# 上传 Session 文件到每个服务器
foreach ($server in $servers) {
    Write-Host "`n上传到: $($server.Name) ($($server.IP))" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    
    $sessions = $serverSessions[$server.IP]
    Write-Host "分配 $($sessions.Count) 个 Session 文件" -ForegroundColor Cyan
    
    if ($sessions.Count -eq 0) {
        Write-Host "跳过（无 Session 文件）" -ForegroundColor Gray
        continue
    }
    
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
    
    # 创建 Session 目录
    Invoke-SSHCommand -SessionId $session.SessionId -Command @"
mkdir -p ~/telegram-ai-system/sessions
chmod 700 ~/telegram-ai-system/sessions
"@ | Out-Null
    
    # 上传每个 Session 文件
    $uploaded = 0
    foreach ($sessionFile in $sessions) {
        try {
            Write-Host "  上传: $($sessionFile.Name)..." -ForegroundColor Gray -NoNewline
            
            Set-SCPFile -SessionId $session.SessionId `
                -LocalFile $sessionFile.FullName `
                -RemotePath "~/telegram-ai-system/sessions/" `
                -ErrorAction Stop
            
            # 设置文件权限
            Invoke-SSHCommand -SessionId $session.SessionId -Command @"
chmod 600 ~/telegram-ai-system/sessions/$($sessionFile.Name)
"@ | Out-Null
            
            Write-Host " ✓" -ForegroundColor Green
            $uploaded++
        } catch {
            Write-Host " ✗" -ForegroundColor Red
            Write-Host "    错误: $_" -ForegroundColor Red
        }
    }
    
    Write-Host "✓ 成功上传 $uploaded/$($sessions.Count) 个文件" -ForegroundColor Green
    
    # 验证上传的文件
    $result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
ls -lh ~/telegram-ai-system/sessions/*.session ~/telegram-ai-system/sessions/*.enc 2>/dev/null | wc -l
"@
    $fileCount = [int]($result.Output.Trim())
    Write-Host "  服务器上现有 Session 文件: $fileCount" -ForegroundColor Gray
    
    # 断开连接
    Remove-SSHSession -SessionId $session.SessionId | Out-Null
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Session 文件上传完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "分配统计:" -ForegroundColor Yellow
foreach ($server in $servers) {
    $count = $serverSessions[$server.IP].Count
    Write-Host "  • $($server.Name): $count 个 Session 文件" -ForegroundColor Cyan
}

