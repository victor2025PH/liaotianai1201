# ============================================================
# 将三个网站项目添加到主仓库
# ============================================================
# 功能：处理子模块或独立 Git 仓库，将它们的内容添加到主仓库
# 使用方法：.\scripts\add-three-sites-to-main-repo.ps1
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📦 将三个网站项目添加到主仓库" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$RepoRoot = (Get-Location).Path
if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
    Write-Host "❌ 错误：当前目录不是 Git 仓库" -ForegroundColor Red
    exit 1
}

Set-Location $RepoRoot

$Sites = @(
    "hbwy20251220",
    "tgmini20251220",
    "aizkw20251219"
)

foreach ($Site in $Sites) {
    $SitePath = Join-Path $RepoRoot $Site
    
    Write-Host "处理: $Site" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    
    if (-not (Test-Path $SitePath)) {
        Write-Host "  ❌ 目录不存在: $SitePath" -ForegroundColor Red
        continue
    }
    
    Write-Host "  ✅ 目录存在" -ForegroundColor Green
    
    # 检查是否是独立的 Git 仓库
    $GitPath = Join-Path $SitePath ".git"
    if (Test-Path $GitPath) {
        Write-Host "  ⚠️  检测到独立的 Git 仓库" -ForegroundColor Yellow
        Write-Host "  正在移除 .git 目录..." -ForegroundColor Gray
        
        # 备份 .git 目录（可选）
        $BackupPath = Join-Path $SitePath ".git.backup"
        if (Test-Path $BackupPath) {
            Remove-Item -Recurse -Force $BackupPath
        }
        Move-Item $GitPath $BackupPath -Force
        
        Write-Host "  ✅ .git 目录已移除（备份到 .git.backup）" -ForegroundColor Green
    }
    
    # 检查 .gitignore
    $GitIgnorePath = Join-Path $SitePath ".gitignore"
    if (Test-Path $GitIgnorePath) {
        $GitIgnoreContent = Get-Content $GitIgnorePath -Raw
        if ($GitIgnoreContent -notmatch "\.env") {
            Write-Host "  ⚠️  .gitignore 未包含 .env，正在添加..." -ForegroundColor Yellow
            Add-Content $GitIgnorePath "`n# Environment variables`n.env`n.env.local`n.env.*.local"
            Write-Host "  ✅ .gitignore 已更新" -ForegroundColor Green
        } else {
            Write-Host "  ✅ .gitignore 已包含 .env" -ForegroundColor Green
        }
    } else {
        Write-Host "  ⚠️  .gitignore 不存在，正在创建..." -ForegroundColor Yellow
        @"
# Environment variables
.env
.env.local
.env.*.local

# Dependencies
node_modules/
dist/

# Build outputs
*.log
"@ | Out-File -FilePath $GitIgnorePath -Encoding UTF8
        Write-Host "  ✅ .gitignore 已创建" -ForegroundColor Green
    }
    
    # 检查是否有 .env.local 文件
    $EnvLocalPath = Join-Path $SitePath ".env.local"
    if (Test-Path $EnvLocalPath) {
        Write-Host "  ⚠️  发现 .env.local 文件（需要手动上传到服务器）" -ForegroundColor Yellow
        
        # 检查是否被 Git 跟踪
        $Tracked = git ls-files --error-unmatch "$Site/.env.local" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ❌ .env.local 被 Git 跟踪，正在移除..." -ForegroundColor Red
            git rm --cached "$Site/.env.local" 2>$null
            Write-Host "  ✅ .env.local 已从 Git 跟踪中移除" -ForegroundColor Green
        } else {
            Write-Host "  ✅ .env.local 未被 Git 跟踪" -ForegroundColor Green
        }
    }
    
    Write-Host ""
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📤 添加文件到 Git" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 添加所有文件
foreach ($Site in $Sites) {
    Write-Host "添加: $Site" -ForegroundColor Yellow
    git add -f "$Site/" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ 已添加" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  添加时出现问题（可能已存在）" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📋 检查状态" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

git status --short | Select-String -Pattern "hbwy|tgmini|aizkw" | ForEach-Object {
    Write-Host "  $_" -ForegroundColor Gray
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ 准备完成" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "  1. 检查上面的状态" -ForegroundColor Gray
Write-Host "  2. 提交更改: git commit -m 'feat: 添加三个网站项目到主仓库'" -ForegroundColor Gray
Write-Host "  3. 推送到 GitHub: git push origin main" -ForegroundColor Gray
Write-Host ""
