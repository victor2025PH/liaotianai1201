# 修复 SSH 密码问题脚本
# 使用方法: .\fix_ssh_password.ps1 -ServerIP <ip> -Password <pass>

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
Write-Host "修复 SSH 密码问题" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "服务器: $ServerIP" -ForegroundColor Cyan
Write-Host "用户名: $Username" -ForegroundColor Cyan
Write-Host "`n正在测试不同的密码格式...`n" -ForegroundColor Yellow

# 检查 Posh-SSH 模块
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Install-Module -Name Posh-SSH -Force -Scope CurrentUser
}

Import-Module Posh-SSH

# 测试不同的密码格式
$passwordVariants = @(
    @{ Name = "原始密码"; Value = $Password },
    @{ Name = "去除首尾空格"; Value = $Password.Trim() },
    @{ Name = "URL 编码"; Value = [System.Web.HttpUtility]::UrlEncode($Password) },
    @{ Name = "HTML 编码"; Value = [System.Web.HttpUtility]::HtmlEncode($Password) }
)

foreach ($variant in $passwordVariants) {
    Write-Host "测试: $($variant.Name)..." -ForegroundColor Cyan -NoNewline
    
    try {
        $securePassword = ConvertTo-SecureString $variant.Value -AsPlainText -Force
        $credential = New-Object System.Management.Automation.PSCredential($Username, $securePassword)
        $session = New-SSHSession -ComputerName $ServerIP -Credential $credential -AcceptKey -ConnectionTimeout 10
        
        if ($session) {
            Write-Host " ✓ 成功！" -ForegroundColor Green
            Write-Host "  使用此密码格式: $($variant.Name)" -ForegroundColor Green
            
            # 测试命令
            $result = Invoke-SSHCommand -SessionId $session.SessionId -Command "echo '连接成功'; whoami"
            Write-Host "  验证: $($result.Output)" -ForegroundColor Gray
            
            Remove-SSHSession -SessionId $session.SessionId | Out-Null
            break
        } else {
            Write-Host " ✗ 失败" -ForegroundColor Red
        }
    } catch {
        Write-Host " ✗ 错误: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "手动测试建议" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "如果所有方法都失败，请尝试手动连接:" -ForegroundColor Yellow
Write-Host "`n1. 使用 PowerShell SSH:" -ForegroundColor Cyan
Write-Host "   ssh ${Username}@${ServerIP}" -ForegroundColor White
Write-Host "   密码: $Password" -ForegroundColor Gray

Write-Host "`n2. 使用 PuTTY 或其他 SSH 客户端" -ForegroundColor Cyan

Write-Host "`n3. 检查密码是否正确:" -ForegroundColor Cyan
Write-Host "   原始密码: $Password" -ForegroundColor White
Write-Host "   密码长度: $($Password.Length) 字符" -ForegroundColor White

Write-Host "`n4. 可能的原因:" -ForegroundColor Cyan
Write-Host "   • 密码可能已被服务器管理员更改" -ForegroundColor Yellow
Write-Host "   • 服务器可能禁用了密码认证" -ForegroundColor Yellow
Write-Host "   • 密码中可能有特殊字符需要转义" -ForegroundColor Yellow
Write-Host "   • 用户名可能不正确" -ForegroundColor Yellow

Write-Host "`n5. 建议操作:" -ForegroundColor Cyan
Write-Host "   • 联系服务器提供商确认密码" -ForegroundColor White
Write-Host "   • 检查服务器 SSH 配置" -ForegroundColor White
Write-Host "   • 尝试使用 SSH 密钥认证" -ForegroundColor White

