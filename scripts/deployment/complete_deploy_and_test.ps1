# 完整部署和测试脚本
# 使用方法: .\complete_deploy_and_test.ps1

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "完整部署和测试 - 所有服务器" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 服务器配置
$servers = @(
    @{
        Name = "洛杉矶服务器"
        IP = "165.154.255.48"
        Username = "ubuntu"
        Password = "8iDcGrYb52Fxpzee"
        DeployDir = "~/telegram-ai-system"
    },
    @{
        Name = "马尼拉服务器"
        IP = "165.154.233.179"
        Username = "ubuntu"
        Password = "8iDcGrYb52Fxpzee"
        DeployDir = "~/telegram-ai-system"
    },
    @{
        Name = "worker-01"
        IP = "165.154.254.99"
        Username = "ubuntu"
        Password = "Along2025!!!"
        DeployDir = "/opt/group-ai"
    }
)

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptPath)

foreach ($server in $servers) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "处理: $($server.Name) ($($server.IP))" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    # 步骤 1: 检查文件结构
    Write-Host "[步骤 1] 检查文件结构..." -ForegroundColor Yellow
    & pwsh -ExecutionPolicy Bypass -File "$scriptPath\diagnose_failure.ps1" `
        -ServerIP $server.IP `
        -Username $server.Username `
        -Password $server.Password `
        -ServerName $server.Name `
        -DeployDir $server.DeployDir | Select-Object -First 50
    
    # 步骤 2: 修复和部署
    Write-Host "`n[步骤 2] 修复和部署..." -ForegroundColor Yellow
    & pwsh -ExecutionPolicy Bypass -File "$scriptPath\fix_deployment_structure.ps1" `
        -ServerIP $server.IP `
        -Username $server.Username `
        -Password $server.Password `
        -ServerName $server.Name `
        -DeployDir $server.DeployDir
    
    # 步骤 3: 测试
    Write-Host "`n[步骤 3] 测试部署..." -ForegroundColor Yellow
    & pwsh -ExecutionPolicy Bypass -File "$scriptPath\test_deployment_complete.ps1" `
        -ServerIP $server.IP `
        -Username $server.Username `
        -Password $server.Password `
        -ServerName $server.Name
    
    Write-Host "`n"
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "所有服务器处理完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

