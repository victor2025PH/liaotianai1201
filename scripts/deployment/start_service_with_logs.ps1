# 启动服务并查看日志
# 使用方法: .\start_service_with_logs.ps1 -ServerIP <ip> -Username <user> -Password <pass> -DeployDir <dir>

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$Password,
    
    [Parameter(Mandatory=$false)]
    [string]$DeployDir = "/home/ubuntu"
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "启动服务并查看日志 - $ServerIP" -ForegroundColor Cyan
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

# 步骤 1: 停止旧服务
Write-Host "[1/5] 停止旧服务..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
pkill -f 'uvicorn' || true
pkill -f 'python.*main.py' || true
sleep 2
echo '旧服务已停止'
"@
Write-Host $result.Output
Write-Host ""

# 步骤 2: 检查 Python 环境和依赖
Write-Host "[2/5] 检查 Python 环境..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
echo '=== Python 环境 ==='
which python3
python3 --version
echo ''
echo '=== 检查 uvicorn ==='
python3 -c 'import uvicorn; print(\"✓ uvicorn:\", uvicorn.__version__)' 2>&1 || echo '✗ uvicorn 未安装'
echo ''
echo '=== 检查 fastapi ==='
python3 -c 'import fastapi; print(\"✓ fastapi:\", fastapi.__version__)' 2>&1 || echo '✗ fastapi 未安装'
"@
Write-Host $result.Output
Write-Host ""

# 步骤 3: 如果缺少依赖，安装
Write-Host "[3/5] 安装依赖（如需要）..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
python3 -c 'import uvicorn' 2>&1 || {
    echo '安装 uvicorn 和 fastapi...'
    python3 -m pip install uvicorn fastapi --user --upgrade 2>&1 | tail -15
}
"@
Write-Host $result.Output
Write-Host ""

# 步骤 4: 检查配置文件
Write-Host "[4/5] 检查配置文件..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir

# 找到 admin-backend
ADMIN_BACKEND=""
if [ -d "admin-backend" ]; then
    ADMIN_BACKEND="admin-backend"
else
    ADMIN_BACKEND=`$(find . -type d -name 'admin-backend' | head -1)
fi

if [ -n "`$ADMIN_BACKEND" ] && [ -d "`$ADMIN_BACKEND" ]; then
    cd `$ADMIN_BACKEND
    echo "工作目录: `$(pwd)"
    echo ""
    echo "=== 检查文件 ==="
    [ -f "app/main.py" ] && echo "✓ app/main.py 存在" || echo "✗ app/main.py 不存在"
    [ -f ".env" ] && echo "✓ .env 存在" || echo "✗ .env 不存在"
    echo ""
    echo "=== .env 内容 ==="
    cat .env 2>/dev/null || echo ".env 不存在，将创建..."
    
    if [ ! -f ".env" ]; then
        JWT_SECRET=`$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "change_me")
        cat > .env << EOF
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=`$JWT_SECRET
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
        echo ".env 已创建"
    fi
else
    echo "✗ 找不到 admin-backend 目录"
fi
"@
Write-Host $result.Output
Write-Host ""

# 步骤 5: 启动服务并查看实时日志
Write-Host "[5/5] 启动服务并查看日志..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir

# 找到 admin-backend
ADMIN_BACKEND=""
if [ -d "admin-backend" ]; then
    ADMIN_BACKEND="admin-backend"
else
    ADMIN_BACKEND=`$(find . -type d -name 'admin-backend' | head -1)
fi

if [ -z "`$ADMIN_BACKEND" ] || [ ! -d "`$ADMIN_BACKEND" ]; then
    echo "✗ 找不到 admin-backend 目录"
    exit 1
fi

cd `$ADMIN_BACKEND

# 创建日志目录
mkdir -p ../logs

# 启动服务（前台运行一段时间查看错误）
echo "启动服务（测试模式，10秒后停止）..."
timeout 10 python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 || {
    echo ""
    echo "=== 启动失败，错误信息 ==="
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 | head -50
}
"@
Write-Host $result.Output
Write-Host ""

# 如果测试启动成功，后台启动
Write-Host "如果测试启动成功，现在后台启动服务..." -ForegroundColor Yellow
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir/admin-backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
echo `$! > ../backend.pid
sleep 5

echo "=== 进程检查 ==="
ps -p `$(cat ../backend.pid 2>/dev/null) && echo "✓ 进程运行中" || echo "✗ 进程已退出"

echo ""
echo "=== 端口检查 ==="
ss -tlnp 2>/dev/null | grep ':8000' && echo "✓ 端口 8000 监听中" || echo "✗ 端口 8000 未监听"

echo ""
echo "=== 启动日志（最后 30 行）==="
tail -30 ../logs/backend.log 2>/dev/null || echo "日志文件不存在"
"@
Write-Host $result.Output

# 断开连接
Remove-SSHSession -SessionId $session.SessionId | Out-Null

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

