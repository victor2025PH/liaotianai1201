#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建 GitHub 部署相关的所有脚本文件
"""

import os
from pathlib import Path

# 脚本目录
SCRIPT_DIR = Path(__file__).parent

# 1. 检查需要追踪的文件.ps1
check_script = '''# 检查哪些文件需要被 Git 追踪
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "检查需要被 Git 追踪的文件" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查未追踪的文件
Write-Host "【1】未追踪的文件:" -ForegroundColor Yellow
$untracked = git ls-files --others --exclude-standard
if ($untracked) {
    $untracked | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
} else {
    Write-Host "  ✓ 没有未追踪的文件" -ForegroundColor Green
}
Write-Host ""

# 2. 检查已修改但未暂存的文件
Write-Host "【2】已修改但未暂存的文件:" -ForegroundColor Yellow
$modified = git diff --name-only
if ($modified) {
    $modified | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
} else {
    Write-Host "  ✓ 没有未暂存的修改" -ForegroundColor Green
}
Write-Host ""

# 3. 检查已暂存的文件
Write-Host "【3】已暂存的文件:" -ForegroundColor Yellow
$staged = git diff --cached --name-only
if ($staged) {
    $staged | ForEach-Object { Write-Host "  + $_" -ForegroundColor Green }
} else {
    Write-Host "  (无)" -ForegroundColor Gray
}
Write-Host ""

# 4. 检查关键文件是否被追踪
Write-Host "【4】关键文件追踪状态:" -ForegroundColor Yellow
$keyFiles = @(
    "admin-backend/app/api/group_ai/accounts.py",
    "deploy/最终完整修复方案.sh",
    "deploy/从GitHub拉取并部署.sh",
    "deploy/推送到GitHub并部署.ps1",
    "deploy/检查需要追踪的文件.ps1"
)
foreach ($file in $keyFiles) {
    if (Test-Path $file) {
        $tracked = git ls-files $file 2>$null
        if ($tracked) {
            Write-Host "  ✓ $file (已追踪)" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $file (未追踪)" -ForegroundColor Red
        }
    } else {
        Write-Host "  ⚠ $file (不存在)" -ForegroundColor Yellow
    }
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "检查完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
'''

# 2. 从GitHub拉取并部署.sh
deploy_script = '''#!/bin/bash
# 从 GitHub 拉取最新代码并部署
# 使用方法: bash ~/liaotian/deploy/从GitHub拉取并部署.sh

set -e

echo "========================================="
echo "从 GitHub 拉取最新代码并部署"
echo "开始时间: $(date)"
echo "========================================="
echo ""

cd ~/liaotian

# 检查 Git 仓库
if [ ! -d ".git" ]; then
    echo "✗ 当前目录不是 Git 仓库"
    echo "  请先克隆仓库: git clone https://github.com/victor2025PH/liaotianai1201.git ."
    exit 1
fi

# 1. 备份当前代码
echo "【步骤1】备份当前代码..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p ~/backups/$BACKUP_DIR
if [ -f "admin-backend/app/api/group_ai/accounts.py" ]; then
    cp admin-backend/app/api/group_ai/accounts.py ~/backups/$BACKUP_DIR/accounts.py 2>/dev/null || true
    echo "  ✓ 备份 accounts.py"
fi
echo ""

# 2. 从 GitHub 拉取最新代码
echo "【步骤2】从 GitHub 拉取最新代码..."
git fetch --all
BRANCH=$(git branch --show-current 2>/dev/null || echo "master")
echo "  当前分支: $BRANCH"
git pull origin $BRANCH || git pull origin master || git pull origin main

if [ $? -eq 0 ]; then
    echo "  ✓ 代码拉取完成"
    echo ""
    echo "  最近的提交:"
    git log --oneline -3 | head -3
else
    echo "  ✗ 代码拉取失败"
    exit 1
fi
echo ""

# 3. 验证关键文件
echo "【步骤3】验证关键文件..."
if [ -f "admin-backend/app/api/group_ai/accounts.py" ]; then
    UPSERT_COUNT=$(grep -c "UPSERT" admin-backend/app/api/group_ai/accounts.py 2>/dev/null || echo "0")
    echo "  ✓ accounts.py 存在（包含 $UPSERT_COUNT 处 UPSERT）"
else
    echo "  ✗ accounts.py 不存在"
fi
echo ""

# 4. 重启后端服务
echo "【步骤4】重启后端服务..."
cd ~/liaotian/admin-backend

if [ ! -d ".venv" ]; then
    echo "  ⚠ 虚拟环境不存在，正在创建..."
    python3 -m venv .venv
fi

source .venv/bin/activate 2>/dev/null || true

echo "  停止旧服务..."
pkill -9 -f 'uvicorn.*app.main:app' || true
pkill -9 -f 'python.*uvicorn.*app.main' || true
sleep 3

echo "  清理 Python 缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "  启动新服务..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "  后端进程 PID: $BACKEND_PID"

echo "  等待服务启动（最多30秒）..."
STARTED=0
for i in {1..15}; do
    sleep 2
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✓ 后端服务已启动（等待了 $((i*2)) 秒）"
        STARTED=1
        break
    fi
done

if [ $STARTED -eq 0 ]; then
    echo "  ⚠ 服务启动超时，查看日志..."
    tail -30 /tmp/backend.log
fi
echo ""

# 5. 验证服务
echo "【步骤5】验证服务..."
if curl -s http://localhost:8000/health | grep -q "ok" 2>/dev/null; then
    echo "  ✓ 后端服务正常运行"
    
    # 显示健康检查响应
    echo ""
    echo "  健康检查响应:"
    curl -s http://localhost:8000/health | head -3
else
    echo "  ✗ 后端服务未正常响应"
    echo "  查看日志:"
    tail -50 /tmp/backend.log | grep -E "ERROR|Exception|Traceback" | tail -10
    exit 1
fi
echo ""

echo "========================================="
echo "部署完成！"
echo "完成时间: $(date)"
echo "========================================="
echo ""
echo "备份位置: ~/backups/$BACKUP_DIR"
echo "后端日志: /tmp/backend.log"
echo ""
'''

# 3. 推送到GitHub并部署.ps1
push_deploy_script = '''# ===========================================
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
'''

# 创建文件
files_to_create = {
    '检查需要追踪的文件.ps1': check_script,
    '从GitHub拉取并部署.sh': deploy_script,
    '推送到GitHub并部署.ps1': push_deploy_script,
}

print("=" * 60)
print("创建 GitHub 部署脚本文件")
print("=" * 60)
print("")

for filename, content in files_to_create.items():
    filepath = SCRIPT_DIR / filename
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 如果是 .sh 文件，设置可执行权限（Windows 下可能无效）
        if filename.endswith('.sh'):
            try:
                os.chmod(filepath, 0o755)
            except:
                pass  # Windows 下不支持 chmod
        
        print(f"✓ 已创建: {filename}")
        print(f"  路径: {filepath}")
        print(f"  大小: {len(content)} 字节")
        print("")
    except Exception as e:
        print(f"✗ 创建失败: {filename}")
        print(f"  错误: {e}")
        print("")

print("=" * 60)
print("所有文件创建完成！")
print("=" * 60)
print("")
print("接下来可以:")
print("1. 运行检查脚本: .\\deploy\\检查需要追踪的文件.ps1")
print("2. 使用部署脚本: .\\deploy\\推送到GitHub并部署.ps1")
print("")
