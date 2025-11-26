# 全自动部署脚本 v2
# 自动读取配置，检查部署状态，完成部署

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Smart TG 全自动部署系统" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 读取服务器配置
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$configPath = Join-Path $projectRoot "data\master_config.json"

if (-not (Test-Path $configPath)) {
    Write-Host "错误: 找不到配置文件: $configPath" -ForegroundColor Red
    Write-Host "请手动提供服务器信息" -ForegroundColor Yellow
    
    $ServerIP = Read-Host "请输入服务器 IP"
    $Username = Read-Host "请输入用户名 (默认: root)"
    if ([string]::IsNullOrEmpty($Username)) { $Username = "root" }
    $Password = Read-Host "请输入密码" -AsSecureString
    $Password = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Password))
    $ProjectPath = "/opt/smart-tg"
} else {
    Write-Host "[1/5] 读取服务器配置..." -ForegroundColor Yellow
    $config = Get-Content $configPath -Encoding UTF8 | ConvertFrom-Json
    $servers = $config.servers
    
    if ($servers.PSObject.Properties.Count -eq 0) {
        Write-Host "错误: 配置文件中没有服务器信息" -ForegroundColor Red
        exit 1
    }
    
    # 选择第一个服务器
    $serverName = $servers.PSObject.Properties.Name[0]
    $serverConfig = $servers.$serverName
    
    $ServerIP = $serverConfig.host
    $Username = $serverConfig.user
    $Password = $serverConfig.password
    $ProjectPath = if ($serverConfig.deploy_dir) { $serverConfig.deploy_dir } else { "/opt/smart-tg" }
    
    Write-Host "✓ 已选择服务器: $serverName ($ServerIP)" -ForegroundColor Green
}

Write-Host "`n服务器信息:" -ForegroundColor Cyan
Write-Host "  IP: $ServerIP" -ForegroundColor White
Write-Host "  用户: $Username" -ForegroundColor White
Write-Host "  项目路径: $ProjectPath`n" -ForegroundColor White

# 检查 Posh-SSH 模块
Write-Host "[2/5] 检查 Posh-SSH 模块..." -ForegroundColor Yellow
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Write-Host "安装 Posh-SSH 模块..." -ForegroundColor Yellow
    Install-Module -Name Posh-SSH -Force -Scope CurrentUser -AllowClobber
}
Import-Module Posh-SSH
Write-Host "✓ Posh-SSH 模块已加载" -ForegroundColor Green

# 连接服务器
Write-Host "`n[3/5] 连接服务器..." -ForegroundColor Yellow
try {
    $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential($Username, $securePassword)
    
    $session = New-SSHSession -ComputerName $ServerIP -Credential $credential -AcceptKey -ErrorAction Stop
    if ($session) {
        Write-Host "✓ 服务器连接成功" -ForegroundColor Green
    } else {
        Write-Host "✗ 服务器连接失败" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ 连接错误: $_" -ForegroundColor Red
    exit 1
}

# 检查当前部署状态
Write-Host "`n[4/5] 检查当前部署状态..." -ForegroundColor Yellow

# 上传检查脚本
$checkScriptPath = Join-Path $scriptDir "check_status.sh"
if (Test-Path $checkScriptPath) {
    $tempDir = "/tmp/smart-tg-deploy-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Invoke-SSHCommand -SessionId $session.SessionId -Command "mkdir -p $tempDir" | Out-Null
    
    Set-SCPFile -ComputerName $ServerIP -Credential $credential -LocalFile $checkScriptPath -RemotePath "$tempDir/check_status.sh" -AcceptKey
    Invoke-SSHCommand -SessionId $session.SessionId -Command "chmod +x $tempDir/check_status.sh" | Out-Null
    
    $statusCheck = Invoke-SSHCommand -SessionId $session.SessionId -Command "bash $tempDir/check_status.sh $ProjectPath" -TimeOut 30
    Write-Host $statusCheck.Output
    
    $backendRunning = $statusCheck.Output -match "BACKEND_RUNNING"
    $frontendRunning = $statusCheck.Output -match "FRONTEND_RUNNING"
    $backendDirExists = $statusCheck.Output -match "BACKEND_DIR_EXISTS"
    $frontendDirExists = $statusCheck.Output -match "FRONTEND_DIR_EXISTS"
} else {
    Write-Host "⚠ 检查脚本不存在，跳过状态检查" -ForegroundColor Yellow
    $backendRunning = $false
    $frontendRunning = $false
    $backendDirExists = $false
    $frontendDirExists = $false
}

# 执行部署
Write-Host "`n[5/5] 执行自动化部署..." -ForegroundColor Yellow

# 上传部署文件
$filesToUpload = @("auto_deploy.sh", "smart-tg-backend.service", "smart-tg-frontend.service")
foreach ($file in $filesToUpload) {
    $localPath = Join-Path $scriptDir $file
    if (Test-Path $localPath) {
        try {
            Set-SCPFile -ComputerName $ServerIP -Credential $credential -LocalFile $localPath -RemotePath "$tempDir/$file" -AcceptKey
            Write-Host "  ✓ 已上传: $file" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ 上传失败: $file - $_" -ForegroundColor Red
        }
    }
}

# 配置并执行部署脚本
Write-Host "`n执行部署脚本..." -ForegroundColor Cyan
$deployCmd = "cd $tempDir; sed -i 's|/opt/smart-tg|$ProjectPath|g' auto_deploy.sh; sed -i 's|/opt/smart-tg|$ProjectPath|g' smart-tg-backend.service; sed -i 's|/opt/smart-tg|$ProjectPath|g' smart-tg-frontend.service; chmod +x auto_deploy.sh; sudo bash auto_deploy.sh"
$deployResult = Invoke-SSHCommand -SessionId $session.SessionId -Command $deployCmd -TimeOut 600

Write-Host $deployResult.Output

# 最终状态检查
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "最终部署状态检查" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$finalCheckPath = Join-Path $scriptDir "final_check.sh"
if (Test-Path $finalCheckPath) {
    Set-SCPFile -ComputerName $ServerIP -Credential $credential -LocalFile $finalCheckPath -RemotePath "$tempDir/final_check.sh" -AcceptKey
    Invoke-SSHCommand -SessionId $session.SessionId -Command "chmod +x $tempDir/final_check.sh" | Out-Null
    $finalCheck = Invoke-SSHCommand -SessionId $session.SessionId -Command "bash $tempDir/final_check.sh" -TimeOut 30
    Write-Host $finalCheck.Output
}

# 清理
Invoke-SSHCommand -SessionId $session.SessionId -Command "rm -rf $tempDir" | Out-Null
Remove-SSHSession -SessionId $session.SessionId | Out-Null

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "访问地址:" -ForegroundColor Yellow
Write-Host "  后端: http://${ServerIP}:8000" -ForegroundColor White
Write-Host "  前端: http://${ServerIP}:3000" -ForegroundColor White
Write-Host "  API 文档: http://${ServerIP}:8000/docs`n" -ForegroundColor White

Write-Host "管理命令:" -ForegroundColor Yellow
Write-Host "  ssh $Username@${ServerIP}" -ForegroundColor Gray
Write-Host "  sudo systemctl status smart-tg-backend" -ForegroundColor Gray
Write-Host "  sudo systemctl status smart-tg-frontend" -ForegroundColor Gray
Write-Host ""

