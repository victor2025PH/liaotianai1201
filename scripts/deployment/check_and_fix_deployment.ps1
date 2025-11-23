# 检查并修复部署问题
# 使用方法: .\check_and_fix_deployment.ps1 -ServerIP <ip> -Username <user> -Password <pass>

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$Password,
    
    [Parameter(Mandatory=$false)]
    [string]$ServerName = "服务器",
    
    [Parameter(Mandatory=$false)]
    [string]$DeployDir = "~/telegram-ai-system"
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "检查并修复部署 - $ServerName ($ServerIP)" -ForegroundColor Cyan
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

# 检查文件结构
Write-Host "[1/6] 检查文件结构..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
echo '=== 当前目录内容 ==='
ls -la | head -20
echo ''
echo '=== 查找 main.py ==='
find . -name 'main.py' -type f 2>/dev/null | head -5
echo ''
echo '=== 查找 .env ==='
find . -name '.env' -type f 2>/dev/null | head -5
echo ''
echo '=== admin-backend 目录 ==='
ls -la admin-backend/ 2>/dev/null | head -10 || echo 'admin-backend 不存在'
"@
Write-Host $result.Output
Write-Host ""

# 检查服务状态和日志
Write-Host "[2/6] 检查服务状态..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
echo '=== 进程信息 ==='
ps aux | grep uvicorn | grep -v grep
echo ''
echo '=== 端口监听 ==='
if command -v netstat &> /dev/null; then
    netstat -tlnp 2>/dev/null | grep ':8000' || echo '端口 8000 未监听'
elif command -v ss &> /dev/null; then
    ss -tlnp 2>/dev/null | grep ':8000' || echo '端口 8000 未监听'
fi
echo ''
echo '=== 最近日志 ==='
if [ -f logs/backend.log ]; then
    tail -30 logs/backend.log
elif [ -f $DeployDir/logs/backend.log ]; then
    tail -30 $DeployDir/logs/backend.log
else
    echo '日志文件不存在'
fi
"@
Write-Host $result.Output
Write-Host ""

# 修复：确保文件在正确位置
Write-Host "[3/6] 修复文件结构..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir

# 如果 deployment-package 存在，移动内容
if [ -d "deployment-package" ]; then
    echo '移动 deployment-package 内容...'
    # 移动所有文件（排除 deployment-package 本身）
    find deployment-package -mindepth 1 -maxdepth 1 -exec mv {} . \;
    echo '文件已移动'
fi

# 确保 admin-backend 存在
if [ ! -d "admin-backend" ]; then
    echo 'admin-backend 目录不存在，查找...'
    find . -type d -name 'admin-backend' 2>/dev/null | head -1
fi

echo ''
echo '=== 修复后的结构 ==='
ls -la | head -15
"@
Write-Host $result.Output
Write-Host ""

# 修复：重新创建 .env
Write-Host "[4/6] 修复 .env 文件..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir

# 找到 admin-backend 目录
ADMIN_BACKEND_DIR=""
if [ -d "admin-backend" ]; then
    ADMIN_BACKEND_DIR="admin-backend"
elif [ -d "deployment-package/admin-backend" ]; then
    ADMIN_BACKEND_DIR="deployment-package/admin-backend"
else
    ADMIN_BACKEND_DIR=`$(find . -type d -name 'admin-backend' | head -1)
fi

if [ -n "`$ADMIN_BACKEND_DIR" ] && [ -d "`$ADMIN_BACKEND_DIR" ]; then
    cd `$ADMIN_BACKEND_DIR
    if [ ! -f ".env" ]; then
        JWT_SECRET=`$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "change_me_please_change_in_production")
        cat > .env << EOF
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=`$JWT_SECRET
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
        echo ".env 文件已创建在 `$ADMIN_BACKEND_DIR"
    else
        echo ".env 文件已存在"
    fi
    echo "admin-backend 路径: `$(pwd)"
else
    echo "✗ 找不到 admin-backend 目录"
fi
"@
Write-Host $result.Output
Write-Host ""

# 修复：重新启动服务
Write-Host "[5/6] 重新启动服务..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir

# 停止旧服务
pkill -f 'uvicorn app.main:app' || true
pkill -f 'python.*main.py' || true
sleep 2

# 找到 admin-backend
ADMIN_BACKEND_DIR=""
if [ -d "admin-backend" ]; then
    ADMIN_BACKEND_DIR="admin-backend"
else
    ADMIN_BACKEND_DIR=`$(find . -type d -name 'admin-backend' | head -1)
fi

if [ -n "`$ADMIN_BACKEND_DIR" ] && [ -d "`$ADMIN_BACKEND_DIR" ]; then
    cd `$ADMIN_BACKEND_DIR
    
    # 确保 .env 存在
    if [ ! -f ".env" ]; then
        JWT_SECRET=`$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "change_me")
        cat > .env << EOF
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=`$JWT_SECRET
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
    fi
    
    # 启动服务
    cd ..
    mkdir -p logs
    cd `$ADMIN_BACKEND_DIR
    nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
    PID=`$!
    echo `$PID > ../backend.pid
    sleep 5
    
    echo "服务已启动 (PID: `$PID)"
    echo "工作目录: `$(pwd)"
else
    echo "✗ 找不到 admin-backend 目录"
fi
"@
Write-Host $result.Output
Write-Host ""

# 验证修复
Write-Host "[6/6] 验证修复..." -ForegroundColor Cyan
Start-Sleep -Seconds 5
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
echo '=== 进程检查 ==='
pgrep -f 'uvicorn' && echo '✓ 进程运行中' || echo '✗ 进程未运行'

echo ''
echo '=== 端口检查 ==='
if command -v netstat &> /dev/null; then
    netstat -tlnp 2>/dev/null | grep ':8000' && echo '✓ 端口监听' || echo '✗ 端口未监听'
elif command -v ss &> /dev/null; then
    ss -tlnp 2>/dev/null | grep ':8000' && echo '✓ 端口监听' || echo '✗ 端口未监听'
fi

echo ''
echo '=== 健康检查 ==='
curl -s http://localhost:8000/health 2>&1 | head -3 || echo '健康检查失败'

echo ''
echo '=== 错误日志 ==='
if [ -f ../logs/backend.log ]; then
    tail -20 ../logs/backend.log | grep -i error || echo '无错误'
fi
"@
Write-Host $result.Output

# 断开连接
Remove-SSHSession -SessionId $session.SessionId | Out-Null

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "修复完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

