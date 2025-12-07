# ============================================================
# Check Server Services Running Status Remotely
# ============================================================
# 
# Running Environment: Local Windows Environment
# Function: Connect to server and check backend/frontend services
# 
# One-click execution: .\scripts\local\check-server-services-remote.ps1
# ============================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "165.154.255.48",
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$Password = "8iDcGrYb52Fxpzee"
)

$ErrorActionPreference = "Continue"

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🔍 检查服务器前后端服务运行状态" -ForegroundColor Cyan
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
    Write-Host "`n请检查:" -ForegroundColor Yellow
    Write-Host "  1. 服务器 IP 地址是否正确" -ForegroundColor White
    Write-Host "  2. 服务器密码是否正确" -ForegroundColor White
    Write-Host "  3. 网络连接是否正常`n" -ForegroundColor White
    exit 1
}

Write-Host ""

# Execute service check
Write-Host "[2/2] 检查前后端服务状态..." -ForegroundColor Yellow
Write-Host ""

$checkCommand = "cd /home/ubuntu/telegram-ai-system && bash scripts/server/check-services-running.sh"
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

