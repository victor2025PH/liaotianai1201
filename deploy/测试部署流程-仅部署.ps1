# 测试部署流程（仅部署，不推送，因为代码已经在 GitHub）

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "165.154.233.55",
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$Password = ""
)

$ErrorActionPreference = "Continue"

function Write-Step { param([string]$Message) Write-Host "`n[$([char]0x2192)] $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message) Write-Host "[✓] $Message" -ForegroundColor Green }
function Write-Error { param([string]$Message) Write-Host "[✗] $Message" -ForegroundColor Red }
function Write-Info { param([string]$Message) Write-Host "[i] $Message" -ForegroundColor Gray }

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  测试部署流程 - 验证行尾符修复" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Step "步骤 1: 上传/更新部署脚本（带行尾符转换）"

$deployScriptPath = Join-Path $PSScriptRoot "从GitHub拉取并部署.sh"
if (-not (Test-Path $deployScriptPath)) {
    Write-Error "部署脚本不存在: $deployScriptPath"
    exit 1
}

# 读取脚本内容并转换行尾符从 CRLF 到 LF
$scriptContent = Get-Content $deployScriptPath -Raw -Encoding UTF8
# 将 Windows 行尾符 (\r\n) 替换为 Unix 行尾符 (\n)
$scriptContent = $scriptContent -replace "`r`n", "`n" -replace "`r", "`n"

$base64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($scriptContent))

# 上传脚本并在服务器上转换行尾符
$uploadCmd = "mkdir -p ~/liaotian/deploy && echo '$base64' | base64 -d > ~/liaotian/deploy/从GitHub拉取并部署.sh && sed -i 's/\r$//' ~/liaotian/deploy/从GitHub拉取并部署.sh 2>/dev/null || sed -i '' 's/\r$//' ~/liaotian/deploy/从GitHub拉取并部署.sh 2>/dev/null || true && chmod +x ~/liaotian/deploy/从GitHub拉取并部署.sh && echo 'SCRIPT_UPLOADED'"

if ($Password) {
    $env:SSHPASS = $Password
    $result = sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$Username@$ServerIP" $uploadCmd 2>&1
    Remove-Item Env:\SSHPASS -ErrorAction SilentlyContinue
} else {
    $result = ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$Username@$ServerIP" $uploadCmd 2>&1
}

if ($result -match "SCRIPT_UPLOADED" -or $LASTEXITCODE -eq 0) {
    Write-Success "部署脚本上传/更新成功"
} else {
    Write-Host "  ⚠ 部署脚本上传可能失败，继续尝试部署..." -ForegroundColor Yellow
}

Write-Step "步骤 2: 在服务器上执行部署"

$deployCmd = "bash ~/liaotian/deploy/从GitHub拉取并部署.sh"

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "服务器部署输出:" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

if ($Password) {
    $env:SSHPASS = $Password
    sshpass -e ssh -o StrictHostKeyChecking=no "$Username@$ServerIP" $deployCmd
    $exitCode = $LASTEXITCODE
    Remove-Item Env:\SSHPASS -ErrorAction SilentlyContinue
} else {
    ssh -o StrictHostKeyChecking=no "$Username@$ServerIP" $deployCmd
    $exitCode = $LASTEXITCODE
}

Write-Host ""

if ($exitCode -eq 0) {
    Write-Success "服务器部署完成"
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  部署测试成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Info "行尾符修复已验证有效"
    Write-Info "服务器脚本可以正常执行"
    Write-Info "代码已从 GitHub 成功拉取"
    Write-Info "后端服务已重启"
} else {
    Write-Error "服务器部署失败（退出码: $exitCode）"
    Write-Info "请检查上面的错误输出"
    exit 1
}
