# 检查部署状态脚本
# 使用方法: .\check_deployment.ps1 [-ServerIP <ip>] [-Username <user>] [-Password <pass>]

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "165.154.255.48",
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$Password = "8iDcGrYb52Fxpzee"
)

$ErrorActionPreference = "Continue"

# 检查 Posh-SSH 模块
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Write-Host "安装 Posh-SSH 模块..." -ForegroundColor Yellow
    Install-Module -Name Posh-SSH -Force -Scope CurrentUser
}

Import-Module Posh-SSH

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "检查部署状态" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "服务器: $ServerIP`n" -ForegroundColor Cyan

# 建立 SSH 连接
Write-Host "正在连接..." -ForegroundColor Gray
Write-Host "  服务器: $ServerIP" -ForegroundColor Gray
Write-Host "  用户名: $Username" -ForegroundColor Gray
Write-Host "  密码长度: $($Password.Length) 字符" -ForegroundColor Gray

try {
    # 确保密码字符串正确（去除可能的隐藏字符）
    $cleanPassword = $Password.Trim()
    
    $securePassword = ConvertTo-SecureString $cleanPassword -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential($Username, $securePassword)
    
    Write-Host "  正在建立 SSH 连接..." -ForegroundColor Gray
    $session = New-SSHSession -ComputerName $ServerIP -Credential $credential -AcceptKey -ConnectionTimeout 30
    
    if (-not $session) {
        Write-Host "✗ SSH 连接失败" -ForegroundColor Red
        Write-Host "  可能原因:" -ForegroundColor Yellow
        Write-Host "    • 密码不正确" -ForegroundColor Yellow
        Write-Host "    • 服务器禁用了密码认证" -ForegroundColor Yellow
        Write-Host "    • 网络连接问题" -ForegroundColor Yellow
        Write-Host "  建议: 运行 .\scripts\deployment\test_ssh_connection.ps1 进行详细测试" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "✓ SSH 连接成功 (Session ID: $($session.SessionId))`n" -ForegroundColor Green
} catch {
    Write-Host "✗ 连接错误: $_" -ForegroundColor Red
    Write-Host "  错误类型: $($_.Exception.GetType().Name)" -ForegroundColor Red
    Write-Host "  错误消息: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`n  可能原因:" -ForegroundColor Yellow
    Write-Host "    • 密码不正确或已被更改" -ForegroundColor Yellow
    Write-Host "    • 服务器 SSH 配置问题" -ForegroundColor Yellow
    Write-Host "    • 网络连接超时" -ForegroundColor Yellow
    Write-Host "`n  建议操作:" -ForegroundColor Yellow
    Write-Host "    1. 手动测试: ssh ${Username}@${ServerIP}" -ForegroundColor White
    Write-Host "    2. 运行测试脚本: .\scripts\deployment\test_ssh_connection.ps1 -ServerIP $ServerIP" -ForegroundColor White
    Write-Host "    3. 确认密码是否正确" -ForegroundColor White
    exit 1
}

# 检查部署目录
Write-Host "[1/8] 检查部署目录..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command "test -d ~/telegram-ai-system && echo '存在' || echo '不存在'"
if ($result.Output -match "存在") {
    Write-Host "✓ 部署目录存在" -ForegroundColor Green
} else {
    Write-Host "✗ 部署目录不存在" -ForegroundColor Red
}

# 检查 main.py 文件
Write-Host "[2/8] 检查 main.py 文件..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
if [ -f ~/telegram-ai-system/admin-backend/app/main.py ]; then
    echo "存在"
    ls -lh ~/telegram-ai-system/admin-backend/app/main.py
elif [ -f ~/telegram-ai-system/app/main.py ]; then
    echo "存在（备用路径）"
    ls -lh ~/telegram-ai-system/app/main.py
else
    echo "不存在"
    find ~/telegram-ai-system -name "main.py" -type f 2>/dev/null | head -5
fi
"@
if ($result.Output -match "存在") {
    Write-Host "✓ main.py 文件存在" -ForegroundColor Green
    $result.Output | Select-String "main.py" | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
} else {
    Write-Host "✗ main.py 文件不存在" -ForegroundColor Red
    if ($result.Output -match "\.py$") {
        Write-Host "  找到的文件:" -ForegroundColor Yellow
        $result.Output | Select-String "\.py$" | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    }
}

# 检查服务运行状态
Write-Host "[3/8] 检查服务运行状态..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command "pgrep -f 'uvicorn app.main:app' && echo '运行中' || echo '未运行'"
if ($result.Output -match "运行中") {
    $pidMatch = ($result.Output | Select-String "\d+")
    if ($pidMatch) {
        $processId = $pidMatch.Matches[0].Value
        Write-Host "✓ 后端服务运行中 (PID: $processId)" -ForegroundColor Green
    } else {
        Write-Host "✓ 后端服务运行中" -ForegroundColor Green
    }
} else {
    Write-Host "✗ 后端服务未运行" -ForegroundColor Red
}

# 检查端口监听
Write-Host "[4/8] 检查端口监听..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command "netstat -tuln | grep ':8000' || ss -tuln | grep ':8000' || echo '未监听'"
if ($result.Output -match ":8000") {
    Write-Host "✓ 端口 8000 正在监听" -ForegroundColor Green
    $result.Output | Select-String ":8000" | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
} else {
    Write-Host "✗ 端口 8000 未监听" -ForegroundColor Red
}

# 检查健康状态
Write-Host "[5/8] 检查服务健康状态..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command "curl -s http://localhost:8000/health 2>/dev/null || echo '不可访问'"
if ($result.Output -match "healthy|status") {
    Write-Host "✓ 服务健康检查通过" -ForegroundColor Green
    $result.Output | ConvertFrom-Json | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Gray
} else {
    Write-Host "✗ 服务健康检查失败" -ForegroundColor Red
    Write-Host "  输出: $($result.Output)" -ForegroundColor Gray
}

# 检查关键文件
Write-Host "[6/8] 检查关键文件..." -ForegroundColor Cyan
$files = @(
    "~/telegram-ai-system/admin-backend/app/main.py",
    "~/telegram-ai-system/admin-backend/app/core/cache.py",
    "~/telegram-ai-system/admin-backend/app/core/auto_backup.py",
    "~/telegram-ai-system/admin-backend/app/core/performance_monitor.py",
    "~/telegram-ai-system/admin-backend/app/api/system/optimization.py"
)

foreach ($file in $files) {
    $result = Invoke-SSHCommand -SessionId $session.SessionId -Command "test -f $file && echo '存在' || echo '不存在'"
    $fileName = Split-Path $file -Leaf
    if ($result.Output -match "存在") {
        Write-Host "  ✓ $fileName" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $fileName" -ForegroundColor Red
    }
}

# 检查 Session 目录
Write-Host "[7/8] 检查 Session 目录..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
if [ -d ~/telegram-ai-system/sessions ]; then
    echo "存在"
    ls -lh ~/telegram-ai-system/sessions/*.session 2>/dev/null | wc -l
    echo "---"
    ls -lh ~/telegram-ai-system/sessions/*.enc 2>/dev/null | wc -l
else
    echo "不存在"
fi
"@
if ($result.Output -match "存在") {
    $sessionCount = ($result.Output | Select-String "^\d+$" | Select-Object -First 1).Line
    Write-Host "✓ Session 目录存在" -ForegroundColor Green
    Write-Host "  Session 文件数量: $sessionCount" -ForegroundColor Gray
} else {
    Write-Host "✗ Session 目录不存在" -ForegroundColor Red
}

# 检查日志文件
Write-Host "[8/8] 检查日志文件..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
if [ -f ~/telegram-ai-system/logs/backend.log ]; then
    echo "存在"
    tail -5 ~/telegram-ai-system/logs/backend.log
else
    echo "不存在"
fi
"@
if ($result.Output -match "存在") {
    Write-Host "✓ 日志文件存在" -ForegroundColor Green
    Write-Host "  最近日志:" -ForegroundColor Gray
    $result.Output | Select-Object -Skip 1 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
} else {
    Write-Host "✗ 日志文件不存在" -ForegroundColor Red
}

# 断开连接
Remove-SSHSession -SessionId $session.SessionId | Out-Null

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "检查完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

