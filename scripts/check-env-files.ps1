# ============================================================
# 检查包含 API Key 的文件
# ============================================================
# 功能：列出所有包含 API Key 的文件（本地和 Git 中）
# 使用方法：.\scripts\check-env-files.ps1
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🔍 检查包含 API Key 的文件" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 设置工作目录
$RepoRoot = (Get-Location).Path
if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
    Write-Host "❌ 错误：当前目录不是 Git 仓库" -ForegroundColor Red
    exit 1
}

Set-Location $RepoRoot

# 1. 检查本地 .env 文件
Write-Host "1. 本地 .env 文件（需要手动上传）" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$LocalEnvFiles = @(
    ".env",
    "admin-backend\.env",
    "hbwy20251220\.env.local",
    "tgmini20251220\.env.local"
)

$FoundLocalFiles = @()
foreach ($File in $LocalEnvFiles) {
    $FullPath = Join-Path $RepoRoot $File
    if (Test-Path $FullPath) {
        Write-Host "  ✅ $File" -ForegroundColor Green
        $FoundLocalFiles += $File
    } else {
        Write-Host "  ❌ $File (不存在)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "找到 $($FoundLocalFiles.Count) 个本地 .env 文件" -ForegroundColor Cyan
Write-Host ""

# 2. 检查 Git 中是否跟踪了 .env 文件
Write-Host "2. Git 跟踪的 .env 文件（不应该有）" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

try {
    $TrackedEnvFiles = git ls-files | Where-Object { $_ -match "\.env$|\.env\.local$" }
    
    if ($TrackedEnvFiles.Count -eq 0) {
        Write-Host "  ✅ 没有 .env 文件被 Git 跟踪" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: The following .env files are tracked by Git (need to remove):" -ForegroundColor Red
        foreach ($File in $TrackedEnvFiles) {
            Write-Host "    - $File" -ForegroundColor Yellow
        }
        Write-Host ""
        Write-Host "  Remove commands:" -ForegroundColor Cyan
        foreach ($File in $TrackedEnvFiles) {
            Write-Host "    git rm --cached $File" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "  ❌ 无法检查 Git 跟踪的文件: $_" -ForegroundColor Red
}

Write-Host ""

# 3. 检查 .gitignore 配置
Write-Host "3. .gitignore 配置" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

if (Test-Path ".gitignore") {
    $GitIgnoreContent = Get-Content ".gitignore" -Raw
    $EnvPatterns = @(".env", ".env.local", ".env.*.local")
    
    $AllIgnored = $true
    foreach ($Pattern in $EnvPatterns) {
        if ($GitIgnoreContent -match [regex]::Escape($Pattern)) {
            Write-Host "  ✅ $Pattern 已在 .gitignore 中" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $Pattern 未在 .gitignore 中" -ForegroundColor Red
            $AllIgnored = $false
        }
    }
    
    if ($AllIgnored) {
        Write-Host ""
        Write-Host "  ✅ .gitignore 配置正确" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "  ⚠️  .gitignore 需要更新" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ .gitignore 文件不存在" -ForegroundColor Red
}

Write-Host ""

# 4. 总结
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📋 文件清单（需要手动上传到服务器）" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if ($FoundLocalFiles.Count -gt 0) {
    Write-Host "以下文件包含 API Key，需要手动上传：" -ForegroundColor Yellow
    foreach ($File in $FoundLocalFiles) {
        Write-Host "  - $File" -ForegroundColor Cyan
    }
    Write-Host ""
    Write-Host "上传命令：" -ForegroundColor Yellow
    Write-Host "  .\scripts\upload-env-files.ps1 -ServerUser ubuntu -ServerHost 165.154.242.60" -ForegroundColor Gray
} else {
    Write-Host "⚠️  未找到本地 .env 文件" -ForegroundColor Yellow
    Write-Host "   如果文件不存在，需要在服务器上创建" -ForegroundColor Gray
}

Write-Host ""
