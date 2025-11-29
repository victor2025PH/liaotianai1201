# ===========================================
# 推送到 GitHub 并触发服务器部署
# ===========================================
param(
    [Parameter(Mandatory=$false)]
    [string]$CommitMessage = "自动部署：修复和更新",
    
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "165.154.233.55",
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$Password = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipPush = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDeploy = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$AutoAdd = $true
)

$ErrorActionPreference = "Continue"

function Write-Step { param([string]$Message) Write-Host "`n[$([char]0x2192)] $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message) Write-Host "[✓] $Message" -ForegroundColor Green }
function Write-Error { param([string]$Message) Write-Host "[✗] $Message" -ForegroundColor Red }
function Write-Info { param([string]$Message) Write-Host "[i] $Message" -ForegroundColor Gray }

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  推送到 GitHub 并触发服务器部署" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Git 状态
Write-Step "步骤 1: 检查 Git 状态"
$gitStatus = git status --short 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "当前目录不是 Git 仓库"
    exit 1
}

if ($gitStatus) {
    Write-Host "  发现以下修改：" -ForegroundColor Yellow
    $gitStatus | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    Write-Host ""
    
    if ($AutoAdd) {
        Write-Info "  自动添加所有修改的文件..."
        git add .
        Write-Success "所有文件已添加到暂存区"
    } else {
        $addAll = Read-Host "  是否添加所有修改的文件？(Y/n)"
        if ($addAll -ne "n" -and $addAll -ne "N") {
            git add .
            Write-Success "所有文件已添加到暂存区"
        }
    }
} else {
    Write-Success "没有未提交的修改"
    
    # 检查是否有未推送的提交
    $localCommits = git log origin/master..HEAD --oneline 2>&1
    if ($localCommits -and $localCommits -notmatch "fatal") {
        Write-Info "发现未推送的本地提交："
        $localCommits | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    }
}
Write-Host ""

# 2. 提交到本地
Write-Step "步骤 2: 提交到本地仓库"
$hasStaged = (git diff --cached --quiet) -and ($LASTEXITCODE -eq 0)
if (-not $hasStaged) {
    Write-Info "提交信息: $CommitMessage"
    git commit -m $CommitMessage
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "提交完成"
        
        # 显示提交信息
        $lastCommit = git log -1 --oneline
        Write-Info "最新提交: $lastCommit"
    } else {
        Write-Error "提交失败"
        exit 1
    }
} else {
    Write-Host "  ⚠ 没有暂存的文件，跳过提交" -ForegroundColor Yellow
}
Write-Host ""

# 3. 推送到 GitHub
if (-not $SkipPush) {
    Write-Step "步骤 3: 推送到 GitHub"
    Write-Info "推送到 origin master..."
    
    # 获取当前分支
    $currentBranch = git branch --show-current
    Write-Info "当前分支: $currentBranch"
    
    git push origin $currentBranch
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "推送成功"
        
        # 显示远程仓库信息
        $remoteUrl = git remote get-url origin 2>&1
        if ($remoteUrl -and $remoteUrl -notmatch "fatal") {
            Write-Info "远程仓库: $remoteUrl"
        }
    } else {
        Write-Error "推送失败，错误码: $LASTEXITCODE"
        Write-Info "请检查："
        Write-Info "  1. 是否有推送权限"
        Write-Info "  2. 远程仓库 URL 是否正确"
        Write-Info "  3. 网络连接是否正常"
        exit 1
    }
    Write-Host ""
} else {
    Write-Host "  ⚠ 步骤 3: 跳过推送到 GitHub（SkipPush = true）" -ForegroundColor Yellow
    Write-Host ""
}

# 4. 在服务器上拉取并部署
if (-not $SkipDeploy) {
    Write-Step "步骤 4: 在服务器上拉取并部署"
    
    # 检查部署脚本是否存在
    $deployScriptPath = Join-Path $PSScriptRoot "从GitHub拉取并部署.sh"
    if (-not (Test-Path $deployScriptPath)) {
        Write-Error "部署脚本不存在: $deployScriptPath"
        exit 1
    }
    
    # 先上传部署脚本（如果服务器上没有或需要更新）
    Write-Info "上传/更新部署脚本..."
    
    $scriptContent = Get-Content $deployScriptPath -Raw -Encoding UTF8
    $base64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($scriptContent))
    
    $uploadCmd = "mkdir -p ~/liaotian/deploy && echo '$base64' | base64 -d > ~/liaotian/deploy/从GitHub拉取并部署.sh && chmod +x ~/liaotian/deploy/从GitHub拉取并部署.sh && echo 'SCRIPT_UPLOADED'"
    
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
    
    # 执行部署脚本
    Write-Host ""
    Write-Info "在服务器上执行部署..."
    Write-Info "服务器: $Username@$ServerIP"
    
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
    } else {
        Write-Error "服务器部署失败（退出码: $exitCode）"
        Write-Info "请手动登录服务器检查日志"
        exit 1
    }
    Write-Host ""
} else {
    Write-Host "  ⚠ 步骤 4: 跳过服务器部署（SkipDeploy = true）" -ForegroundColor Yellow
    Write-Info "如需手动部署，请执行:"
    Write-Info "  ssh $Username@$ServerIP 'bash ~/liaotian/deploy/从GitHub拉取并部署.sh'"
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Info "总结:"
Write-Info "  - 本地修改已提交并推送到 GitHub"
if (-not $SkipDeploy) {
    Write-Info "  - 服务器已从 GitHub 拉取最新代码"
    Write-Info "  - 后端服务已重启"
}
Write-Host ""
