# 全自动远程部署脚本
# 从 Windows 本地自动部署到 Linux 服务器

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "root",
    
    [Parameter(Mandatory=$false)]
    [string]$Password = "",
    
    [Parameter(Mandatory=$false)]
    [string]$ProjectPath = "/opt/smart-tg"
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Smart TG 全自动远程部署" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 检查参数
if ([string]::IsNullOrEmpty($ServerIP)) {
    Write-Host "错误: 请提供服务器 IP 地址" -ForegroundColor Red
    Write-Host "使用方法: .\auto_deploy_remote.ps1 -ServerIP <ip> -Username <user> -Password <pass>" -ForegroundColor Yellow
    exit 1
}

if ([string]::IsNullOrEmpty($Password)) {
    Write-Host "错误: 请提供服务器密码" -ForegroundColor Red
    exit 1
}

Write-Host "服务器信息:" -ForegroundColor Cyan
Write-Host "  IP: $ServerIP" -ForegroundColor White
Write-Host "  用户: $Username" -ForegroundColor White
Write-Host "  项目路径: $ProjectPath`n" -ForegroundColor White

# 检查 Posh-SSH 模块
Write-Host "[1/10] 检查 Posh-SSH 模块..." -ForegroundColor Yellow
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Write-Host "安装 Posh-SSH 模块..." -ForegroundColor Yellow
    Install-Module -Name Posh-SSH -Force -Scope CurrentUser -AllowClobber
}
Import-Module Posh-SSH
Write-Host "✓ Posh-SSH 模块已加载" -ForegroundColor Green

# 测试连接
Write-Host "`n[2/10] 测试服务器连接..." -ForegroundColor Yellow
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

# 检查系统环境
Write-Host "`n[3/10] 检查系统环境..." -ForegroundColor Yellow
$envCheck = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
echo "=== 系统信息 ==="
uname -a
echo ""
echo "=== Python ==="
python3 --version 2>/dev/null || echo "Python3 未安装"
echo ""
echo "=== Node.js ==="
node --version 2>/dev/null || echo "Node.js 未安装"
echo ""
echo "=== 磁盘空间 ==="
df -h / | tail -1
"@

Write-Host $envCheck.Output

# 创建项目目录
Write-Host "`n[4/10] 创建项目目录..." -ForegroundColor Yellow
$createDir = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
sudo mkdir -p $ProjectPath/{admin-backend,saas-demo,data,logs}
sudo chown -R `$USER:`$USER $ProjectPath
echo "目录创建完成"
"@

if ($createDir.ExitStatus -eq 0) {
    Write-Host "✓ 项目目录已创建" -ForegroundColor Green
} else {
    Write-Host "⚠ 目录创建可能有问题: $($createDir.Output)" -ForegroundColor Yellow
}

# 获取当前脚本目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$deployFiles = @(
    "auto_deploy.sh",
    "smart-tg-backend.service",
    "smart-tg-frontend.service",
    "check_deployment.sh"
)

# 上传部署文件
Write-Host "`n[5/10] 上传部署文件..." -ForegroundColor Yellow
$tempDir = "/tmp/smart-tg-deploy-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

$uploadResult = Invoke-SSHCommand -SessionId $session.SessionId -Command "mkdir -p $tempDir"
if ($uploadResult.ExitStatus -eq 0) {
    Write-Host "✓ 临时目录已创建" -ForegroundColor Green
}

foreach ($file in $deployFiles) {
    $localPath = Join-Path $scriptDir $file
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

# 修改部署脚本中的路径
Write-Host "`n[6/10] 配置部署脚本..." -ForegroundColor Yellow
$configScript = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $tempDir
sed -i 's|/opt/smart-tg|$ProjectPath|g' auto_deploy.sh
sed -i 's|/opt/smart-tg|$ProjectPath|g' smart-tg-backend.service
sed -i 's|/opt/smart-tg|$ProjectPath|g' smart-tg-frontend.service
chmod +x auto_deploy.sh check_deployment.sh
echo "配置完成"
"@

if ($configScript.ExitStatus -eq 0) {
    Write-Host "✓ 部署脚本已配置" -ForegroundColor Green
}

# 检查代码是否已上传
Write-Host "`n[7/10] 检查代码目录..." -ForegroundColor Yellow
$codeCheck = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
if [ -d "$ProjectPath/admin-backend" ] && [ -f "$ProjectPath/admin-backend/requirements.txt" ]; then
    echo "BACKEND_EXISTS"
else
    echo "BACKEND_MISSING"
fi
if [ -d "$ProjectPath/saas-demo" ] && [ -f "$ProjectPath/saas-demo/package.json" ]; then
    echo "FRONTEND_EXISTS"
else
    echo "FRONTEND_MISSING"
fi
"@

$backendExists = $codeCheck.Output -match "BACKEND_EXISTS"
$frontendExists = $codeCheck.Output -match "FRONTEND_EXISTS"

if (-not $backendExists) {
    Write-Host "⚠ 后端代码未上传，请先上传代码到 $ProjectPath/admin-backend" -ForegroundColor Yellow
    Write-Host "  或使用以下命令上传:" -ForegroundColor Yellow
    Write-Host "  scp -r admin-backend/* $Username@${ServerIP}:$ProjectPath/admin-backend/" -ForegroundColor Gray
}

if (-not $frontendExists) {
    Write-Host "⚠ 前端代码未上传，请先上传代码到 $ProjectPath/saas-demo" -ForegroundColor Yellow
    Write-Host "  或使用以下命令上传:" -ForegroundColor Yellow
    Write-Host "  scp -r saas-demo/* $Username@${ServerIP}:$ProjectPath/saas-demo/" -ForegroundColor Gray
}

# 执行部署脚本
Write-Host "`n[8/10] 执行自动化部署..." -ForegroundColor Yellow
if ($backendExists -and $frontendExists) {
    $deployResult = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd $tempDir
sudo bash auto_deploy.sh 2>&1
"@ -TimeOut 300
    
    Write-Host $deployResult.Output
    
    if ($deployResult.ExitStatus -eq 0) {
        Write-Host "`n✓ 部署脚本执行完成" -ForegroundColor Green
    } else {
        Write-Host "`n⚠ 部署脚本执行可能有问题，退出码: $($deployResult.ExitStatus)" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠ 代码未完全上传，跳过自动部署" -ForegroundColor Yellow
    Write-Host "  请先上传代码，然后手动执行:" -ForegroundColor Yellow
    Write-Host "  ssh $Username@${ServerIP}" -ForegroundColor Gray
    Write-Host "  cd $tempDir && sudo bash auto_deploy.sh" -ForegroundColor Gray
}

# 检查部署状态
Write-Host "`n[9/10] 检查部署状态..." -ForegroundColor Yellow
$statusCheck = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
echo "=== 服务状态 ==="
sudo systemctl status smart-tg-backend --no-pager -l | head -n 5 || echo "后端服务未运行"
echo ""
sudo systemctl status smart-tg-frontend --no-pager -l | head -n 5 || echo "前端服务未运行"
echo ""
echo "=== 端口检查 ==="
sudo netstat -tlnp 2>/dev/null | grep -E ':8000|:3000' || echo "端口未被占用"
echo ""
echo "=== 健康检查 ==="
curl -s http://localhost:8000/health 2>/dev/null || echo "后端健康检查失败"
"@

Write-Host $statusCheck.Output

# 清理临时文件
Write-Host "`n[10/10] 清理临时文件..." -ForegroundColor Yellow
$cleanup = Invoke-SSHCommand -SessionId $session.SessionId -Command "rm -rf $tempDir"
Write-Host "✓ 临时文件已清理" -ForegroundColor Green

# 断开连接
Remove-SSHSession -SessionId $session.SessionId | Out-Null

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "后续操作:" -ForegroundColor Yellow
Write-Host "1. 检查服务状态:" -ForegroundColor White
Write-Host "   ssh $Username@${ServerIP}" -ForegroundColor Gray
Write-Host "   sudo systemctl status smart-tg-backend" -ForegroundColor Gray
Write-Host "   sudo systemctl status smart-tg-frontend" -ForegroundColor Gray
Write-Host ""
Write-Host "2. 查看日志:" -ForegroundColor White
Write-Host "   sudo journalctl -u smart-tg-backend -f" -ForegroundColor Gray
Write-Host "   sudo journalctl -u smart-tg-frontend -f" -ForegroundColor Gray
Write-Host ""
Write-Host "3. 访问服务:" -ForegroundColor White
Write-Host "   后端: http://${ServerIP}:8000" -ForegroundColor Gray
Write-Host "   前端: http://${ServerIP}:3000" -ForegroundColor Gray
Write-Host ""

