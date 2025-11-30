# 执行测试部署 - 简化版
# 直接测试服务器部署脚本，验证行尾符修复

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "165.154.233.55",
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "ubuntu"
)

$ErrorActionPreference = "Continue"

function Write-Step { param([string]$Message) Write-Host "`n[$([char]0x2192)] $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message) Write-Host "[✓] $Message" -ForegroundColor Green }
function Write-Error { param([string]$Message) Write-Host "[✗] $Message" -ForegroundColor Red }
function Write-Info { param([string]$Message) Write-Host "[i] $Message" -ForegroundColor Gray }

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  执行测试部署流程" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Step "步骤 1: 上传部署脚本（带行尾符转换）"

$deployScriptPath = Join-Path $PSScriptRoot "从GitHub拉取并部署.sh"
if (-not (Test-Path $deployScriptPath)) {
    Write-Error "部署脚本不存在: $deployScriptPath"
    exit 1
}

Write-Info "读取脚本内容并转换行尾符..."
$scriptContent = Get-Content $deployScriptPath -Raw -Encoding UTF8
$scriptContent = $scriptContent -replace "`r`n", "`n" -replace "`r", "`n"

$base64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($scriptContent))

Write-Info "上传脚本到服务器..."
$uploadCmd = "mkdir -p ~/liaotian/deploy && echo '$base64' | base64 -d > ~/liaotian/deploy/从GitHub拉取并部署.sh && sed -i 's/\r$//' ~/liaotian/deploy/从GitHub拉取并部署.sh 2>/dev/null || sed -i '' 's/\r$//' ~/liaotian/deploy/从GitHub拉取并部署.sh 2>/dev/null || true && chmod +x ~/liaotian/deploy/从GitHub拉取并部署.sh && echo 'SCRIPT_UPLOADED'"

try {
    $result = ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$Username@$ServerIP" $uploadCmd 2>&1
    if ($result -match "SCRIPT_UPLOADED" -or $LASTEXITCODE -eq 0) {
        Write-Success "部署脚本上传成功"
    } else {
        Write-Host "  脚本上传可能有问题，但继续尝试..." -ForegroundColor Yellow
        Write-Host "  输出: $result" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ⚠ SSH 连接可能需要密码或密钥" -ForegroundColor Yellow
    Write-Host "  请手动执行: ssh $Username@$ServerIP" -ForegroundColor Gray
}

Write-Step "步骤 2: 在服务器上执行部署"

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "服务器部署输出:" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

$deployCmd = "bash ~/liaotian/deploy/从GitHub拉取并部署.sh"

try {
    ssh -o StrictHostKeyChecking=no "$Username@$ServerIP" $deployCmd
    $exitCode = $LASTEXITCODE
    
    Write-Host ""
    
    if ($exitCode -eq 0) {
        Write-Success "部署测试完成"
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  ✓ 测试成功！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
    } else {
        Write-Error "部署失败（退出码: $exitCode）"
        Write-Info "请检查上面的错误输出"
    }
} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  手动执行提示" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "如果 SSH 连接需要密码，请手动执行:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  ssh $Username@$ServerIP" -ForegroundColor White
    Write-Host "  bash ~/liaotian/deploy/从GitHub拉取并部署.sh" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
