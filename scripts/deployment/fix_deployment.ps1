# 修复部署脚本
# 使用方法: .\fix_deployment.ps1 -ServerIP <ip> [-Username <user>] [-Password <pass>]

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$Password = "8iDcGrYb52Fxpzee"
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "修复部署" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "服务器: $ServerIP`n" -ForegroundColor Cyan

# 检查 Posh-SSH 模块
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Install-Module -Name Posh-SSH -Force -Scope CurrentUser
}

Import-Module Posh-SSH

# 建立 SSH 连接
try {
    $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential($Username, $securePassword)
    $session = New-SSHSession -ComputerName $ServerIP -Credential $credential -AcceptKey
    
    if (-not $session) {
        Write-Host "✗ SSH 连接失败" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ SSH 连接成功`n" -ForegroundColor Green
} catch {
    Write-Host "✗ 连接错误: $_" -ForegroundColor Red
    exit 1
}

# 1. 创建缺失的目录
Write-Host "[1/5] 创建缺失的目录..." -ForegroundColor Cyan
Invoke-SSHCommand -SessionId $session.SessionId -Command @"
mkdir -p ~/telegram-ai-system/sessions
mkdir -p ~/telegram-ai-system/logs
mkdir -p ~/telegram-ai-system/backups
mkdir -p ~/telegram-ai-system/pids
chmod 700 ~/telegram-ai-system/sessions
"@ | Out-Null
Write-Host "✓ 目录已创建" -ForegroundColor Green

# 2. 检查并修复服务
Write-Host "[2/5] 检查并修复服务..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
# 检查服务是否运行
if pgrep -f 'uvicorn app.main:app' > /dev/null; then
    echo '服务已运行'
    pgrep -f 'uvicorn app.main:app'
else
    echo '服务未运行'
    # 尝试启动服务
    cd ~/telegram-ai-system
    if [ -d admin-backend ]; then
        cd admin-backend
        nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
        echo `$! > ../backend.pid
        echo '服务已启动'
    else
        echo 'admin-backend 目录不存在'
    fi
fi
"@
Write-Host $result.Output

# 3. 检查端口监听
Write-Host "[3/5] 检查端口监听..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
netstat -tuln 2>/dev/null | grep ':8000' || ss -tuln 2>/dev/null | grep ':8000' || echo '端口未监听'
"@
if ($result.Output -match ":8000") {
    Write-Host "✓ 端口 8000 正在监听" -ForegroundColor Green
} else {
    Write-Host "✗ 端口 8000 未监听，等待服务启动..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # 再次检查
    $result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
netstat -tuln 2>/dev/null | grep ':8000' || ss -tuln 2>/dev/null | grep ':8000' || echo '端口仍未监听'
"@
    if ($result.Output -match ":8000") {
        Write-Host "✓ 端口 8000 现在正在监听" -ForegroundColor Green
    } else {
        Write-Host "✗ 端口仍未监听，请检查服务日志" -ForegroundColor Red
    }
}

# 4. 验证健康检查
Write-Host "[4/5] 验证健康检查..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
curl -s http://localhost:8000/health 2>/dev/null || echo '健康检查失败'
"@
if ($result.Output -match "healthy|status") {
    Write-Host "✓ 健康检查通过" -ForegroundColor Green
    $result.Output | ConvertFrom-Json | ConvertTo-Json -Depth 2 | Write-Host -ForegroundColor Gray
} else {
    Write-Host "✗ 健康检查失败" -ForegroundColor Red
    Write-Host "  输出: $($result.Output)" -ForegroundColor Gray
    Write-Host "  提示: 查看日志文件 ~/telegram-ai-system/logs/backend.log" -ForegroundColor Yellow
}

# 5. 显示服务信息
Write-Host "[5/5] 显示服务信息..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
echo '=== 服务进程 ==='
ps aux | grep -E 'uvicorn|python.*main' | grep -v grep || echo '无服务进程'
echo ''
echo '=== 端口监听 ==='
netstat -tuln 2>/dev/null | grep ':8000' || ss -tuln 2>/dev/null | grep ':8000' || echo '端口未监听'
echo ''
echo '=== 日志文件 ==='
ls -lh ~/telegram-ai-system/logs/*.log 2>/dev/null | tail -3 || echo '无日志文件'
"@
Write-Host $result.Output

# 断开连接
Remove-SSHSession -SessionId $session.SessionId | Out-Null

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "修复完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "服务地址: http://${ServerIP}:8000" -ForegroundColor Cyan
Write-Host "API 文档: http://${ServerIP}:8000/docs`n" -ForegroundColor Cyan

