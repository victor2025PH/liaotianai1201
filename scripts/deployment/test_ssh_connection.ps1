# 测试 SSH 连接脚本
# 使用方法: .\test_ssh_connection.ps1 -ServerIP <ip> -Username <user> -Password <pass>

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$Password = "8iDcGrYb52Fxpzee"
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "测试 SSH 连接" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "服务器: $ServerIP" -ForegroundColor Cyan
Write-Host "用户名: $Username" -ForegroundColor Cyan
Write-Host "密码长度: $($Password.Length) 字符`n" -ForegroundColor Cyan

# 检查 Posh-SSH 模块
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Write-Host "安装 Posh-SSH 模块..." -ForegroundColor Yellow
    Install-Module -Name Posh-SSH -Force -Scope CurrentUser
}

Import-Module Posh-SSH

# 方法 1: 使用 Posh-SSH
Write-Host "[方法 1] 使用 Posh-SSH 连接..." -ForegroundColor Cyan
try {
    $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential($Username, $securePassword)
    
    Write-Host "  正在连接..." -ForegroundColor Gray
    $session = New-SSHSession -ComputerName $ServerIP -Credential $credential -AcceptKey -ConnectionTimeout 30
    
    if ($session) {
        Write-Host "  ✓ 连接成功 (Session ID: $($session.SessionId))" -ForegroundColor Green
        
        # 测试命令
        $result = Invoke-SSHCommand -SessionId $session.SessionId -Command "echo '连接测试成功'; whoami; pwd"
        Write-Host "  命令输出:" -ForegroundColor Gray
        $result.Output | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        
        Remove-SSHSession -SessionId $session.SessionId | Out-Null
        Write-Host "`n✓ Posh-SSH 连接测试成功`n" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 连接失败" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ 连接错误: $_" -ForegroundColor Red
    Write-Host "  错误详情: $($_.Exception.Message)" -ForegroundColor Red
}

# 方法 2: 使用 sshpass (如果可用)
Write-Host "[方法 2] 使用 sshpass 测试..." -ForegroundColor Cyan
if (Get-Command sshpass -ErrorAction SilentlyContinue) {
    $env:SSHPASS = $Password
    try {
        $result = sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "${Username}@${ServerIP}" "echo 'sshpass 测试成功'; whoami" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ sshpass 连接成功" -ForegroundColor Green
            Write-Host "  输出: $result" -ForegroundColor Gray
        } else {
            Write-Host "  ✗ sshpass 连接失败" -ForegroundColor Red
            Write-Host "  输出: $result" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ✗ sshpass 错误: $_" -ForegroundColor Red
    }
    Remove-Item Env:\SSHPASS
} else {
    Write-Host "  ⊘ sshpass 未安装，跳过" -ForegroundColor Yellow
}

# 方法 3: 使用原生 SSH (需要手动输入密码)
Write-Host "[方法 3] 使用原生 SSH 测试..." -ForegroundColor Cyan
Write-Host "  提示: 这将打开交互式 SSH 会话，需要手动输入密码" -ForegroundColor Yellow
Write-Host "  命令: ssh ${Username}@${ServerIP}" -ForegroundColor Gray
Write-Host "  密码: $Password" -ForegroundColor Gray

# 显示密码字符（用于验证）
Write-Host "`n密码验证:" -ForegroundColor Cyan
Write-Host "  原始密码: $Password" -ForegroundColor Gray
Write-Host "  密码字符: $($Password.ToCharArray() -join ' ')" -ForegroundColor Gray
Write-Host "  密码长度: $($Password.Length)" -ForegroundColor Gray

# 检查密码中是否有特殊字符
$specialChars = @('$', '`', '"', "'", '\', '|', '&', ';', '(', ')', '<', '>', ' ', '*', '?', '[', ']', '{', '}')
$hasSpecial = $false
foreach ($char in $specialChars) {
    if ($Password.Contains($char)) {
        Write-Host "  警告: 密码包含特殊字符 '$char'，可能需要转义" -ForegroundColor Yellow
        $hasSpecial = $true
    }
}
if (-not $hasSpecial) {
    Write-Host "  ✓ 密码不包含需要转义的特殊字符" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "建议:" -ForegroundColor Yellow
Write-Host "1. 确认密码是否正确: $Password" -ForegroundColor White
Write-Host "2. 尝试手动 SSH 连接: ssh ${Username}@${ServerIP}" -ForegroundColor White
Write-Host "3. 检查服务器是否允许密码认证" -ForegroundColor White
Write-Host "4. 验证用户名是否正确" -ForegroundColor White

