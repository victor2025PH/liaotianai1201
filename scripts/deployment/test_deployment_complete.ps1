# 完整测试部署
# 使用方法: .\test_deployment_complete.ps1 -ServerIP <ip> -Username <user> -Password <pass>

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$Password,
    
    [Parameter(Mandatory=$false)]
    [string]$ServerName = "服务器"
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "完整部署测试 - $ServerName ($ServerIP)" -ForegroundColor Cyan
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

$testResults = @()

# 测试 1: 服务进程
Write-Host "[测试 1] 检查服务进程..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command "pgrep -f 'uvicorn' && echo 'PASS' || echo 'FAIL'"
if ($result.Output -match "PASS") {
    Write-Host "  ✓ 服务进程运行中" -ForegroundColor Green
    $testResults += @{Test="服务进程"; Status="PASS"}
} else {
    Write-Host "  ✗ 服务进程未运行" -ForegroundColor Red
    $testResults += @{Test="服务进程"; Status="FAIL"}
}

# 测试 2: 端口监听
Write-Host "[测试 2] 检查端口监听..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
if command -v netstat &> /dev/null; then
    netstat -tlnp 2>/dev/null | grep ':8000' && echo 'PASS' || echo 'FAIL'
elif command -v ss &> /dev/null; then
    ss -tlnp 2>/dev/null | grep ':8000' && echo 'PASS' || echo 'FAIL'
else
    echo 'FAIL'
fi
"@
if ($result.Output -match "PASS") {
    Write-Host "  ✓ 端口 8000 正在监听" -ForegroundColor Green
    $testResults += @{Test="端口监听"; Status="PASS"}
} else {
    Write-Host "  ✗ 端口 8000 未监听" -ForegroundColor Red
    $testResults += @{Test="端口监听"; Status="FAIL"}
}

# 测试 3: 健康检查
Write-Host "[测试 3] 健康检查..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health"
if ($result.Output -match "200") {
    Write-Host "  ✓ 健康检查通过 (HTTP 200)" -ForegroundColor Green
    $testResults += @{Test="健康检查"; Status="PASS"}
} else {
    Write-Host "  ✗ 健康检查失败 (HTTP $($result.Output))" -ForegroundColor Red
    $testResults += @{Test="健康检查"; Status="FAIL"}
}

# 测试 4: API 文档
Write-Host "[测试 4] 检查 API 文档..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/docs"
if ($result.Output -match "200") {
    Write-Host "  ✓ API 文档可访问" -ForegroundColor Green
    $testResults += @{Test="API 文档"; Status="PASS"}
} else {
    Write-Host "  ✗ API 文档不可访问" -ForegroundColor Red
    $testResults += @{Test="API 文档"; Status="FAIL"}
}

# 测试 5: 关键文件
Write-Host "[测试 5] 检查关键文件..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd ~/telegram-ai-system
[ -f admin-backend/app/main.py ] && echo 'main.py: PASS' || echo 'main.py: FAIL'
[ -f admin-backend/.env ] && echo '.env: PASS' || echo '.env: FAIL'
[ -d sessions ] && echo 'sessions: PASS' || echo 'sessions: FAIL'
[ -d logs ] && echo 'logs: PASS' || echo 'logs: FAIL'
"@
$fileTests = $result.Output -split "`n"
foreach ($test in $fileTests) {
    if ($test -match "PASS") {
        Write-Host "  ✓ $test" -ForegroundColor Green
        $testResults += @{Test=$test; Status="PASS"}
    } else {
        Write-Host "  ✗ $test" -ForegroundColor Red
        $testResults += @{Test=$test; Status="FAIL"}
    }
}

# 测试 6: 外部访问
Write-Host "[测试 6] 测试外部访问..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://${ServerIP}:8000/health" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✓ 外部访问正常" -ForegroundColor Green
        $testResults += @{Test="外部访问"; Status="PASS"}
    } else {
        Write-Host "  ✗ 外部访问失败 (HTTP $($response.StatusCode))" -ForegroundColor Red
        $testResults += @{Test="外部访问"; Status="FAIL"}
    }
} catch {
    Write-Host "  ✗ 外部访问失败: $_" -ForegroundColor Red
    $testResults += @{Test="外部访问"; Status="FAIL"}
}

# 断开连接
Remove-SSHSession -SessionId $session.SessionId | Out-Null

# 显示测试结果摘要
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "测试结果摘要" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$passCount = ($testResults | Where-Object { $_.Status -eq "PASS" }).Count
$failCount = ($testResults | Where-Object { $_.Status -eq "FAIL" }).Count
$totalCount = $testResults.Count

Write-Host "总计: $totalCount 个测试" -ForegroundColor Cyan
Write-Host "通过: $passCount" -ForegroundColor Green
Write-Host "失败: $failCount" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($failCount -eq 0) {
    Write-Host "✓ 所有测试通过！部署成功！" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ 部分测试失败，请检查部署" -ForegroundColor Red
    exit 1
}

