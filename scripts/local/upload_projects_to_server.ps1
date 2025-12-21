# PowerShell 脚本：上传项目文件到服务器
# 使用方法：在 PowerShell 中运行此脚本

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [Parameter(Mandatory=$true)]
    [string]$ServerUser = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$ServerPath = "/home/ubuntu/telegram-ai-system"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "📤 上传项目文件到服务器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查本地项目目录
$LocalBasePath = "D:\telegram-ai-system"
if (-not (Test-Path $LocalBasePath)) {
    Write-Host "❌ 本地项目目录不存在: $LocalBasePath" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 本地项目目录: $LocalBasePath" -ForegroundColor Green
Write-Host ""

# 项目配置
$Projects = @(
    @{
        Name = "tgmini"
        LocalDir = "tgmini20251220"
        ServerDir = "tgmini20251220"
    },
    @{
        Name = "hongbao"
        LocalDir = "hbwy20251220"
        ServerDir = "hbwy20251220"
    },
    @{
        Name = "aizkw"
        LocalDir = "aizkw20251219"
        ServerDir = "aizkw20251219"
    }
)

# 检查 scp 是否可用（需要安装 OpenSSH 客户端）
$scpCommand = Get-Command scp -ErrorAction SilentlyContinue
if (-not $scpCommand) {
    Write-Host "⚠️  scp 命令未找到，请安装 OpenSSH 客户端" -ForegroundColor Yellow
    Write-Host "   或在 Windows 设置中启用 'OpenSSH 客户端'" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   或者使用 WinSCP、FileZilla 等工具手动上传" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ scp 命令可用" -ForegroundColor Green
Write-Host ""

# 上传每个项目
foreach ($project in $Projects) {
    $LocalProjectPath = Join-Path $LocalBasePath $project.LocalDir
    $ServerProjectPath = "$ServerUser@${ServerIP}:$ServerPath/$($project.ServerDir)"
    
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "📤 上传项目: $($project.Name)" -ForegroundColor Cyan
    Write-Host "本地目录: $LocalProjectPath" -ForegroundColor Cyan
    Write-Host "服务器目录: $ServerProjectPath" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
    if (-not (Test-Path $LocalProjectPath)) {
        Write-Host "❌ 本地项目目录不存在: $LocalProjectPath" -ForegroundColor Red
        Write-Host "   跳过此项目" -ForegroundColor Yellow
        Write-Host ""
        continue
    }
    
    # 检查关键文件
    $PackageJson = Join-Path $LocalProjectPath "package.json"
    if (-not (Test-Path $PackageJson)) {
        Write-Host "⚠️  警告: package.json 不存在: $PackageJson" -ForegroundColor Yellow
        Write-Host "   继续上传其他文件..." -ForegroundColor Yellow
    } else {
        Write-Host "✅ 找到 package.json" -ForegroundColor Green
    }
    
    # 上传整个项目目录（排除 node_modules 和 dist，这些可以在服务器上构建）
    Write-Host "📤 上传文件到服务器..." -ForegroundColor Cyan
    
    # 使用 scp 上传（排除 node_modules 和 dist）
    $ExcludePatterns = @("node_modules", "dist", ".git", "*.log")
    
    # 创建临时文件列表
    $TempFileList = [System.IO.Path]::GetTempFileName()
    Get-ChildItem -Path $LocalProjectPath -Recurse -File | 
        Where-Object { 
            $relativePath = $_.FullName.Substring($LocalProjectPath.Length + 1)
            $shouldExclude = $false
            foreach ($pattern in $ExcludePatterns) {
                if ($relativePath -like "*$pattern*") {
                    $shouldExclude = $true
                    break
                }
            }
            -not $shouldExclude
        } | 
        ForEach-Object { $_.FullName } | 
        Out-File -FilePath $TempFileList -Encoding UTF8
    
    # 使用 scp 上传
    try {
        # 先创建服务器目录
        Write-Host "   创建服务器目录..." -ForegroundColor Gray
        ssh "$ServerUser@${ServerIP}" "mkdir -p $ServerPath/$($project.ServerDir)"
        
        # 上传文件
        Write-Host "   上传文件..." -ForegroundColor Gray
        scp -r "$LocalProjectPath\*" "$ServerProjectPath/" 2>&1 | ForEach-Object {
            if ($_ -match "error|Error|ERROR|failed|Failed|FAILED") {
                Write-Host "   ⚠️  $_" -ForegroundColor Yellow
            } else {
                Write-Host "   $_" -ForegroundColor Gray
            }
        }
        
        Write-Host "✅ 上传完成: $($project.Name)" -ForegroundColor Green
    } catch {
        Write-Host "❌ 上传失败: $($project.Name)" -ForegroundColor Red
        Write-Host "   错误: $_" -ForegroundColor Red
    } finally {
        # 清理临时文件
        if (Test-Path $TempFileList) {
            Remove-Item $TempFileList -Force
        }
    }
    
    Write-Host ""
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ 上传完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Yellow
Write-Host "1. 在服务器上运行: sudo bash scripts/server/build_and_start_all.sh" -ForegroundColor White
Write-Host "2. 检查服务状态: pm2 list" -ForegroundColor White
Write-Host "3. 验证端口监听: sudo netstat -tlnp | grep -E ':(3001|3002|3003)'" -ForegroundColor White
