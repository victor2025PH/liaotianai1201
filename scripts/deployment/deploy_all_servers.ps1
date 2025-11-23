# 部署到所有服务器
# 使用方法: .\deploy_all_servers.ps1

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
Write-Host "批量部署到所有服务器" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

foreach ($server in $servers) {
    Write-Host "`n部署到: $($server.Name) ($($server.IP))" -ForegroundColor Yellow
    Write-Host "========================================`n" -ForegroundColor Yellow
    
    & "$PSScriptRoot\deploy_to_server.ps1" `
        -ServerIP $server.IP `
        -Username $server.Username `
        -Password $server.Password `
        -ServerName $server.Name
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✓ $($server.Name) 部署成功`n" -ForegroundColor Green
    } else {
        Write-Host "`n✗ $($server.Name) 部署失败`n" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 2
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "批量部署完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "服务器列表:" -ForegroundColor Yellow
foreach ($server in $servers) {
    Write-Host "  • $($server.Name): http://$($server.IP):8000" -ForegroundColor Cyan
}

