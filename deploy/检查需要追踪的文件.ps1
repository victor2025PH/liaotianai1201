# 检查哪些文件需要被 Git 追踪
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
