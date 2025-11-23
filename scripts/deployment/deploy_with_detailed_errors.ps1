# 详细错误报告的部署脚本
# 使用方法: .\deploy_with_detailed_errors.ps1 -ServerIP <ip> -Username <user> -Password <pass>

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$Password = "8iDcGrYb52Fxpzee",
    
    [Parameter(Mandatory=$false)]
    [string]$ServerName = "服务器"
)

$ErrorActionPreference = "Continue"
$errorLog = @()

function Log-Error {
    param([string]$Step, [string]$Error)
    $errorLog += "[$Step] $Error"
    Write-Host "✗ [$Step] $Error" -ForegroundColor Red
}

function Log-Success {
    param([string]$Step, [string]$Message)
    Write-Host "✓ [$Step] $Message" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "详细部署诊断 - $ServerName ($ServerIP)" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 检查 Posh-SSH 模块
Write-Host "[步骤 0] 检查环境..." -ForegroundColor Cyan
try {
    if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
        Write-Host "  安装 Posh-SSH 模块..." -ForegroundColor Yellow
        Install-Module -Name Posh-SSH -Force -Scope CurrentUser -ErrorAction Stop
    }
    Import-Module Posh-SSH -ErrorAction Stop
    Log-Success "步骤 0" "Posh-SSH 模块已加载"
} catch {
    Log-Error "步骤 0" "Posh-SSH 模块加载失败: $_"
    exit 1
}

# 测试连接
Write-Host "`n[步骤 1] 测试 SSH 连接..." -ForegroundColor Cyan
try {
    $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential($Username, $securePassword)
    
    Write-Host "  正在连接到 $ServerIP..." -ForegroundColor Gray
    $session = New-SSHSession -ComputerName $ServerIP -Credential $credential -AcceptKey -ConnectionTimeout 30
    
    if (-not $session) {
        Log-Error "步骤 1" "SSH 连接失败：无法建立会话"
        exit 1
    }
    
    Log-Success "步骤 1" "SSH 连接成功 (Session ID: $($session.SessionId))"
} catch {
    Log-Error "步骤 1" "SSH 连接错误: $_"
    Write-Host "  错误类型: $($_.Exception.GetType().Name)" -ForegroundColor Red
    Write-Host "  错误消息: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 检查系统环境
Write-Host "`n[步骤 2] 检查系统环境..." -ForegroundColor Cyan
try {
    $result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
echo '=== 系统信息 ==='
uname -a
echo ''
echo '=== Python ==='
python3 --version 2>&1 || echo 'Python 未安装'
echo ''
echo '=== 磁盘空间 ==='
df -h / | tail -1
"@
    
    if ($result.ExitStatus -eq 0) {
        Write-Host $result.Output
        Log-Success "步骤 2" "系统环境检查完成"
    } else {
        Log-Error "步骤 2" "系统环境检查失败: $($result.Error)"
    }
} catch {
    Log-Error "步骤 2" "系统环境检查异常: $_"
}

# 检查部署目录
Write-Host "`n[步骤 3] 检查部署目录..." -ForegroundColor Cyan
try {
    $result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
if [ -d ~/telegram-ai-system ]; then
    echo '目录存在'
    ls -la ~/telegram-ai-system | head -10
    echo ''
    echo '=== 关键文件检查 ==='
    [ -f ~/telegram-ai-system/main.py ] && echo 'main.py: 存在' || echo 'main.py: 不存在'
    [ -f ~/telegram-ai-system/admin-backend/app/main.py ] && echo 'admin-backend/app/main.py: 存在' || echo 'admin-backend/app/main.py: 不存在'
    [ -d ~/telegram-ai-system/sessions ] && echo 'sessions 目录: 存在' || echo 'sessions 目录: 不存在'
else
    echo '目录不存在'
fi
"@
    
    Write-Host $result.Output
    if ($result.Output -match "目录不存在") {
        Log-Error "步骤 3" "部署目录不存在"
    } else {
        Log-Success "步骤 3" "部署目录检查完成"
    }
} catch {
    Log-Error "步骤 3" "部署目录检查异常: $_"
}

# 检查服务状态
Write-Host "`n[步骤 4] 检查服务状态..." -ForegroundColor Cyan
try {
    $result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
echo '=== 进程检查 ==='
pgrep -f 'uvicorn' && echo 'uvicorn 进程: 运行中' || echo 'uvicorn 进程: 未运行'
pgrep -f 'python.*main.py' && echo 'main.py 进程: 运行中' || echo 'main.py 进程: 未运行'
echo ''
echo '=== 端口检查 ==='
netstat -tlnp 2>/dev/null | grep ':8000' || ss -tlnp 2>/dev/null | grep ':8000' || echo '端口 8000: 未监听'
"@
    
    Write-Host $result.Output
    Log-Success "步骤 4" "服务状态检查完成"
} catch {
    Log-Error "步骤 4" "服务状态检查异常: $_"
}

# 检查日志
Write-Host "`n[步骤 5] 检查日志..." -ForegroundColor Cyan
try {
    $result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
if [ -f ~/telegram-ai-system/logs/backend.log ]; then
    echo '=== 最近 20 行日志 ==='
    tail -20 ~/telegram-ai-system/logs/backend.log
else
    echo '日志文件不存在'
fi
"@
    
    Write-Host $result.Output
    Log-Success "步骤 5" "日志检查完成"
} catch {
    Log-Error "步骤 5" "日志检查异常: $_"
}

# 断开连接
Remove-SSHSession -SessionId $session.SessionId | Out-Null

# 输出错误摘要
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "错误摘要" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if ($errorLog.Count -eq 0) {
    Write-Host "✓ 未发现错误" -ForegroundColor Green
} else {
    Write-Host "发现 $($errorLog.Count) 个错误:" -ForegroundColor Red
    foreach ($error in $errorLog) {
        Write-Host "  $error" -ForegroundColor Yellow
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "诊断完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

