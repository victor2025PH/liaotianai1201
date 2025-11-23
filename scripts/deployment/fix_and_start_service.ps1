# 修复并启动服务
# 使用方法: .\fix_and_start_service.ps1 -ServerIP <ip> -Username <user> -Password <pass> -DeployDir <dir>

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
Write-Host "修复并启动服务 - $ServerIP" -ForegroundColor Cyan
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
Write-Host "[1/6] 停止旧服务..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
pkill -f 'uvicorn' || true
pkill -f 'python.*main.py' || true
sleep 2
echo '旧服务已停止'
"@
Write-Host $result.Output
Write-Host ""

# 步骤 2: 安装依赖
Write-Host "[2/6] 安装 Python 依赖..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir

# 找到 requirements.txt
REQ_FILE=""
if [ -f "admin-backend/requirements.txt" ]; then
    REQ_FILE="admin-backend/requirements.txt"
elif [ -f "requirements.txt" ]; then
    REQ_FILE="requirements.txt"
else
    REQ_FILE=`$(find . -name 'requirements.txt' -type f | head -1)
fi

if [ -n "`$REQ_FILE" ] && [ -f "`$REQ_FILE" ]; then
    echo "使用: `$REQ_FILE"
    echo "安装依赖..."
    pip3 install -r "`$REQ_FILE" --upgrade 2>&1 | tail -20
    echo ""
    echo "安装 uvicorn 和 fastapi..."
    pip3 install uvicorn fastapi --upgrade 2>&1 | tail -10
    echo "依赖安装完成"
else
    echo "✗ requirements.txt 不存在，直接安装 uvicorn 和 fastapi..."
    pip3 install uvicorn fastapi --upgrade 2>&1 | tail -10
fi
"@
Write-Host $result.Output
Write-Host ""

# 步骤 3: 创建必要目录
Write-Host "[3/6] 创建必要目录..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
mkdir -p logs sessions backups
chmod 700 sessions
chmod 755 logs backups
echo "目录创建完成"
"@
Write-Host $result.Output
Write-Host ""

# 步骤 4: 创建 .env 文件
Write-Host "[4/6] 创建 .env 文件..." -ForegroundColor Cyan
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
    
    if [ ! -f ".env" ]; then
        JWT_SECRET=`$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "change_me_please_change_in_production")
        cat > .env << EOF
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=`$JWT_SECRET
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
        echo ".env 文件已创建"
    else
        echo ".env 文件已存在"
    fi
else
    echo "✗ 找不到 admin-backend 目录"
fi
"@
Write-Host $result.Output
Write-Host ""

# 步骤 5: 启动服务
Write-Host "[5/6] 启动服务..." -ForegroundColor Cyan
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
echo "启动服务..."
echo "工作目录: `$(pwd)"
echo "Python: `$(which python3)"
echo "检查 uvicorn:"
python3 -c "import uvicorn; print('✓ uvicorn 已安装')" 2>&1 || echo "✗ uvicorn 未安装"

nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
echo `$! > ../backend.pid
sleep 5

echo "服务已启动"
"@
Write-Host $result.Output
Write-Host ""

# 步骤 6: 验证服务
Write-Host "[6/6] 验证服务..." -ForegroundColor Cyan
Start-Sleep -Seconds 5
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir

echo '=== 进程检查 ==='
PID=`$(cat backend.pid 2>/dev/null)
if [ -n "`$PID" ]; then
    ps -p `$PID && echo "✓ 进程运行中 (PID: `$PID)" || echo "✗ 进程已退出"
fi
pgrep -f 'uvicorn' && echo "✓ uvicorn 进程存在" || echo "✗ uvicorn 进程不存在"

echo ''
echo '=== 端口检查 ==='
if command -v ss &> /dev/null; then
    ss -tlnp 2>/dev/null | grep ':8000' && echo "✓ 端口 8000 监听中" || echo "✗ 端口 8000 未监听"
fi

echo ''
echo '=== 健康检查 ==='
curl -s http://localhost:8000/health 2>&1 | head -5 || echo "健康检查失败"

echo ''
echo '=== 启动日志（最后 30 行）==='
tail -30 logs/backend.log 2>/dev/null || echo "日志文件不存在"
"@
Write-Host $result.Output

# 外部访问测试
Write-Host "`n=== 外部访问测试 ===" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://${ServerIP}:8000/health" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✓ 外部访问成功 (HTTP $($response.StatusCode))" -ForegroundColor Green
        Write-Host "  响应: $($response.Content)" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠ 外部访问返回 HTTP $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ 外部访问失败: $_" -ForegroundColor Red
}

# 断开连接
Remove-SSHSession -SessionId $session.SessionId | Out-Null

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "服务地址: http://${ServerIP}:8000" -ForegroundColor Yellow
Write-Host "API 文档: http://${ServerIP}:8000/docs" -ForegroundColor Yellow
Write-Host "健康检查: http://${ServerIP}:8000/health`n" -ForegroundColor Yellow

