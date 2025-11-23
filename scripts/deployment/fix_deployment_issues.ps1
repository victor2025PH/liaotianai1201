# 修复部署问题的脚本
# 使用方法: .\fix_deployment_issues.ps1 -ServerIP <ip> -Username <user> -Password <pass>

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

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "修复部署问题 - $ServerName ($ServerIP)" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

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

# 修复步骤 1: 停止现有服务
Write-Host "[1/6] 停止现有服务..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
echo '停止现有服务...'
pkill -f 'uvicorn' || true
pkill -f 'python.*main.py' || true
sleep 2
pgrep -f 'uvicorn' && echo '仍有进程运行' || echo '所有进程已停止'
"@
Write-Host $result.Output
if ($result.ExitStatus -eq 0) {
    Write-Host "✓ 服务已停止`n" -ForegroundColor Green
} else {
    Write-Host "⚠ 停止服务时出现警告`n" -ForegroundColor Yellow
}

# 修复步骤 2: 创建必要目录
Write-Host "[2/6] 创建必要目录..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd ~/telegram-ai-system
mkdir -p sessions
mkdir -p logs
chmod 700 sessions
chmod 755 logs
echo '目录创建完成'
ls -ld sessions logs
"@
Write-Host $result.Output
if ($result.ExitStatus -eq 0) {
    Write-Host "✓ 目录创建成功`n" -ForegroundColor Green
} else {
    Write-Host "✗ 目录创建失败`n" -ForegroundColor Red
}

# 修复步骤 3: 检查项目文件
Write-Host "[3/6] 检查项目文件..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd ~/telegram-ai-system
echo '=== 检查关键文件 ==='
[ -f admin-backend/app/main.py ] && echo '✓ admin-backend/app/main.py 存在' || echo '✗ admin-backend/app/main.py 不存在'
[ -f main.py ] && echo '✓ main.py 存在' || echo '✗ main.py 不存在'
[ -d admin-backend ] && echo '✓ admin-backend 目录存在' || echo '✗ admin-backend 目录不存在'
echo ''
echo '=== 项目结构 ==='
ls -la | head -10
"@
Write-Host $result.Output
Write-Host ""

# 修复步骤 4: 检查依赖
Write-Host "[4/6] 检查 Python 依赖..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd ~/telegram-ai-system
if [ -d admin-backend ]; then
    cd admin-backend
    if [ -f pyproject.toml ]; then
        echo '使用 Poetry 管理依赖'
        poetry --version 2>&1 || echo 'Poetry 未安装'
    elif [ -f requirements.txt ]; then
        echo '使用 requirements.txt'
        python3 -c 'import fastapi; print("FastAPI 已安装")' 2>&1 || echo 'FastAPI 未安装'
    fi
else
    echo 'admin-backend 目录不存在'
fi
"@
Write-Host $result.Output
Write-Host ""

# 修复步骤 5: 重新启动服务
Write-Host "[5/6] 重新启动服务..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd ~/telegram-ai-system

# 确定启动方式
if [ -f admin-backend/app/main.py ]; then
    echo '使用 admin-backend/app/main.py 启动'
    cd admin-backend
    
    # 检查是否有 .env 文件
    if [ ! -f .env ]; then
        echo '创建 .env 文件...'
        cat > .env << 'EOF'
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=`$(python3 -c "import secrets; print(secrets.token_hex(32))")
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
    fi
    
    # 启动服务
    nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
    PID=`$!
    echo `$PID > ../backend.pid
    sleep 3
    echo "服务已启动 (PID: `$PID)"
elif [ -f main.py ]; then
    echo '使用 main.py 启动'
    nohup python3 main.py > logs/backend.log 2>&1 &
    PID=`$!
    echo `$PID > backend.pid
    sleep 3
    echo "服务已启动 (PID: `$PID)"
else
    echo '✗ 找不到启动文件'
    exit 1
fi
"@
Write-Host $result.Output
if ($result.ExitStatus -eq 0) {
    Write-Host "✓ 服务启动命令已执行`n" -ForegroundColor Green
} else {
    Write-Host "✗ 服务启动失败`n" -ForegroundColor Red
}

# 修复步骤 6: 验证服务
Write-Host "[6/6] 验证服务状态..." -ForegroundColor Cyan
Start-Sleep -Seconds 5
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
echo '=== 进程检查 ==='
pgrep -f 'uvicorn' && echo '✓ uvicorn 进程运行中' || echo '✗ uvicorn 进程未运行'
echo ''
echo '=== 端口检查 ==='
if command -v netstat &> /dev/null; then
    netstat -tlnp 2>/dev/null | grep ':8000' && echo '✓ 端口 8000 正在监听' || echo '✗ 端口 8000 未监听'
elif command -v ss &> /dev/null; then
    ss -tlnp 2>/dev/null | grep ':8000' && echo '✓ 端口 8000 正在监听' || echo '✗ 端口 8000 未监听'
else
    echo '无法检查端口状态'
fi
echo ''
echo '=== 健康检查 ==='
curl -s http://localhost:8000/health 2>&1 | head -5 || echo '健康检查失败'
echo ''
echo '=== 最近日志 ==='
if [ -f ~/telegram-ai-system/logs/backend.log ]; then
    tail -10 ~/telegram-ai-system/logs/backend.log
else
    echo '日志文件不存在'
fi
"@
Write-Host $result.Output

# 断开连接
Remove-SSHSession -SessionId $session.SessionId | Out-Null

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "修复完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "服务地址: http://${ServerIP}:8000" -ForegroundColor Yellow
Write-Host "API 文档: http://${ServerIP}:8000/docs" -ForegroundColor Yellow
Write-Host "健康检查: http://${ServerIP}:8000/health`n" -ForegroundColor Yellow

