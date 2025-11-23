# 修复所有服务器部署
# 使用方法: .\fix_all_servers.ps1

$ErrorActionPreference = "Continue"

# 服务器配置
$servers = @(
    @{
        Name = "洛杉矶服务器"
        IP = "165.154.255.48"
        Username = "ubuntu"
        Password = "8iDcGrYb52Fxpzee"
    },
    @{
        Name = "马尼拉服务器"
        IP = "165.154.233.179"
        Username = "ubuntu"
        Password = "8iDcGrYb52Fxpzee"
    }
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "修复所有服务器部署" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

foreach ($server in $servers) {
    Write-Host "`n修复: $($server.Name) ($($server.IP))" -ForegroundColor Yellow
    Write-Host "========================================`n" -ForegroundColor Yellow
    
    & "$PSScriptRoot\fix_deployment.ps1" `
        -ServerIP $server.IP `
        -Username $server.Username `
        -Password $server.Password
    
    Start-Sleep -Seconds 2
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "所有服务器修复完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

