# ============================================================
# 上传包含 API Key 的文件到服务器
# ============================================================
# 功能：使用 SCP 上传 .env 文件到服务器
# 使用方法：.\scripts\upload-env-files.ps1
# ============================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerUser = "ubuntu",
    
    [Parameter(Mandatory=$true)]
    [string]$ServerHost = "165.154.242.60",
    
    [Parameter(Mandatory=$false)]
    [string]$ServerPath = "/home/ubuntu/telegram-ai-system"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📤 上传包含 API Key 的文件到服务器" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "服务器: $ServerUser@$ServerHost" -ForegroundColor Yellow
Write-Host "目标路径: $ServerPath" -ForegroundColor Yellow
Write-Host ""

# 设置工作目录
$RepoRoot = (Get-Location).Path
if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
    Write-Host "❌ 错误：当前目录不是 Git 仓库" -ForegroundColor Red
    exit 1
}

Set-Location $RepoRoot

# 定义要上传的文件列表
$FilesToUpload = @(
    @{
        LocalPath = ".env"
        RemotePath = "$ServerPath/.env"
        Description = "项目根目录环境变量文件"
    },
    @{
        LocalPath = "admin-backend\.env"
        RemotePath = "$ServerPath/admin-backend/.env"
        Description = "后端环境变量文件"
    },
    @{
        LocalPath = "hbwy20251220\.env.local"
        RemotePath = "$ServerPath/hbwy20251220/.env.local"
        Description = "前端项目 1 环境变量文件"
        Optional = $true
    },
    @{
        LocalPath = "tgmini20251220\.env.local"
        RemotePath = "$ServerPath/tgmini20251220/.env.local"
        Description = "前端项目 2 环境变量文件"
        Optional = $true
    }
)

$UploadedCount = 0
$SkippedCount = 0
$FailedCount = 0

foreach ($File in $FilesToUpload) {
    $LocalFile = Join-Path $RepoRoot $File.LocalPath
    
    Write-Host "检查: $($File.LocalPath)" -ForegroundColor Cyan
    
    if (Test-Path $LocalFile) {
        Write-Host "  ✅ 文件存在" -ForegroundColor Green
        Write-Host "  📝 $($File.Description)" -ForegroundColor Gray
        
        try {
            Write-Host "  📤 上传中..." -ForegroundColor Yellow
            
            # 使用 scp 上传文件
            $RemoteDir = Split-Path $File.RemotePath -Parent
            $RemoteFile = Split-Path $File.RemotePath -Leaf
            
            # 先创建远程目录（如果需要）
            ssh "$ServerUser@$ServerHost" "mkdir -p $RemoteDir" 2>&1 | Out-Null
            
            # 上传文件
            scp $LocalFile "${ServerUser}@${ServerHost}:$($File.RemotePath)" 2>&1 | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ 上传成功" -ForegroundColor Green
                $UploadedCount++
            } else {
                Write-Host "  ❌ 上传失败 (退出代码: $LASTEXITCODE)" -ForegroundColor Red
                $FailedCount++
            }
        } catch {
            Write-Host "  ❌ 上传失败: $_" -ForegroundColor Red
            $FailedCount++
        }
    } else {
        if ($File.Optional) {
            Write-Host "  ⚠️  文件不存在（可选文件，跳过）" -ForegroundColor Yellow
            $SkippedCount++
        } else {
            Write-Host "  ❌ 文件不存在（必需文件）" -ForegroundColor Red
            $FailedCount++
        }
    }
    Write-Host ""
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📊 上传结果" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ 成功: $UploadedCount" -ForegroundColor Green
Write-Host "⚠️  跳过: $SkippedCount" -ForegroundColor Yellow
Write-Host "❌ 失败: $FailedCount" -ForegroundColor Red
Write-Host ""

if ($FailedCount -eq 0) {
    Write-Host "✅ 所有必需文件已成功上传" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步：在服务器上设置文件权限" -ForegroundColor Cyan
    Write-Host "  ssh $ServerUser@$ServerHost" -ForegroundColor Gray
    Write-Host "  chmod 600 $ServerPath/.env" -ForegroundColor Gray
    Write-Host "  chmod 600 $ServerPath/admin-backend/.env" -ForegroundColor Gray
} else {
    Write-Host "❌ 部分文件上传失败，请检查错误信息" -ForegroundColor Red
    exit 1
}
