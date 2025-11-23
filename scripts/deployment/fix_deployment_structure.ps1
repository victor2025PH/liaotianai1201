# 修复部署文件结构
# 使用方法: .\fix_deployment_structure.ps1 -ServerIP <ip> -Username <user> -Password <pass>

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
Write-Host "修复部署文件结构 - $ServerName ($ServerIP)" -ForegroundColor Cyan
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

# 步骤 1: 检查当前状态
Write-Host "[1/7] 检查当前状态..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
echo '=== 当前目录 ==='
pwd
echo ''
echo '=== 目录内容 ==='
ls -la
echo ''
echo '=== deployment-package 内容 ==='
if [ -d "deployment-package" ]; then
    ls -la deployment-package | head -15
fi
"@
Write-Host $result.Output
Write-Host ""

# 步骤 2: 停止所有旧服务
Write-Host "[2/7] 停止旧服务..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
pkill -f 'uvicorn' || true
pkill -f 'python.*main.py' || true
pkill -f 'python.*uvicorn' || true
sleep 2
echo '旧服务已停止'
"@
Write-Host $result.Output
Write-Host ""

# 步骤 3: 移动 deployment-package 内容
Write-Host "[3/7] 移动 deployment-package 内容..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir

if [ -d "deployment-package" ]; then
    echo '移动 deployment-package 内容到当前目录...'
    
    # 移动所有文件和目录（排除 deployment-package 本身）
    for item in deployment-package/* deployment-package/.*; do
        if [ -e "`$item" ] && [ "`$(basename `$item)" != "." ] && [ "`$(basename `$item)" != ".." ]; then
            mv "`$item" . 2>/dev/null || true
        fi
    done
    
    echo '文件移动完成'
    echo ''
    echo '=== 移动后的结构 ==='
    ls -la | head -20
else
    echo 'deployment-package 目录不存在，检查其他位置...'
    find . -type d -name 'deployment-package' 2>/dev/null | head -3
fi
"@
Write-Host $result.Output
Write-Host ""

# 步骤 4: 验证文件结构
Write-Host "[4/7] 验证文件结构..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
echo '=== 检查关键目录和文件 ==='
[ -d "admin-backend" ] && echo "✓ admin-backend 目录存在" || echo "✗ admin-backend 目录不存在"
[ -d "group_ai_service" ] && echo "✓ group_ai_service 目录存在" || echo "✗ group_ai_service 目录不存在"
[ -d "utils" ] && echo "✓ utils 目录存在" || echo "✗ utils 目录不存在"
[ -f "admin-backend/app/main.py" ] && echo "✓ admin-backend/app/main.py 存在" || echo "✗ admin-backend/app/main.py 不存在"
[ -f "requirements.txt" ] && echo "✓ requirements.txt 存在" || echo "✗ requirements.txt 不存在"
"@
Write-Host $result.Output
Write-Host ""

# 步骤 5: 安装依赖
Write-Host "[5/7] 安装 Python 依赖..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir

if [ -f "admin-backend/requirements.txt" ]; then
    cd admin-backend
    echo '安装依赖...'
    pip3 install -r requirements.txt --quiet --upgrade 2>&1 | tail -10
    echo '依赖安装完成'
elif [ -f "requirements.txt" ]; then
    echo '安装依赖...'
    pip3 install -r requirements.txt --quiet --upgrade 2>&1 | tail -10
    echo '依赖安装完成'
else
    echo '✗ requirements.txt 不存在'
fi
"@
Write-Host $result.Output
Write-Host ""

# 步骤 6: 创建 .env 文件
Write-Host "[6/7] 创建 .env 文件..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir

# 找到 admin-backend 目录
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
        cat .env
    else
        echo ".env 文件已存在"
    fi
else
    echo "✗ 找不到 admin-backend 目录"
fi
"@
Write-Host $result.Output
Write-Host ""

# 步骤 7: 启动服务
Write-Host "[7/7] 启动服务..." -ForegroundColor Cyan
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

# 创建日志目录
mkdir -p logs
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
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
PID=`$!
echo `$PID > ../backend.pid
sleep 5

echo "服务已启动 (PID: `$PID)"
echo ''
echo '=== 检查进程 ==='
ps -p `$PID && echo "进程运行中" || echo "进程已退出"
echo ''
echo '=== 检查端口 ==='
if command -v ss &> /dev/null; then
    ss -tlnp 2>/dev/null | grep ':8000' && echo "端口监听中" || echo "端口未监听"
fi
echo ''
echo '=== 启动日志（最后 20 行）==='
tail -20 ../logs/backend.log 2>/dev/null || echo "日志文件不存在"
"@
Write-Host $result.Output

# 断开连接
Remove-SSHSession -SessionId $session.SessionId | Out-Null

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "修复完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "服务地址: http://${ServerIP}:8000" -ForegroundColor Yellow
Write-Host "查看日志: ssh ${Username}@${ServerIP} 'tail -f $DeployDir/logs/backend.log'`n" -ForegroundColor Yellow

