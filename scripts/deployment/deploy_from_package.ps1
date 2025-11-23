# 从已上传的 deployment-package 部署
# 使用方法: .\deploy_from_package.ps1 -ServerIP <ip> -Username <user> -Password <pass> -ServerName <name>

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
Write-Host "从 deployment-package 部署 - $ServerName ($ServerIP)" -ForegroundColor Cyan
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

# 步骤 1: 检查 deployment-package
Write-Host "[1/8] 检查 deployment-package..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
if [ -d "deployment-package" ]; then
    echo "目录存在"
    ls -la deployment-package | head -10
elif [ -f "deployment-package.zip" ]; then
    echo "ZIP文件存在，需要解压"
else
    echo "未找到 deployment-package"
fi
"@
Write-Host $result.Output
if ($result.Output -match "未找到") {
    Write-Host "✗ deployment-package 不存在" -ForegroundColor Red
    Remove-SSHSession -SessionId $session.SessionId | Out-Null
    exit 1
}
Write-Host ""

# 步骤 2: 解压 ZIP（如果存在）
if ($result.Output -match "ZIP文件存在") {
    Write-Host "[2/8] 解压 deployment-package.zip..." -ForegroundColor Cyan
    $result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
unzip -q -o deployment-package.zip -d .
echo "解压完成"
"@
    Write-Host $result.Output
    Write-Host ""
}

# 步骤 3: 移动文件到正确位置
Write-Host "[3/8] 整理文件结构..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
if [ -d "deployment-package" ]; then
    # 移动 deployment-package 内容到当前目录
    cp -r deployment-package/* .
    cp -r deployment-package/.* . 2>/dev/null || true
    echo "文件已复制"
    ls -la | head -15
else
    echo "deployment-package 目录不存在"
fi
"@
Write-Host $result.Output
Write-Host ""

# 步骤 4: 安装 Python 依赖
Write-Host "[4/8] 安装 Python 依赖..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
if [ -f "admin-backend/requirements.txt" ]; then
    cd admin-backend
    pip3 install -r requirements.txt --quiet --upgrade
    echo "依赖安装完成"
else
    echo "requirements.txt 不存在"
fi
"@
Write-Host $result.Output
if ($result.ExitStatus -ne 0) {
    Write-Host "⚠ 依赖安装可能有警告，继续..." -ForegroundColor Yellow
}
Write-Host ""

# 步骤 5: 创建 .env 文件
Write-Host "[5/8] 创建 .env 文件..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir/admin-backend
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
    echo ".env 文件已存在，跳过"
fi
"@
Write-Host $result.Output
Write-Host ""

# 步骤 6: 创建必要目录
Write-Host "[6/8] 创建必要目录..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir
mkdir -p sessions logs backups
chmod 700 sessions
chmod 755 logs backups
echo "目录创建完成"
ls -ld sessions logs backups
"@
Write-Host $result.Output
Write-Host ""

# 步骤 7: 停止旧服务并启动新服务
Write-Host "[7/8] 启动服务..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $DeployDir

# 停止旧服务
pkill -f 'uvicorn app.main:app' || true
pkill -f 'python.*main.py' || true
sleep 2

# 启动新服务
cd admin-backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
PID=`$!
echo `$PID > ../backend.pid
sleep 3

# 检查进程
if ps -p `$PID > /dev/null; then
    echo "服务已启动 (PID: `$PID)"
else
    echo "服务启动失败，查看日志:"
    tail -20 ../logs/backend.log
fi
"@
Write-Host $result.Output
Write-Host ""

# 步骤 8: 验证部署
Write-Host "[8/8] 验证部署..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
echo '=== 进程检查 ==='
pgrep -f 'uvicorn' && echo '✓ uvicorn 进程运行中' || echo '✗ uvicorn 进程未运行'

echo ''
echo '=== 端口检查 ==='
if command -v netstat &> /dev/null; then
    netstat -tlnp 2>/dev/null | grep ':8000' && echo '✓ 端口 8000 正在监听' || echo '✗ 端口 8000 未监听'
elif command -v ss &> /dev/null; then
    ss -tlnp 2>/dev/null | grep ':8000' && echo '✓ 端口 8000 正在监听' || echo '✗ 端口 8000 未监听'
fi

echo ''
echo '=== 健康检查 ==='
curl -s http://localhost:8000/health 2>&1 | head -5 || echo '健康检查失败'

echo ''
echo '=== 最近日志 ==='
tail -10 logs/backend.log 2>/dev/null || echo '日志文件不存在'
"@
Write-Host $result.Output

# 断开连接
Remove-SSHSession -SessionId $session.SessionId | Out-Null

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "部署完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "服务地址: http://${ServerIP}:8000" -ForegroundColor Yellow
Write-Host "API 文档: http://${ServerIP}:8000/docs" -ForegroundColor Yellow
Write-Host "健康检查: http://${ServerIP}:8000/health`n" -ForegroundColor Yellow

