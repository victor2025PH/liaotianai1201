# Git推送验证脚本
# 用于验证文件是否正确添加到Git并推送到GitHub

param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Git 推送验证工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查文件是否存在
Write-Host "[1/7] 检查文件是否存在..." -ForegroundColor Yellow
if (Test-Path $FilePath) {
    Write-Host "  ✓ 文件存在: $FilePath" -ForegroundColor Green
    $FileInfo = Get-Item $FilePath
    Write-Host "  文件大小: $($FileInfo.Length) 字节" -ForegroundColor Gray
} else {
    Write-Host "  ✗ 文件不存在: $FilePath" -ForegroundColor Red
    exit 1
}

# 2. 检查文件是否被.gitignore忽略
Write-Host ""
Write-Host "[2/7] 检查是否被.gitignore忽略..." -ForegroundColor Yellow
$gitIgnoreCheck = git check-ignore -v $FilePath 2>&1
if ($gitIgnoreCheck -match "\.gitignore") {
    Write-Host "  ✗ 文件被.gitignore忽略:" -ForegroundColor Red
    Write-Host "    $gitIgnoreCheck" -ForegroundColor Red
    Write-Host ""
    Write-Host "  解决方案: 需要从.gitignore中移除相关规则或使用 git add -f" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "  ✓ 文件未被忽略" -ForegroundColor Green
}

# 3. 检查文件是否已添加到暂存区
Write-Host ""
Write-Host "[3/7] 检查文件是否已添加到暂存区..." -ForegroundColor Yellow
$staged = git diff --cached --name-only | Select-String -Pattern ([regex]::Escape($FilePath))
if ($staged) {
    Write-Host "  ✓ 文件已在暂存区" -ForegroundColor Green
} else {
    Write-Host "  ⚠ 文件未在暂存区，尝试添加..." -ForegroundColor Yellow
    git add $FilePath
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ 文件已添加到暂存区" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 添加失败" -ForegroundColor Red
        exit 1
    }
}

# 4. 检查文件是否在Git仓库中（已提交）
Write-Host ""
Write-Host "[4/7] 检查文件是否在Git仓库中..." -ForegroundColor Yellow
$inRepo = git ls-files $FilePath 2>&1
if ($inRepo) {
    Write-Host "  ✓ 文件已在Git仓库中" -ForegroundColor Green
    Write-Host "    Git路径: $inRepo" -ForegroundColor Gray
} else {
    Write-Host "  ⚠ 文件未在Git仓库中，需要提交" -ForegroundColor Yellow
}

# 5. 检查是否有未提交的更改
Write-Host ""
Write-Host "[5/7] 检查是否有未提交的更改..." -ForegroundColor Yellow
$status = git status --porcelain $FilePath 2>&1
if ($status) {
    Write-Host "  ⚠ 有未提交的更改:" -ForegroundColor Yellow
    Write-Host "    $status" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  提示: 需要执行 git commit" -ForegroundColor Yellow
} else {
    Write-Host "  ✓ 没有未提交的更改" -ForegroundColor Green
}

# 6. 检查远程仓库状态
Write-Host ""
Write-Host "[6/7] 检查远程仓库状态..." -ForegroundColor Yellow
$remoteUrl = git remote get-url origin 2>&1
if ($remoteUrl) {
    Write-Host "  ✓ 远程仓库: $remoteUrl" -ForegroundColor Green
    
    # 获取当前分支
    $currentBranch = git rev-parse --abbrev-ref HEAD
    Write-Host "  当前分支: $currentBranch" -ForegroundColor Gray
    
    # 检查是否有未推送的提交
    $unpushed = git log origin/$currentBranch..HEAD --oneline 2>&1
    if ($unpushed) {
        Write-Host "  ⚠ 有未推送的提交:" -ForegroundColor Yellow
        $unpushed | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        Write-Host ""
        Write-Host "  提示: 需要执行 git push origin $currentBranch" -ForegroundColor Yellow
    } else {
        Write-Host "  ✓ 所有提交已推送" -ForegroundColor Green
    }
} else {
    Write-Host "  ✗ 未找到远程仓库" -ForegroundColor Red
}

# 7. 验证远程仓库中是否有该文件
Write-Host ""
Write-Host "[7/7] 验证远程仓库中是否有该文件..." -ForegroundColor Yellow
$currentBranch = git rev-parse --abbrev-ref HEAD
$remoteFile = git ls-tree -r origin/$currentBranch --name-only | Select-String -Pattern ([regex]::Escape($FilePath.Replace('\', '/')))
if ($remoteFile) {
    Write-Host "  ✓ 文件已在远程仓库中" -ForegroundColor Green
    Write-Host "    远程路径: $remoteFile" -ForegroundColor Gray
} else {
    Write-Host "  ⚠ 文件不在远程仓库中" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  可能的原因:" -ForegroundColor Yellow
    Write-Host "    1. 文件未提交 (需要 git commit)" -ForegroundColor Gray
    Write-Host "    2. 提交未推送 (需要 git push)" -ForegroundColor Gray
    Write-Host "    3. 文件被.gitignore忽略" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "验证完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "如果文件未推送，执行以下命令:" -ForegroundColor Yellow
Write-Host "  git add $FilePath" -ForegroundColor White
Write-Host "  git commit -m 'Add $FilePath'" -ForegroundColor White
Write-Host "  git push origin $currentBranch" -ForegroundColor White
