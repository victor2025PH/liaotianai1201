# 上傳項目到新 GitHub 倉庫
# 目標倉庫: https://github.com/victor2025PH/liaotianai1201.git

param(
    [string]$RemoteUrl = "https://github.com/victor2025PH/liaotianai1201.git",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "上傳項目到新 GitHub 倉庫" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "目標倉庫: $RemoteUrl" -ForegroundColor Yellow
Write-Host ""

# 步驟 1: 檢查 Git 倉庫
Write-Host "步驟 1: 檢查 Git 倉庫..." -ForegroundColor Yellow
if (-not (Test-Path .git)) {
    Write-Host "❌ 當前目錄不是 Git 倉庫" -ForegroundColor Red
    Write-Host "   正在初始化 Git 倉庫..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Git 倉庫已初始化" -ForegroundColor Green
} else {
    Write-Host "✅ Git 倉庫已存在" -ForegroundColor Green
}
Write-Host ""

# 步驟 2: 檢查 .gitignore
Write-Host "步驟 2: 檢查 .gitignore 配置..." -ForegroundColor Yellow
if (Test-Path .gitignore) {
    Write-Host "✅ .gitignore 文件存在" -ForegroundColor Green
    $hasNodeModules = Select-String -Path .gitignore -Pattern "node_modules" -Quiet
    $hasVenv = Select-String -Path .gitignore -Pattern "\.venv" -Quiet
    if ($hasNodeModules -and $hasVenv) {
        Write-Host "✅ 大文件目錄已正確配置為忽略" -ForegroundColor Green
    } else {
        Write-Host "⚠️  警告: .gitignore 可能缺少某些配置" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ .gitignore 文件不存在，將使用默認配置" -ForegroundColor Yellow
}
Write-Host ""

# 步驟 3: 檢查待提交的文件
Write-Host "步驟 3: 檢查待提交的文件..." -ForegroundColor Yellow
$statusOutput = git status --porcelain
if ($statusOutput) {
    Write-Host "發現以下變更：" -ForegroundColor Yellow
    Write-Host $statusOutput -ForegroundColor Gray
    Write-Host ""
    Write-Host "正在添加所有文件..." -ForegroundColor Yellow
    git add .
    Write-Host "✅ 文件已添加到暫存區" -ForegroundColor Green
} else {
    Write-Host "✅ 沒有待提交的文件變更" -ForegroundColor Green
}
Write-Host ""

# 步驟 4: 檢查是否有提交
Write-Host "步驟 4: 檢查提交歷史..." -ForegroundColor Yellow
$commitCount = (git log --oneline 2>&1 | Measure-Object -Line).Lines
if ($commitCount -eq 0) {
    Write-Host "⚠️  尚未有任何提交，將創建初始提交..." -ForegroundColor Yellow
    $commitMessage = "Initial commit: 上傳項目到新倉庫"
} else {
    Write-Host "✅ 發現 $commitCount 個提交" -ForegroundColor Green
    Write-Host "是否創建一個新的提交以包含所有當前變更？(Y/N): " -NoNewline -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "Y" -or $response -eq "y") {
        $commitMessage = "chore: 準備上傳到新倉庫"
    } else {
        $commitMessage = $null
    }
}

if ($commitMessage) {
    Write-Host "創建提交..." -ForegroundColor Yellow
    git commit -m $commitMessage
    Write-Host "✅ 提交已創建" -ForegroundColor Green
}
Write-Host ""

# 步驟 5: 檢查或設置分支
Write-Host "步驟 5: 檢查分支..." -ForegroundColor Yellow
$currentBranch = git branch --show-current
if (-not $currentBranch) {
    Write-Host "沒有當前分支，檢查默認分支名稱..." -ForegroundColor Yellow
    $hasMain = git branch -a | Select-String -Pattern "main" -Quiet
    $hasMaster = git branch -a | Select-String -Pattern "master" -Quiet
    
    if ($hasMain) {
        $Branch = "main"
    } elseif ($hasMaster) {
        $Branch = "master"
    } else {
        Write-Host "創建 $Branch 分支..." -ForegroundColor Yellow
        git checkout -b $Branch
    }
} else {
    $Branch = $currentBranch
    Write-Host "✅ 當前分支: $Branch" -ForegroundColor Green
}
Write-Host ""

# 步驟 6: 設置遠程倉庫
Write-Host "步驟 6: 設置遠程倉庫..." -ForegroundColor Yellow
$remoteExists = git remote | Select-String -Pattern "^origin$" -Quiet

if ($remoteExists) {
    $currentRemote = git remote get-url origin
    Write-Host "當前遠程倉庫: $currentRemote" -ForegroundColor Gray
    Write-Host "是否更新為新倉庫地址？(Y/N): " -NoNewline -ForegroundColor Yellow
    $updateRemote = Read-Host
    if ($updateRemote -eq "Y" -or $updateRemote -eq "y") {
        git remote set-url origin $RemoteUrl
        Write-Host "✅ 遠程倉庫已更新" -ForegroundColor Green
    } else {
        Write-Host "保持原有遠程倉庫地址" -ForegroundColor Yellow
        $RemoteUrl = $currentRemote
    }
} else {
    Write-Host "添加新的遠程倉庫..." -ForegroundColor Yellow
    git remote add origin $RemoteUrl
    Write-Host "✅ 遠程倉庫已添加" -ForegroundColor Green
}
Write-Host ""

# 步驟 7: 驗證遠程倉庫連接
Write-Host "步驟 7: 驗證遠程倉庫連接..." -ForegroundColor Yellow
try {
    git ls-remote --heads origin $Branch 2>&1 | Out-Null
    Write-Host "✅ 遠程倉庫連接正常" -ForegroundColor Green
} catch {
    Write-Host "⚠️  無法連接到遠程倉庫（可能是新倉庫或網絡問題）" -ForegroundColor Yellow
}
Write-Host ""

# 步驟 8: 推送到遠程倉庫
Write-Host "步驟 8: 推送到遠程倉庫..." -ForegroundColor Yellow
Write-Host "目標分支: $Branch" -ForegroundColor Gray
Write-Host "是否繼續推送？(Y/N): " -NoNewline -ForegroundColor Yellow
$confirmPush = Read-Host

if ($confirmPush -eq "Y" -or $confirmPush -eq "y") {
    Write-Host "正在推送..." -ForegroundColor Yellow
    
    # 檢查遠程分支是否存在
    $remoteBranchExists = git ls-remote --heads origin $Branch 2>&1 | Select-String -Pattern $Branch -Quiet
    
    if ($remoteBranchExists) {
        Write-Host "遠程分支已存在，使用標準推送..." -ForegroundColor Gray
        git push -u origin $Branch
    } else {
        Write-Host "遠程分支不存在，創建新分支..." -ForegroundColor Gray
        git push -u origin $Branch
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "✅ 上傳成功！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "倉庫地址: $RemoteUrl" -ForegroundColor Cyan
        Write-Host "分支: $Branch" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "下一步：" -ForegroundColor Yellow
        Write-Host "  1. 訪問倉庫頁面查看上傳的文件" -ForegroundColor White
        Write-Host "  2. 檢查 GitHub Actions（如果有）" -ForegroundColor White
        Write-Host "  3. 設置倉庫描述和 README" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "❌ 推送失敗" -ForegroundColor Red
        Write-Host "可能的原因：" -ForegroundColor Yellow
        Write-Host "  - 網絡連接問題" -ForegroundColor White
        Write-Host "  - 認證問題（需要配置 GitHub 憑據）" -ForegroundColor White
        Write-Host "  - 遠程倉庫權限問題" -ForegroundColor White
        Write-Host ""
        Write-Host "解決方法：" -ForegroundColor Yellow
        Write-Host "  1. 檢查網絡連接" -ForegroundColor White
        Write-Host "  2. 配置 GitHub 認證（使用 Personal Access Token）" -ForegroundColor White
        Write-Host "  3. 確認倉庫權限" -ForegroundColor White
        exit 1
    }
} else {
    Write-Host "已取消推送" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "手動推送命令：" -ForegroundColor Yellow
    Write-Host "  git push -u origin $Branch" -ForegroundColor Cyan
}

Write-Host ""
