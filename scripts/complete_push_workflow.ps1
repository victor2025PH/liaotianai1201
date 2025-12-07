# 完整的Git推送工作流
# 确保文件正确添加到Git、提交并推送到GitHub

param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath,
    
    [Parameter(Mandatory=$false)]
    [string]$CommitMessage = ""
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Git 完整推送工作流" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

try {
    # 1. 验证文件存在
    Write-Host "[步骤 1/5] 验证文件存在..." -ForegroundColor Yellow
    if (-not (Test-Path $FilePath)) {
        throw "文件不存在: $FilePath"
    }
    Write-Host "  ✓ 文件存在" -ForegroundColor Green
    
    # 2. 检查.gitignore
    Write-Host ""
    Write-Host "[步骤 2/5] 检查.gitignore..." -ForegroundColor Yellow
    $gitIgnoreCheck = git check-ignore -v $FilePath 2>&1
    if ($gitIgnoreCheck -match "\.gitignore") {
        Write-Host "  ⚠ 文件被.gitignore忽略，使用 -f 强制添加" -ForegroundColor Yellow
        git add -f $FilePath
    } else {
        git add $FilePath
    }
    Write-Host "  ✓ 文件已添加到暂存区" -ForegroundColor Green
    
    # 3. 检查是否有更改
    Write-Host ""
    Write-Host "[步骤 3/5] 检查更改..." -ForegroundColor Yellow
    $status = git status --porcelain $FilePath
    if (-not $status) {
        Write-Host "  ⚠ 文件没有更改，可能已提交" -ForegroundColor Yellow
        $alreadyCommitted = $true
    } else {
        Write-Host "  ✓ 检测到更改" -ForegroundColor Green
        $alreadyCommitted = $false
    }
    
    # 4. 提交（如果需要）
    if (-not $alreadyCommitted) {
        Write-Host ""
        Write-Host "[步骤 4/5] 提交更改..." -ForegroundColor Yellow
        if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
            $fileName = Split-Path -Leaf $FilePath
            $CommitMessage = "Add/Update $fileName"
        }
        git commit -m $CommitMessage
        if ($LASTEXITCODE -ne 0) {
            throw "提交失败"
        }
        Write-Host "  ✓ 提交成功: $CommitMessage" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[步骤 4/5] 跳过提交（无更改）" -ForegroundColor Yellow
    }
    
    # 5. 推送到远程
    Write-Host ""
    Write-Host "[步骤 5/5] 推送到GitHub..." -ForegroundColor Yellow
    $currentBranch = git rev-parse --abbrev-ref HEAD
    Write-Host "  目标分支: $currentBranch" -ForegroundColor Gray
    
    git push origin $currentBranch
    if ($LASTEXITCODE -ne 0) {
        throw "推送失败"
    }
    Write-Host "  ✓ 推送成功" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ 所有步骤完成！文件已推送到GitHub" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "文件路径: $FilePath" -ForegroundColor Gray
    Write-Host "远程仓库: $(git remote get-url origin)" -ForegroundColor Gray
    Write-Host "分支: $currentBranch" -ForegroundColor Gray
    
} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ 错误: $_" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}
