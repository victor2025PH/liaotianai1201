# 诊断部署失败原因
# 使用方法: .\diagnose_failure.ps1 -ServerIP <ip> -Username <user> -Password <pass>

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
Write-Host "诊断部署失败原因 - $ServerName ($ServerIP)" -ForegroundColor Cyan
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

# 诊断 1: 检查目录结构
Write-Host "[诊断 1] 检查目录结构..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
echo '=== 当前目录 ==='
pwd
echo ''
echo '=== 目录内容 ==='
ls -la
echo ''
echo '=== deployment-package 是否存在 ==='
[ -d "deployment-package" ] && echo "存在" || echo "不存在"
[ -f "deployment-package.zip" ] && echo "ZIP文件存在" || echo "ZIP文件不存在"
echo ''
echo '=== 查找 admin-backend ==='
find . -type d -name 'admin-backend' 2>/dev/null | head -5
echo ''
echo '=== 查找 main.py ==='
find . -name 'main.py' -type f 2>/dev/null | head -5
"@
Write-Host $result.Output
Write-Host ""

# 诊断 2: 检查进程和端口
Write-Host "[诊断 2] 检查进程和端口..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
echo '=== 所有 uvicorn 进程 ==='
ps aux | grep uvicorn | grep -v grep
echo ''
echo '=== 所有 python 进程 ==='
ps aux | grep python | grep -v grep | head -10
echo ''
echo '=== 端口 8000 监听情况 ==='
if command -v netstat &> /dev/null; then
    netstat -tlnp 2>/dev/null | grep ':8000' || echo '端口 8000 未监听'
    netstat -tlnp 2>/dev/null | grep LISTEN | head -10
elif command -v ss &> /dev/null; then
    ss -tlnp 2>/dev/null | grep ':8000' || echo '端口 8000 未监听'
    ss -tlnp 2>/dev/null | grep LISTEN | head -10
fi
echo ''
echo '=== 检查防火墙 ==='
if command -v ufw &> /dev/null; then
    ufw status | head -5
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --list-ports 2>/dev/null | head -5
else
    echo '未找到防火墙管理工具'
fi
"@
Write-Host $result.Output
Write-Host ""

# 诊断 3: 检查日志
Write-Host "[诊断 3] 检查日志..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
echo '=== 日志文件位置 ==='
find . -name '*.log' -type f 2>/dev/null | head -10
echo ''
echo '=== backend.log 内容（最后 50 行）==='
if [ -f "logs/backend.log" ]; then
    tail -50 logs/backend.log
elif [ -f "admin-backend/logs/backend.log" ]; then
    tail -50 admin-backend/logs/backend.log
else
    echo '日志文件不存在，查找所有日志...'
    find . -name 'backend.log' -o -name '*.log' 2>/dev/null | head -5
    if [ -f "logs/backend.log" ] || [ -f "admin-backend/logs/backend.log" ]; then
        tail -50 logs/backend.log 2>/dev/null || tail -50 admin-backend/logs/backend.log 2>/dev/null
    fi
fi
"@
Write-Host $result.Output
Write-Host ""

# 诊断 4: 检查 Python 环境和依赖
Write-Host "[诊断 4] 检查 Python 环境..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
echo '=== Python 版本 ==='
python3 --version
which python3
echo ''
echo '=== 检查关键模块 ==='
python3 -c "import fastapi; print('FastAPI:', fastapi.__version__)" 2>&1
python3 -c "import uvicorn; print('Uvicorn:', uvicorn.__version__)" 2>&1
python3 -c "import sqlalchemy; print('SQLAlchemy:', sqlalchemy.__version__)" 2>&1
echo ''
echo '=== 查找 requirements.txt ==='
find . -name 'requirements.txt' -type f 2>/dev/null | head -5
"@
Write-Host $result.Output
Write-Host ""

# 诊断 5: 检查 .env 和配置
Write-Host "[诊断 5] 检查配置文件..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
echo '=== 查找 .env 文件 ==='
find . -name '.env' -type f 2>/dev/null | head -5
echo ''
echo '=== 检查 admin-backend/.env ==='
if [ -f "admin-backend/.env" ]; then
    echo "文件存在"
    cat admin-backend/.env
elif [ -f "deployment-package/admin-backend/.env" ]; then
    echo "在 deployment-package 中"
    cat deployment-package/admin-backend/.env
else
    echo "文件不存在"
fi
echo ''
echo '=== 检查 app/main.py ==='
if [ -f "admin-backend/app/main.py" ]; then
    echo "文件存在: admin-backend/app/main.py"
    head -20 admin-backend/app/main.py
elif [ -f "deployment-package/admin-backend/app/main.py" ]; then
    echo "文件存在: deployment-package/admin-backend/app/main.py"
    head -20 deployment-package/admin-backend/app/main.py
else
    echo "文件不存在，查找..."
    find . -path '*/app/main.py' 2>/dev/null | head -5
fi
"@
Write-Host $result.Output
Write-Host ""

# 诊断 6: 尝试手动启动服务
Write-Host "[诊断 6] 尝试手动启动服务..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir

# 找到 admin-backend
ADMIN_BACKEND=""
if [ -d "admin-backend" ]; then
    ADMIN_BACKEND="admin-backend"
elif [ -d "deployment-package/admin-backend" ]; then
    ADMIN_BACKEND="deployment-package/admin-backend"
else
    ADMIN_BACKEND=`$(find . -type d -name 'admin-backend' | head -1)
fi

if [ -z "`$ADMIN_BACKEND" ] || [ ! -d "`$ADMIN_BACKEND" ]; then
    echo "✗ 找不到 admin-backend 目录"
    exit 1
fi

echo "找到 admin-backend: `$ADMIN_BACKEND"
cd `$ADMIN_BACKEND

# 检查文件
echo ''
echo '=== 检查关键文件 ==='
[ -f "app/main.py" ] && echo "✓ app/main.py 存在" || echo "✗ app/main.py 不存在"
[ -f ".env" ] && echo "✓ .env 存在" || echo "✗ .env 不存在"
[ -f "requirements.txt" ] && echo "✓ requirements.txt 存在" || echo "✗ requirements.txt 不存在"

# 尝试启动（前台运行，查看错误）
echo ''
echo '=== 尝试启动服务（测试）==='
timeout 5 python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 || echo "启动失败或超时"
"@
Write-Host $result.Output
Write-Host ""

# 诊断 7: 检查错误信息
Write-Host "[诊断 7] 收集错误信息..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
echo '=== 系统错误日志 ==='
dmesg | tail -20 2>/dev/null || echo '无法访问系统日志'
echo ''
echo '=== 检查服务启动脚本 ==='
find . -name '*.sh' -o -name '*.py' | grep -E '(start|run|main)' | head -10
echo ''
echo '=== 检查 PID 文件 ==='
find . -name '*.pid' -type f 2>/dev/null
if [ -f "backend.pid" ]; then
    PID=`$(cat backend.pid 2>/dev/null)
    if [ -n "`$PID" ]; then
        echo "PID 文件内容: `$PID"
        ps -p `$PID && echo "进程存在" || echo "进程不存在"
    fi
fi
"@
Write-Host $result.Output

# 断开连接
Remove-SSHSession -SessionId $session.SessionId | Out-Null

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "诊断完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

