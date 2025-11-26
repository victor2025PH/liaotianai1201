# 简单部署脚本 - 避免编码问题
param(
    [string]$ServerIP = "165.154.254.99",
    [string]$Username = "ubuntu",
    [string]$Password = "Along2025!!!"
)

Write-Host "`n开始部署到服务器: $ServerIP`n" -ForegroundColor Cyan

# 检查 Posh-SSH
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Install-Module -Name Posh-SSH -Force -Scope CurrentUser
}
Import-Module Posh-SSH

# 连接
$securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential($Username, $securePassword)
$session = New-SSHSession -ComputerName $ServerIP -Credential $credential -AcceptKey

if (-not $session) {
    Write-Host "连接失败" -ForegroundColor Red
    exit 1
}

Write-Host "连接成功`n" -ForegroundColor Green

# 检查状态
Write-Host "检查部署状态..." -ForegroundColor Yellow
$checkCmd = 'bash -c "systemctl is-active smart-tg-backend 2>/dev/null && echo BACKEND_RUNNING || echo BACKEND_STOPPED; systemctl is-active smart-tg-frontend 2>/dev/null && echo FRONTEND_RUNNING || echo FRONTEND_STOPPED; curl -s http://localhost:8000/health || echo HEALTH_FAILED"'
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command $checkCmd
Write-Host $result.Output

# 上传文件
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$files = @("auto_deploy.sh", "smart-tg-backend.service", "smart-tg-frontend.service")
$tempDir = "/tmp/deploy-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

Invoke-SSHCommand -SessionId $session.SessionId -Command "mkdir -p $tempDir" | Out-Null

foreach ($file in $files) {
    $localPath = Join-Path $scriptDir $file
    if (Test-Path $localPath) {
        Set-SCPFile -ComputerName $ServerIP -Credential $credential -LocalFile $localPath -RemotePath "$tempDir/$file" -AcceptKey
        Write-Host "已上传: $file" -ForegroundColor Green
    }
}

# 执行部署
Write-Host "`n执行部署..." -ForegroundColor Yellow
$deployCmd = "cd $tempDir; chmod +x auto_deploy.sh; sudo bash auto_deploy.sh"
$deployResult = Invoke-SSHCommand -SessionId $session.SessionId -Command $deployCmd -TimeOut 600
Write-Host $deployResult.Output

# 最终检查
Write-Host "`n最终检查..." -ForegroundColor Yellow
$finalCmd = 'bash -c "systemctl is-active smart-tg-backend && echo OK_BACKEND || echo FAIL_BACKEND; systemctl is-active smart-tg-frontend && echo OK_FRONTEND || echo FAIL_FRONTEND"'
$finalResult = Invoke-SSHCommand -SessionId $session.SessionId -Command $finalCmd
Write-Host $finalResult.Output

Remove-SSHSession -SessionId $session.SessionId | Out-Null
Write-Host ""
Write-Host "完成！" -ForegroundColor Green

