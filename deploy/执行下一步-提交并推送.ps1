# 执行下一步：提交并推送行尾符修复

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  执行下一步：提交并推送行尾符修复" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤 1: 添加文件
Write-Host "[步骤 1] 添加修复的文件到 Git..." -ForegroundColor Yellow
git add .gitattributes deploy/推送到GitHub并部署.ps1 deploy/从GitHub拉取并部署.sh docs/开发笔记/行尾符问题修复说明.md docs/开发笔记/下一步行动计划-部署流程验证.md

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 文件已添加到暂存区" -ForegroundColor Green
} else {
    Write-Host "  ✗ 添加文件失败" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 步骤 2: 提交
Write-Host "[步骤 2] 提交修复..." -ForegroundColor Yellow
git commit -m "修复 Windows/Linux 行尾符兼容性问题，确保脚本在服务器上正常执行"

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 提交成功" -ForegroundColor Green
    
    # 显示最新提交
    $lastCommit = git log -1 --oneline
    Write-Host "  最新提交: $lastCommit" -ForegroundColor Gray
} else {
    Write-Host "  ✗ 提交失败（可能没有需要提交的更改）" -ForegroundColor Yellow
    
    # 检查是否有未提交的更改
    $status = git status --short
    if ($status) {
        Write-Host "  仍有未提交的更改，请检查" -ForegroundColor Yellow
        exit 1
    } else {
        Write-Host "  所有更改已提交" -ForegroundColor Green
    }
}
Write-Host ""

# 步骤 3: 推送
Write-Host "[步骤 3] 推送到 GitHub..." -ForegroundColor Yellow
git push origin master

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 推送成功" -ForegroundColor Green
    
    # 显示远程仓库信息
    $remoteUrl = git remote get-url origin 2>&1
    if ($remoteUrl -and $remoteUrl -notmatch "fatal") {
        Write-Host "  远程仓库: $remoteUrl" -ForegroundColor Gray
    }
} else {
    Write-Host "  ✗ 推送失败" -ForegroundColor Red
    Write-Host "  请检查网络连接和权限" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  完成！下一步：测试部署流程" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "现在可以执行:" -ForegroundColor Yellow
Write-Host "  .\deploy\推送到GitHub并部署.ps1 -CommitMessage '测试行尾符修复'" -ForegroundColor White
Write-Host ""
