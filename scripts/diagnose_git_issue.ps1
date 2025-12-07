# Git问题诊断脚本
# 完整诊断从本地文件到服务器拉取的整个流程

param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Git 问题完整诊断" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$issues = @()

# 阶段1: 本地文件检查
Write-Host "【阶段 1】本地文件检查" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

if (Test-Path $FilePath) {
    Write-Host "  ✓ 文件存在" -ForegroundColor Green
    $fileInfo = Get-Item $FilePath
    Write-Host "    路径: $($fileInfo.FullName)" -ForegroundColor Gray
    Write-Host "    大小: $($fileInfo.Length) 字节" -ForegroundColor Gray
} else {
    Write-Host "  ✗ 文件不存在" -ForegroundColor Red
    $issues += "文件不存在: $FilePath"
    exit 1
}

# 阶段2: Git跟踪检查
Write-Host ""
Write-Host "【阶段 2】Git跟踪检查" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$gitIgnoreCheck = git check-ignore -v $FilePath 2>&1
if ($gitIgnoreCheck -match "\.gitignore") {
    Write-Host "  ✗ 文件被.gitignore忽略" -ForegroundColor Red
    Write-Host "    规则: $gitIgnoreCheck" -ForegroundColor Red
    $issues += "文件被.gitignore忽略: $gitIgnoreCheck"
    Write-Host ""
    Write-Host "  解决方案:" -ForegroundColor Yellow
    Write-Host "    git add -f $FilePath" -ForegroundColor White
} else {
    Write-Host "  ✓ 文件未被.gitignore忽略" -ForegroundColor Green
}

$inRepo = git ls-files $FilePath 2>&1
if ($inRepo) {
    Write-Host "  ✓ 文件在Git仓库中" -ForegroundColor Green
} else {
    Write-Host "  ✗ 文件不在Git仓库中" -ForegroundColor Red
    $issues += "文件未被Git跟踪"
    Write-Host ""
    Write-Host "  解决方案:" -ForegroundColor Yellow
    Write-Host "    git add $FilePath" -ForegroundColor White
    Write-Host "    或" -ForegroundColor Gray
    Write-Host "    git add -f $FilePath  (如果被忽略)" -ForegroundColor White
}

# 阶段3: 暂存区检查
Write-Host ""
Write-Host "【阶段 3】暂存区检查" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$staged = git diff --cached --name-only | Select-String -Pattern ([regex]::Escape($FilePath))
if ($staged) {
    Write-Host "  ✓ 文件在暂存区（已add，未commit）" -ForegroundColor Green
} else {
    Write-Host "  ℹ 文件不在暂存区" -ForegroundColor Gray
}

# 阶段4: 提交检查
Write-Host ""
Write-Host "【阶段 4】提交检查" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$status = git status --porcelain $FilePath 2>&1
if ($status) {
    Write-Host "  ⚠ 文件有未提交的更改" -ForegroundColor Yellow
    Write-Host "    状态: $status" -ForegroundColor Gray
    $issues += "文件有未提交的更改"
} else {
    Write-Host "  ✓ 文件已提交（或没有更改）" -ForegroundColor Green
}

# 检查最近的提交
$lastCommit = git log -1 --oneline --name-only -- $FilePath 2>&1
if ($lastCommit) {
    Write-Host "  最近提交:" -ForegroundColor Gray
    $lastCommit | Select-Object -First 1 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
} else {
    Write-Host "  ⚠ 文件从未被提交" -ForegroundColor Yellow
    $issues += "文件从未被提交"
}

# 阶段5: 远程仓库检查
Write-Host ""
Write-Host "【阶段 5】远程仓库检查" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$remoteUrl = git remote get-url origin 2>&1
if ($remoteUrl) {
    Write-Host "  ✓ 远程仓库已配置" -ForegroundColor Green
    Write-Host "    URL: $remoteUrl" -ForegroundColor Gray
} else {
    Write-Host "  ✗ 未配置远程仓库" -ForegroundColor Red
    $issues += "未配置远程仓库"
    exit 1
}

$currentBranch = git rev-parse --abbrev-ref HEAD
Write-Host "  当前分支: $currentBranch" -ForegroundColor Gray

# 检查远程分支
$remoteBranch = git ls-remote --heads origin $currentBranch 2>&1
if ($remoteBranch) {
    Write-Host "  ✓ 远程分支存在" -ForegroundColor Green
} else {
    Write-Host "  ⚠ 远程分支不存在，首次推送需要设置上游" -ForegroundColor Yellow
}

# 检查未推送的提交
Write-Host ""
Write-Host "  检查未推送的提交..." -ForegroundColor Gray
git fetch origin $currentBranch 2>&1 | Out-Null
$unpushed = git log origin/$currentBranch..HEAD --oneline --name-only -- $FilePath 2>&1
if ($unpushed) {
    Write-Host "  ⚠ 有包含此文件的未推送提交" -ForegroundColor Yellow
    $unpushed | Select-Object -First 3 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    $issues += "文件在未推送的提交中"
    Write-Host ""
    Write-Host "  解决方案:" -ForegroundColor Yellow
    Write-Host "    git push origin $currentBranch" -ForegroundColor White
} else {
    Write-Host "  ✓ 所有包含此文件的提交都已推送" -ForegroundColor Green
}

# 阶段6: 远程文件验证
Write-Host ""
Write-Host "【阶段 6】远程文件验证" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

try {
    $remoteFile = git ls-tree -r origin/$currentBranch --name-only 2>&1 | Select-String -Pattern ([regex]::Escape($FilePath.Replace('\', '/')))
    if ($remoteFile) {
        Write-Host "  ✓ 文件在远程仓库中" -ForegroundColor Green
        Write-Host "    远程路径: $remoteFile" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ 文件不在远程仓库中" -ForegroundColor Red
        $issues += "文件不在远程仓库中"
        Write-Host ""
        Write-Host "  可能的原因:" -ForegroundColor Yellow
        Write-Host "    1. 文件未提交" -ForegroundColor Gray
        Write-Host "    2. 提交未推送" -ForegroundColor Gray
        Write-Host "    3. 文件在不同分支" -ForegroundColor Gray
        Write-Host "    4. 文件被.gitignore忽略" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ⚠ 无法验证远程文件（可能需要先fetch）" -ForegroundColor Yellow
}

# 阶段7: 服务器端检查建议
Write-Host ""
Write-Host "【阶段 7】服务器端检查建议" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host "  在服务器上执行以下命令:" -ForegroundColor Gray
Write-Host ""
Write-Host "  # 1. 进入项目目录" -ForegroundColor White
Write-Host "  cd ~/liaotian" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # 2. 检查当前分支" -ForegroundColor White
Write-Host "  git branch" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # 3. 拉取最新代码" -ForegroundColor White
Write-Host "  git fetch origin $currentBranch" -ForegroundColor Cyan
Write-Host "  git pull origin $currentBranch" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # 4. 验证文件存在" -ForegroundColor White
Write-Host "  ls -la $($FilePath.Replace('\', '/'))" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # 5. 检查文件在Git中" -ForegroundColor White
Write-Host "  git ls-files $($FilePath.Replace('\', '/'))" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # 6. 添加执行权限并运行" -ForegroundColor White
Write-Host "  chmod +x $($FilePath.Replace('\', '/'))" -ForegroundColor Cyan
Write-Host "  bash $($FilePath.Replace('\', '/'))" -ForegroundColor Cyan

# 总结
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "诊断总结" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($issues.Count -eq 0) {
    Write-Host "  ✓ 未发现问题！文件应该可以正常推送到服务器。" -ForegroundColor Green
} else {
    Write-Host "  发现 $($issues.Count) 个问题:" -ForegroundColor Red
    $issues | ForEach-Object { Write-Host "    - $_" -ForegroundColor Red }
    Write-Host ""
    Write-Host "  推荐操作:" -ForegroundColor Yellow
    Write-Host "    1. 运行: .\scripts\complete_push_workflow.ps1 -FilePath `"$FilePath`"" -ForegroundColor White
    Write-Host "    2. 或手动执行修复步骤" -ForegroundColor White
}

Write-Host ""
