# 全自动部署脚本
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
    
    # 选择服务器（如果有多个）
    if ($servers.PSObject.Properties.Count -gt 1) {
        Write-Host "`n发现多个服务器，请选择:" -ForegroundColor Cyan
        $serverList = @()
        $index = 1
        foreach ($key in $servers.PSObject.Properties.Name) {
            $server = $servers.$key
            Write-Host "  [$index] $key - $($server.host)" -ForegroundColor White
            $serverList += @{
                Key = $key
                Server = $server
            }
            $index++
        }
        
        $choice = Read-Host "`n请选择服务器 (1-$($serverList.Count))"
        $selected = $serverList[[int]$choice - 1]
        $serverConfig = $selected.Server
        $serverName = $selected.Key
    } else {
        $serverName = $servers.PSObject.Properties.Name[0]
        $serverConfig = $servers.$serverName
    }
    
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

# 构建检查脚本（使用单引号避免 PowerShell 解析）
$checkStatusScript = 'echo "=== 服务状态检查 ==="; if systemctl is-active --quiet smart-tg-backend 2>/dev/null; then echo "BACKEND_RUNNING"; systemctl status smart-tg-backend --no-pager -l | head -n 3; else echo "BACKEND_STOPPED"; fi; if systemctl is-active --quiet smart-tg-frontend 2>/dev/null; then echo "FRONTEND_RUNNING"; systemctl status smart-tg-frontend --no-pager -l | head -n 3; else echo "FRONTEND_STOPPED"; fi; echo ""; echo "=== 端口检查 ==="; sudo netstat -tlnp 2>/dev/null | grep -E ":8000|:3000" || echo "端口未被占用"; echo ""; echo "=== 健康检查 ==="; curl -s http://localhost:8000/health 2>/dev/null || echo "后端健康检查失败"; curl -s http://localhost:3000 >/dev/null 2>&1 && echo "前端可访问" || echo "前端不可访问"; echo ""; echo "=== 目录检查 ==="; [ -d "' + $ProjectPath + '/admin-backend" ] && echo "BACKEND_DIR_EXISTS" || echo "BACKEND_DIR_MISSING"; [ -d "' + $ProjectPath + '/saas-demo" ] && echo "FRONTEND_DIR_EXISTS" || echo "FRONTEND_DIR_MISSING"'

$statusCheck = Invoke-SSHCommand -SessionId $session.SessionId -Command "bash -c `"$checkStatusScript`"" -TimeOut 30

Write-Host $statusCheck.Output

$backendRunning = $statusCheck.Output -match "BACKEND_RUNNING"
$frontendRunning = $statusCheck.Output -match "FRONTEND_RUNNING"
$backendDirExists = $statusCheck.Output -match "BACKEND_DIR_EXISTS"
$frontendDirExists = $statusCheck.Output -match "FRONTEND_DIR_EXISTS"

# 执行部署
Write-Host "`n[5/5] 执行自动化部署..." -ForegroundColor Yellow

# 获取部署脚本目录
$deployScriptDir = $scriptDir

# 上传部署文件
$tempDir = "/tmp/smart-tg-deploy-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$uploadResult = Invoke-SSHCommand -SessionId $session.SessionId -Command "mkdir -p $tempDir"

$filesToUpload = @("auto_deploy.sh", "smart-tg-backend.service", "smart-tg-frontend.service")
foreach ($file in $filesToUpload) {
    $localPath = Join-Path $deployScriptDir $file
    if (Test-Path $localPath) {
        try {
            Set-SCPFile -ComputerName $ServerIP -Credential $credential -LocalFile $localPath -RemotePath "$tempDir/$file" -AcceptKey
            Write-Host "  ✓ 已上传: $file" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ 上传失败: $file - $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  ⚠ 文件不存在: $file" -ForegroundColor Yellow
    }
}

# 配置并执行部署脚本
$deployCmd1 = "cd $tempDir"
$deployCmd2 = "sed -i 's|/opt/smart-tg|$ProjectPath|g' auto_deploy.sh 2>/dev/null || true"
$deployCmd3 = "sed -i 's|/opt/smart-tg|$ProjectPath|g' smart-tg-backend.service 2>/dev/null || true"
$deployCmd4 = "sed -i 's|/opt/smart-tg|$ProjectPath|g' smart-tg-frontend.service 2>/dev/null || true"
$deployCmd5 = "chmod +x auto_deploy.sh"
$deployCmd6 = "sudo bash auto_deploy.sh 2>&1"
$deployScript = "$deployCmd1; $deployCmd2; $deployCmd3; $deployCmd4; $deployCmd5; $deployCmd6"

Write-Host "`n执行部署脚本..." -ForegroundColor Cyan
$deployResult = Invoke-SSHCommand -SessionId $session.SessionId -Command $deployScript -TimeOut 600

Write-Host $deployResult.Output

# 最终状态检查
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "最终部署状态检查" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$finalCheckScript = 'echo "=== 服务状态 ==="; systemctl is-active smart-tg-backend 2>/dev/null && echo "✓ 后端服务运行中" || echo "✗ 后端服务未运行"; systemctl is-active smart-tg-frontend 2>/dev/null && echo "✓ 前端服务运行中" || echo "✗ 前端服务未运行"; echo ""; echo "=== 健康检查 ==="; HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null); if [ -n "$HEALTH" ]; then echo "✓ 后端健康检查: $HEALTH"; else echo "✗ 后端健康检查失败"; fi; FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null); if [ "$FRONTEND" = "200" ]; then echo "✓ 前端服务可访问"; else echo "✗ 前端服务不可访问 (HTTP $FRONTEND)"; fi'

$finalCheck = Invoke-SSHCommand -SessionId $session.SessionId -Command "bash -c `"$finalCheckScript`"" -TimeOut 30

Write-Host $finalCheck.Output

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
Write-Host "  sudo journalctl -u smart-tg-backend -f" -ForegroundColor Gray
Write-Host ""
