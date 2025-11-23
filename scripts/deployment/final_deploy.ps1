# 最终完整部署脚本
# 使用方法: .\final_deploy.ps1 -ServerIP <ip> -Username <user> -Password <pass> -ServerName <name>

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
Write-Host "最终完整部署 - $ServerName ($ServerIP)" -ForegroundColor Cyan
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

# 步骤 1: 全面查找文件
Write-Host "[1/10] 全面查找 deployment-package..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
echo '=== 查找 deployment-package ==='
find ~ -type d -name 'deployment-package' 2>/dev/null | head -5
echo ''
echo '=== 查找 admin-backend ==='
find ~ -type d -name 'admin-backend' 2>/dev/null | head -5
echo ''
echo '=== 检查部署目录 ==='
cd $DeployDir
pwd
ls -la
"@
Write-Host $result.Output
Write-Host ""

# 步骤 2: 如果找到 deployment-package，移动文件
Write-Host "[2/10] 移动文件到正确位置..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir

# 查找 deployment-package
DEPLOY_PKG=`$(find ~ -type d -name 'deployment-package' 2>/dev/null | head -1)

if [ -n "`$DEPLOY_PKG" ] && [ -d "`$DEPLOY_PKG" ]; then
    echo "找到 deployment-package: `$DEPLOY_PKG"
    echo "移动文件..."
    
    # 移动到当前目录
    cd `$DEPLOY_PKG
    for item in * .*; do
        if [ -e "`$item" ] && [ "`$(basename `$item)" != "." ] && [ "`$(basename `$item)" != ".." ] && [ "`$(basename `$item)" != "deployment-package" ]; then
            cp -r "`$item" $DeployDir/ 2>/dev/null || true
        fi
    done
    
    cd $DeployDir
    echo "文件已复制"
    ls -la | head -20
else
    echo "未找到 deployment-package，检查是否已在正确位置"
    ls -la | head -20
fi
"@
Write-Host $result.Output
Write-Host ""

# 步骤 3: 验证文件结构
Write-Host "[3/10] 验证文件结构..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
echo '=== 关键目录 ==='
[ -d "admin-backend" ] && echo "✓ admin-backend" || echo "✗ admin-backend"
[ -d "group_ai_service" ] && echo "✓ group_ai_service" || echo "✗ group_ai_service"
[ -d "utils" ] && echo "✓ utils" || echo "✗ utils"
echo ''
echo '=== 关键文件 ==='
[ -f "admin-backend/app/main.py" ] && echo "✓ admin-backend/app/main.py" || echo "✗ admin-backend/app/main.py"
[ -f "requirements.txt" ] && echo "✓ requirements.txt" || ( [ -f "admin-backend/requirements.txt" ] && echo "✓ admin-backend/requirements.txt" || echo "✗ requirements.txt" )
"@
Write-Host $result.Output
Write-Host ""

# 步骤 4: 停止所有旧服务
Write-Host "[4/10] 停止旧服务..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
pkill -f 'uvicorn' || true
pkill -f 'python.*main.py' || true
pkill -f 'python.*uvicorn' || true
sleep 2
echo '旧服务已停止'
"@
Write-Host $result.Output
Write-Host ""

# 步骤 5: 安装 Python 依赖
Write-Host "[5/10] 安装 Python 依赖..." -ForegroundColor Cyan
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
    pip3 install -r "`$REQ_FILE" --quiet --upgrade 2>&1 | tail -15
    echo "依赖安装完成"
else
    echo "✗ requirements.txt 不存在"
fi
"@
Write-Host $result.Output
Write-Host ""

# 步骤 6: 创建必要目录
Write-Host "[6/10] 创建必要目录..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
mkdir -p sessions logs backups
chmod 700 sessions
chmod 755 logs backups
echo "目录创建完成"
"@
Write-Host $result.Output
Write-Host ""

# 步骤 7: 创建 .env 文件
Write-Host "[7/10] 创建 .env 文件..." -ForegroundColor Cyan
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

# 步骤 8: 启动服务
Write-Host "[8/10] 启动服务..." -ForegroundColor Cyan
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
python3 -c "import uvicorn; print('uvicorn 已安装')" 2>&1 || echo "uvicorn 未安装，正在安装..."
python3 -m pip install uvicorn fastapi --quiet 2>&1 | tail -5

nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
PID=`$!
echo `$PID > ../backend.pid
sleep 5

echo "服务已启动 (PID: `$PID)"
"@
Write-Host $result.Output
Write-Host ""

# 步骤 9: 验证服务
Write-Host "[9/10] 验证服务..." -ForegroundColor Cyan
Start-Sleep -Seconds 5
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
echo '=== 进程检查 ==='
ps -p `$(cat ../backend.pid 2>/dev/null) && echo "✓ 进程运行中" || echo "✗ 进程已退出"
pgrep -f 'uvicorn' && echo "✓ uvicorn 进程存在" || echo "✗ uvicorn 进程不存在"

echo ''
echo '=== 端口检查 ==='
if command -v ss &> /dev/null; then
    ss -tlnp 2>/dev/null | grep ':8000' && echo "✓ 端口 8000 监听中" || echo "✗ 端口 8000 未监听"
fi

echo ''
echo '=== 健康检查 ==='
curl -s http://localhost:8000/health 2>&1 | head -3 || echo "健康检查失败"

echo ''
echo '=== 启动日志（最后 30 行）==='
tail -30 ../logs/backend.log 2>/dev/null || echo "日志文件不存在"
"@
Write-Host $result.Output
Write-Host ""

# 步骤 10: 外部访问测试
Write-Host "[10/10] 外部访问测试..." -ForegroundColor Cyan
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
Write-Host "部署完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "服务地址: http://${ServerIP}:8000" -ForegroundColor Yellow
Write-Host "API 文档: http://${ServerIP}:8000/docs" -ForegroundColor Yellow
Write-Host "健康检查: http://${ServerIP}:8000/health`n" -ForegroundColor Yellow

