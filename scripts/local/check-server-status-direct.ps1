# ============================================================
# Check Server Status Directly (Local Environment - Windows)
# ============================================================
# 
# Running Environment: Local Windows Environment
# Function: Connect to server and check service status directly
# 
# One-click execution: .\scripts\local\check-server-status-direct.ps1
# ============================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "165.154.233.55",
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$Password = ""
)

$ErrorActionPreference = "Continue"

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🔍 直接检查服务器服务状态" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Server: $ServerIP" -ForegroundColor Cyan
Write-Host "User: $Username`n" -ForegroundColor Cyan

# Check Posh-SSH module
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Write-Host "正在安装 Posh-SSH 模块..." -ForegroundColor Yellow
    Install-Module -Name Posh-SSH -Force -Scope CurrentUser -SkipPublisherCheck
}

Import-Module Posh-SSH -ErrorAction Stop

# Connect to server
Write-Host "[1/2] 连接到服务器..." -ForegroundColor Yellow
try {
    if (-not $Password) {
        $Password = Read-Host "请输入服务器密码" -AsSecureString
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($Password)
        $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    }
    
    $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential($Username, $securePassword)
    
    $session = New-SSHSession -ComputerName $ServerIP -Credential $credential -AcceptKey -ErrorAction Stop
    if ($session) {
        Write-Host "✓ 已连接到服务器" -ForegroundColor Green
    } else {
        Write-Host "✗ 连接失败" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ 连接错误: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Execute comprehensive service check
Write-Host "[2/2] 检查服务状态..." -ForegroundColor Yellow
Write-Host ""

$checkCommand = @"
cd /home/ubuntu/telegram-ai-system

echo "============================================================"
echo "🔍 服务器服务状态检查"
echo "============================================================"
echo ""

# 1. Backend Service Status
echo "[1/6] 检查后端服务状态..."
echo "----------------------------------------"
if systemctl list-units --type=service | grep -q "telegram-backend"; then
    if systemctl is-active --quiet telegram-backend; then
        echo "✅ 后端服务正在运行"
        systemctl status telegram-backend --no-pager -l | head -n 8
    else
        echo "❌ 后端服务未运行"
        systemctl status telegram-backend --no-pager -l | head -n 8 || true
    fi
else
    echo "⚠️  后端服务未配置 (systemd)"
    if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
        echo "✅ 发现 uvicorn 进程在运行"
        ps aux | grep -E "uvicorn.*app.main:app" | grep -v grep | head -n 2
    else
        echo "❌ 未发现 uvicorn 进程"
    fi
fi
echo ""

# 2. Backend Port Status
echo "[2/6] 检查后端端口 (8000)..."
echo "----------------------------------------"
if ss -tlnp 2>/dev/null | grep -q ":8000"; then
    echo "✅ 端口 8000 正在监听"
    ss -tlnp 2>/dev/null | grep ":8000"
else
    echo "❌ 端口 8000 未监听"
fi
echo ""

# 3. Backend Health Check
echo "[3/6] 检查后端健康状态..."
echo "----------------------------------------"
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端健康检查通过"
    echo "健康检查响应:"
    curl -s http://localhost:8000/health | head -n 5
else
    echo "❌ 后端健康检查失败"
fi
echo ""

# 4. Frontend Service Status
echo "[4/6] 检查前端服务状态..."
echo "----------------------------------------"
FRONTEND_FOUND=false
for service_name in "liaotian-frontend" "smart-tg-frontend" "saas-demo"; do
    if systemctl list-units --type=service | grep -q "\$service_name"; then
        FRONTEND_FOUND=true
        if systemctl is-active --quiet "\$service_name"; then
            echo "✅ 前端服务正在运行 (\$service_name)"
            systemctl status "\$service_name" --no-pager -l | head -n 8
            break
        else
            echo "⚠️  前端服务已配置但未运行 (\$service_name)"
            systemctl status "\$service_name" --no-pager -l | head -n 5 || true
        fi
    fi
done

if [ "\$FRONTEND_FOUND" = false ]; then
    echo "⚠️  前端服务未配置 (systemd)"
    if pgrep -f "node.*next" > /dev/null || pgrep -f "npm.*start" > /dev/null; then
        echo "✅ 发现 Node.js 进程在运行"
        ps aux | grep -E "node.*next|npm.*start" | grep -v grep | head -n 2
    else
        echo "⚠️  未发现 Node.js 进程"
    fi
fi
echo ""

# 5. Frontend Port Status
echo "[5/6] 检查前端端口 (3000, 3001)..."
echo "----------------------------------------"
FRONTEND_PORT_FOUND=false
for port in 3000 3001 3002; do
    if ss -tlnp 2>/dev/null | grep -q ":\$port"; then
        echo "✅ 端口 \$port 正在监听"
        ss -tlnp 2>/dev/null | grep ":\$port"
        FRONTEND_PORT_FOUND=true
    fi
done

if [ "\$FRONTEND_PORT_FOUND" = false ]; then
    echo "❌ 前端端口 (3000, 3001, 3002) 均未监听"
fi
echo ""

# 6. Frontend Health Check
echo "[6/6] 检查前端健康状态..."
echo "----------------------------------------"
FRONTEND_HTTP_OK=false
for port in 3000 3001 3002; do
    HTTP_CODE=\$(curl -s -o /dev/null -w "%{http_code}" http://localhost:\$port 2>/dev/null || echo "000")
    if [ "\$HTTP_CODE" = "200" ] || [ "\$HTTP_CODE" = "301" ] || [ "\$HTTP_CODE" = "302" ]; then
        echo "✅ 前端服务在端口 \$port 响应正常 (HTTP \$HTTP_CODE)"
        echo "访问地址: http://localhost:\$port"
        FRONTEND_HTTP_OK=true
        break
    fi
done

if [ "\$FRONTEND_HTTP_OK" = false ]; then
    echo "❌ 前端服务未响应"
fi
echo ""

# Summary
echo "============================================================"
echo "📊 服务状态总结"
echo "============================================================"
echo ""

BACKEND_OK=false
FRONTEND_OK=false

# Check backend
if systemctl is-active --quiet telegram-backend 2>/dev/null || pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 后端服务: 运行正常"
        BACKEND_OK=true
    else
        echo "⚠️  后端服务: 进程运行但健康检查失败"
    fi
else
    echo "❌ 后端服务: 未运行"
fi

# Check frontend
if systemctl is-active --quiet liaotian-frontend 2>/dev/null || systemctl is-active --quiet smart-tg-frontend 2>/dev/null; then
    FRONTEND_OK=true
elif pgrep -f "node.*next" > /dev/null || pgrep -f "npm.*start" > /dev/null; then
    FRONTEND_OK=true
fi

if [ "\$FRONTEND_OK" = true ]; then
    HTTP_CODE=\$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
    if [ "\$HTTP_CODE" = "200" ] || [ "\$HTTP_CODE" = "301" ] || [ "\$HTTP_CODE" = "302" ]; then
        echo "✅ 前端服务: 运行正常 (端口 3000)"
    else
        echo "⚠️  前端服务: 进程运行但 HTTP 响应异常"
    fi
else
    echo "❌ 前端服务: 未运行"
fi

echo ""
echo "============================================================"
"@

$checkResult = Invoke-SSHCommand -SessionId $session.SessionId -Command $checkCommand

# Display output
if ($checkResult.Output) {
    Write-Host $checkResult.Output
}

if ($checkResult.Error) {
    Write-Host $checkResult.Error -ForegroundColor Red
}

Write-Host ""

# Close session
Remove-SSHSession -SessionId $session.SessionId | Out-Null

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ 检查完成" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

