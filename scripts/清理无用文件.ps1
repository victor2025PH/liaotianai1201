# 清理無用文件腳本
# 將舊文件移動到歸檔目錄，而不是刪除

param(
    [switch]$DryRun = $false,
    [switch]$Archive = $true
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "清理無用文件" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "⚠️  乾跑模式 - 不會實際移動或刪除文件" -ForegroundColor Yellow
    Write-Host ""
}

# 創建歸檔目錄
$ArchiveDir = Join-Path $ProjectRoot "archive"
$ArchiveScripts = Join-Path $ArchiveDir "old-scripts"
$ArchiveReports = Join-Path $ArchiveDir "old-reports"
$ArchiveDocs = Join-Path $ArchiveDir "old-docs"

if ($Archive -and -not $DryRun) {
    New-Item -ItemType Directory -Force -Path $ArchiveScripts | Out-Null
    New-Item -ItemType Directory -Force -Path $ArchiveReports | Out-Null
    New-Item -ItemType Directory -Force -Path $ArchiveDocs | Out-Null
    Write-Host "✅ 歸檔目錄已創建" -ForegroundColor Green
}

# 定義要清理的文件模式
$Patterns = @(
    # 項目根目錄的臨時腳本
    @{
        Pattern = "修复*.sh"
        Category = "scripts"
        Description = "臨時修復腳本 (sh)"
    },
    @{
        Pattern = "修复*.md"
        Category = "reports"
        Description = "修復報告 (md)"
    },
    @{
        Pattern = "修复*.bat"
        Category = "scripts"
        Description = "臨時修復腳本 (bat)"
    },
    @{
        Pattern = "修复*.ps1"
        Category = "scripts"
        Description = "臨時修復腳本 (ps1)"
    },
    @{
        Pattern = "全自动*.ps1"
        Category = "scripts"
        Description = "全自動腳本"
    },
    @{
        Pattern = "全自动*.sh"
        Category = "scripts"
        Description = "全自動腳本 (sh)"
    },
    @{
        Pattern = "最终*.ps1"
        Category = "scripts"
        Description = "最終版本腳本"
    },
    @{
        Pattern = "最终*.md"
        Category = "reports"
        Description = "最終報告"
    },
    @{
        Pattern = "持续*.ps1"
        Category = "scripts"
        Description = "持續監控腳本"
    },
    @{
        Pattern = "自动*.ps1"
        Category = "scripts"
        Description = "自動化腳本"
    },
    @{
        Pattern = "一键*.bat"
        Category = "scripts"
        Description = "一鍵修復腳本"
    },
    @{
        Pattern = "一键*.sh"
        Category = "scripts"
        Description = "一鍵修復腳本 (sh)"
    },
    @{
        Pattern = "启动*.ps1"
        Category = "scripts"
        Description = "啟動腳本"
    },
    @{
        Pattern = "启动*.txt"
        Category = "docs"
        Description = "啟動說明"
    },
    @{
        Pattern = "检查*.ps1"
        Category = "scripts"
        Description = "檢查腳本"
    },
    @{
        Pattern = "查看*.ps1"
        Category = "scripts"
        Description = "查看腳本"
    },
    @{
        Pattern = "执行*.md"
        Category = "reports"
        Description = "執行報告"
    },
    @{
        Pattern = "执行*.txt"
        Category = "docs"
        Description = "執行說明"
    },
    @{
        Pattern = "诊断*.sh"
        Category = "scripts"
        Description = "診斷腳本"
    },
    @{
        Pattern = "监控*.ps1"
        Category = "scripts"
        Description = "監控腳本"
    },
    @{
        Pattern = "本地*.py"
        Category = "scripts"
        Description = "本地腳本"
    }
)

$TotalFiles = 0
$MovedFiles = 0

Write-Host "開始掃描文件..." -ForegroundColor Yellow
Write-Host ""

foreach ($PatternInfo in $Patterns) {
    $Pattern = $PatternInfo.Pattern
    $Category = $PatternInfo.Category
    $Description = $PatternInfo.Description
    
    $Files = Get-ChildItem -Path $ProjectRoot -Filter $Pattern -File -ErrorAction SilentlyContinue
    
    if ($Files) {
        Write-Host "發現 $($Files.Count) 個文件: $Description ($Pattern)" -ForegroundColor Cyan
        
        foreach ($File in $Files) {
            $TotalFiles++
            $RelativePath = $File.FullName.Replace($ProjectRoot + "\", "")
            
            if ($DryRun) {
                Write-Host "  [乾跑] 將移動: $RelativePath" -ForegroundColor Gray
            } else {
                if ($Archive) {
                    # 移動到歸檔目錄
                    switch ($Category) {
                        "scripts" { $DestDir = $ArchiveScripts }
                        "reports" { $DestDir = $ArchiveReports }
                        "docs" { $DestDir = $ArchiveDocs }
                        default { $DestDir = $ArchiveDir }
                    }
                    
                    try {
                        Move-Item -Path $File.FullName -Destination $DestDir -Force -ErrorAction Stop
                        Write-Host "  ✅ 已歸檔: $RelativePath" -ForegroundColor Green
                        $MovedFiles++
                    } catch {
                        Write-Host "  ❌ 移動失敗: $RelativePath - $_" -ForegroundColor Red
                    }
                }
            }
        }
        Write-Host ""
    }
}

Write-Host "========================================" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "乾跑完成" -ForegroundColor Yellow
    Write-Host "發現 $TotalFiles 個文件需要處理" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "執行以下命令實際移動文件：" -ForegroundColor Yellow
    Write-Host "  .\scripts\清理无用文件.ps1" -ForegroundColor Cyan
} else {
    Write-Host "清理完成" -ForegroundColor Green
    Write-Host "處理了 $TotalFiles 個文件，成功移動 $MovedFiles 個" -ForegroundColor Green
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
