# 检查 worker-01 (165.154.254.99) 服务器状态
# 使用正确的配置：密码 Along2025!!!，部署目录 /opt/group-ai

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "165.154.254.99",
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$Password = "Along2025!!!",
    
    [Parameter(Mandatory=$false)]
    [string]$DeployDir = "/opt/group-ai"
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "检查 worker-01 服务器状态" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "服务器: $ServerIP" -ForegroundColor Cyan
Write-Host "部署目录: $DeployDir`n" -ForegroundColor Cyan

# 检查 Posh-SSH 模块
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Install-Module -Name Posh-SSH -Force -Scope CurrentUser
}
Import-Module Posh-SSH

# 建立 SSH 连接
try {
    $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential($Username, $securePassword)
    $session = New-SSHSession -ComputerName $ServerIP -Credential $credential -AcceptKey -ConnectionTimeout 30
    
    if (-not $session) {
        Write-Host "✗ SSH 连接失败" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ SSH 连接成功`n" -ForegroundColor Green
} catch {
    Write-Host "✗ 连接错误: $_" -ForegroundColor Red
    exit 1
}

# 检查部署目录
Write-Host "[1/10] 检查部署目录..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command "test -d $DeployDir && echo '存在' || echo '不存在'"
if ($result.Output -match "存在") {
    Write-Host "✓ 部署目录存在: $DeployDir" -ForegroundColor Green
    
    # 列出目录内容
    $listResult = Invoke-SSHCommand -SessionId $session.SessionId -Command "ls -la $DeployDir | head -20"
    Write-Host $listResult.Output
} else {
    Write-Host "✗ 部署目录不存在: $DeployDir" -ForegroundColor Red
}
Write-Host ""

# 检查关键文件
Write-Host "[2/10] 检查关键文件..." -ForegroundColor Cyan
$files = @(
    "main.py",
    "config.py",
    "requirements.txt",
    ".env"
)

foreach ($file in $files) {
    $result = Invoke-SSHCommand -SessionId $session.SessionId -Command "test -f $DeployDir/$file && echo '存在' || echo '不存在'"
    if ($result.Output -match "存在") {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file" -ForegroundColor Red
    }
}
Write-Host ""

# 检查 systemd 服务
Write-Host "[3/10] 检查 systemd 服务..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command "systemctl is-active group-ai-worker 2>/dev/null || echo 'inactive'"
$serviceStatus = $result.Output.Trim()
if ($serviceStatus -eq "active") {
    Write-Host "✓ 服务状态: active" -ForegroundColor Green
} else {
    Write-Host "✗ 服务状态: $serviceStatus" -ForegroundColor Red
}

# 检查服务详细信息
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command "systemctl status group-ai-worker --no-pager -l | head -15"
Write-Host $result.Output
Write-Host ""

# 检查进程
Write-Host "[4/10] 检查运行进程..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
pgrep -f 'uvicorn' && echo 'uvicorn 运行中' || echo 'uvicorn 未运行'
pgrep -f 'python.*main.py' && echo 'main.py 运行中' || echo 'main.py 未运行'
"@
Write-Host $result.Output
Write-Host ""

# 检查端口监听
Write-Host "[5/10] 检查端口监听..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
if command -v netstat &> /dev/null; then
    netstat -tlnp 2>/dev/null | grep ':8000' || echo '端口 8000 未监听'
elif command -v ss &> /dev/null; then
    ss -tlnp 2>/dev/null | grep ':8000' || echo '端口 8000 未监听'
else
    echo '无法检查端口状态'
fi
"@
Write-Host $result.Output
Write-Host ""

# 检查健康检查
Write-Host "[6/10] 检查健康检查..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command "curl -s http://localhost:8000/health 2>&1 | head -5 || echo '健康检查失败'"
Write-Host $result.Output
Write-Host ""

# 检查 Session 目录
Write-Host "[7/10] 检查 Session 目录..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
if [ -d $DeployDir/sessions ]; then
    echo '目录存在'
    ls -lh $DeployDir/sessions/*.session 2>/dev/null | wc -l
    echo '个 Session 文件'
else
    echo '目录不存在'
fi
"@
Write-Host $result.Output
Write-Host ""

# 检查日志
Write-Host "[8/10] 检查日志文件..." -ForegroundColor Cyan
$logFiles = @(
    "$DeployDir/logs/worker.log",
    "$DeployDir/logs/backend.log",
    "/var/log/group-ai/worker-01.log"
)

foreach ($logFile in $logFiles) {
    $result = Invoke-SSHCommand -SessionId $session.SessionId -Command "test -f $logFile && echo '存在' || echo '不存在'"
    if ($result.Output -match "存在") {
        Write-Host "  ✓ $logFile" -ForegroundColor Green
        # 显示最后几行
        $tailResult = Invoke-SSHCommand -SessionId $session.SessionId -Command "tail -5 $logFile"
        Write-Host "    最近日志:" -ForegroundColor Gray
        $tailResult.Output -split "`n" | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    } else {
        Write-Host "  ✗ $logFile" -ForegroundColor Red
    }
}
Write-Host ""

# 检查 Python 环境
Write-Host "[9/10] 检查 Python 环境..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
python3 --version
if [ -d $DeployDir/venv ]; then
    echo '虚拟环境存在'
    $DeployDir/venv/bin/python --version 2>&1
else
    echo '虚拟环境不存在'
fi
"@
Write-Host $result.Output
Write-Host ""

# 检查磁盘空间
Write-Host "[10/10] 检查磁盘空间..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command "df -h $DeployDir"
Write-Host $result.Output
Write-Host ""

# 断开连接
Remove-SSHSession -SessionId $session.SessionId | Out-Null

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "检查完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

