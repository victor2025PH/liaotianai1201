# 检查本地项目目录结构
# 使用方法：在 PowerShell 中运行此脚本

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🔍 检查本地项目目录结构" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$BasePath = "D:\telegram-ai-system"

if (-not (Test-Path $BasePath)) {
    Write-Host "❌ 项目根目录不存在: $BasePath" -ForegroundColor Red
    exit 1
}

Write-Host "项目根目录: $BasePath" -ForegroundColor Green
Write-Host ""

# 检查三个项目目录
$Projects = @(
    @{
        Name = "tgmini"
        Dir = "tgmini20251220"
    },
    @{
        Name = "hongbao"
        Dir = "hbwy20251220"
    },
    @{
        Name = "aizkw"
        Dir = "aizkw20251219"
    }
)

$AllValid = $true

foreach ($project in $Projects) {
    $ProjectPath = Join-Path $BasePath $project.Dir
    
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "📁 检查项目: $($project.Name)" -ForegroundColor Cyan
    Write-Host "目录: $ProjectPath" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
    if (-not (Test-Path $ProjectPath)) {
        Write-Host "❌ 目录不存在" -ForegroundColor Red
        $AllValid = $false
        Write-Host ""
        continue
    }
    
    Write-Host "✅ 目录存在" -ForegroundColor Green
    Write-Host ""
    
    # 检查 package.json
    $PackageJson = Join-Path $ProjectPath "package.json"
    if (Test-Path $PackageJson) {
        Write-Host "✅ package.json 存在" -ForegroundColor Green
        $packageContent = Get-Content $PackageJson -Raw | ConvertFrom-Json
        Write-Host "   项目名称: $($packageContent.name)" -ForegroundColor Gray
        Write-Host "   版本: $($packageContent.version)" -ForegroundColor Gray
    } else {
        Write-Host "❌ package.json 不存在" -ForegroundColor Red
        $AllValid = $false
    }
    Write-Host ""
    
    # 检查关键文件
    $KeyFiles = @("vite.config.ts", "vite.config.js", "tsconfig.json", "index.html", "App.tsx")
    Write-Host "检查关键文件:" -ForegroundColor Yellow
    foreach ($file in $KeyFiles) {
        $FilePath = Join-Path $ProjectPath $file
        if (Test-Path $FilePath) {
            Write-Host "  ✅ $file" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  $file 不存在" -ForegroundColor Yellow
        }
    }
    Write-Host ""
    
    # 检查 components 目录
    $ComponentsPath = Join-Path $ProjectPath "components"
    if (Test-Path $ComponentsPath) {
        Write-Host "✅ components 目录存在" -ForegroundColor Green
        $componentFiles = Get-ChildItem -Path $ComponentsPath -Filter "*.tsx" -File
        Write-Host "   TSX 文件数量: $($componentFiles.Count)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  components 目录不存在" -ForegroundColor Yellow
    }
    Write-Host ""
    
    # 检查是否有嵌套的目录结构（不应该有）
    $SubDirs = Get-ChildItem -Path $ProjectPath -Directory | Where-Object { 
        $_.Name -notin @("components", "contexts", "src", "hooks", "node_modules", "dist", ".git")
    }
    if ($SubDirs.Count -gt 0) {
        Write-Host "⚠️  发现意外的子目录（可能结构不正确）:" -ForegroundColor Yellow
        foreach ($subDir in $SubDirs) {
            Write-Host "   - $($subDir.Name)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "✅ 目录结构正常（没有意外的嵌套）" -ForegroundColor Green
    }
    Write-Host ""
    
    # 列出目录内容（前 15 项）
    Write-Host "目录内容（前 15 项）:" -ForegroundColor Yellow
    Get-ChildItem -Path $ProjectPath | Select-Object -First 15 | ForEach-Object {
        $icon = if ($_.PSIsContainer) { "📁" } else { "📄" }
        Write-Host "   $icon $($_.Name)" -ForegroundColor Gray
    }
    Write-Host ""
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "📊 检查结果汇总" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

if ($AllValid) {
    Write-Host "✅ 所有项目的目录结构都正确！" -ForegroundColor Green
    Write-Host ""
    Write-Host "上传指南：" -ForegroundColor Yellow
    Write-Host "1. 使用 WinSCP 或 scp 上传整个项目目录" -ForegroundColor White
    Write-Host "2. 确保上传到服务器对应的子目录：" -ForegroundColor White
    Write-Host "   - tgmini20251220 → /home/ubuntu/telegram-ai-system/tgmini20251220/" -ForegroundColor Gray
    Write-Host "   - hbwy20251220 → /home/ubuntu/telegram-ai-system/hbwy20251220/" -ForegroundColor Gray
    Write-Host "   - aizkw20251219 → /home/ubuntu/telegram-ai-system/aizkw20251219/" -ForegroundColor Gray
    Write-Host "3. 上传时排除 node_modules 和 dist 目录" -ForegroundColor White
} else {
    Write-Host "❌ 部分项目的目录结构有问题" -ForegroundColor Red
    Write-Host "   请检查上述输出，确保每个项目都有 package.json" -ForegroundColor Yellow
}
