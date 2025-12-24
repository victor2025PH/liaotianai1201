# 本地构建三个 Vite 项目并准备上传
# 用法: .\scripts\local\build_and_upload.ps1

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "本地构建三个 Vite 项目" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 项目配置
$Projects = @(
    @{
        Name = "tgmini"
        LocalDir = ""  # 将在下面检测
        ServerDir = "/opt/web3-sites/tgmini20251220"
        Port = 3001
        PM2Name = "tgmini-frontend"
    },
    @{
        Name = "hongbao"
        LocalDir = ""  # 将在下面检测
        ServerDir = "/opt/web3-sites/hbwy20251220"
        Port = 3002
        PM2Name = "hongbao-frontend"
    },
    @{
        Name = "aizkw"
        LocalDir = ""  # 将在下面检测
        ServerDir = "/opt/web3-sites/aizkw20251219"
        Port = 3003
        PM2Name = "aizkw-frontend"
    }
)

# 可能的基础路径
$PossibleBasePaths = @(
    "D:\telegram-ai-system",
    "D:\wxedge_storage"
)

# 可能的子目录结构
$PossibleSubPaths = @{
    "tgmini20251220" = @("tgmini20251220", "tgmini20251220")
    "hbwy20251220" = @("hbwy20251220", "react-vite-template\hbwy20251220", "hbwy20251220")
    "aizkw20251219" = @("aizkw20251219", "migrations\aizkw20251219", "aizkw20251219")
}

# 查找项目目录
Write-Host "查找项目目录..." -ForegroundColor Yellow
Write-Host ""

foreach ($project in $Projects) {
    $projectName = $project.Name
    $dirName = switch ($projectName) {
        "tgmini" { "tgmini20251220" }
        "hongbao" { "hbwy20251220" }
        "aizkw" { "aizkw20251219" }
    }
    
    $found = $false
    
    # 方法1：按标准路径查找
    foreach ($basePath in $PossibleBasePaths) {
        if (-not (Test-Path $basePath)) {
            continue
        }
        
        $subPaths = $PossibleSubPaths[$dirName]
        foreach ($subPath in $subPaths) {
            $fullPath = Join-Path $basePath $subPath
            $packageJsonPath = Join-Path $fullPath "package.json"
            
            if (Test-Path $packageJsonPath) {
                $project.LocalDir = $fullPath
                Write-Host "✅ $projectName 找到: $fullPath" -ForegroundColor Green
                $found = $true
                break
            }
        }
        
        if ($found) {
            break
        }
    }
    
    # 方法2：递归搜索（如果标准路径没找到）
    if (-not $found) {
        foreach ($basePath in $PossibleBasePaths) {
            if (-not (Test-Path $basePath)) {
                continue
            }
            
            $foundDirs = Get-ChildItem $basePath -Recurse -Directory -Filter $dirName -ErrorAction SilentlyContinue | Where-Object {
                Test-Path (Join-Path $_.FullName "package.json")
            }
            
            if ($foundDirs) {
                $project.LocalDir = $foundDirs[0].FullName
                Write-Host "✅ $projectName 找到（递归搜索）: $($foundDirs[0].FullName)" -ForegroundColor Green
                $found = $true
                break
            }
        }
    }
    
    if (-not $found) {
        Write-Host "❌ $projectName 未找到" -ForegroundColor Red
        Write-Host "   请手动指定路径，或确保项目存在于以下位置之一:" -ForegroundColor Yellow
        foreach ($basePath in $PossibleBasePaths) {
            Write-Host "     - $basePath\$dirName" -ForegroundColor Gray
            if ($basePath -eq "D:\telegram-ai-system") {
                $subPaths = $PossibleSubPaths[$dirName]
                foreach ($subPath in $subPaths) {
                    Write-Host "     - $basePath\$subPath" -ForegroundColor Gray
                }
            }
        }
        Write-Host ""
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "开始构建" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$BuildResults = @()

foreach ($project in $Projects) {
    if ([string]::IsNullOrEmpty($project.LocalDir)) {
        Write-Host "⏭️  跳过 $($project.Name)（未找到目录）" -ForegroundColor Yellow
        $BuildResults += @{
            Name = $project.Name
            Success = $false
            Reason = "目录未找到"
        }
        continue
    }
    
    Write-Host "构建 $($project.Name)..." -ForegroundColor Cyan
    Write-Host "  目录: $($project.LocalDir)" -ForegroundColor Gray
    Write-Host ""
    
    Push-Location $project.LocalDir
    
    try {
        # 检查是否有 node_modules
        if (-not (Test-Path "node_modules")) {
            Write-Host "  📥 安装依赖..." -ForegroundColor Yellow
            npm install
        } else {
            Write-Host "  ✅ 依赖已存在，跳过安装" -ForegroundColor Green
        }
        
        # 构建
        Write-Host "  🔨 构建项目..." -ForegroundColor Yellow
        npm run build
        
        # 检查构建结果
        if (Test-Path "dist" -PathType Container) {
            $distFiles = Get-ChildItem "dist" -Recurse -File
            if ($distFiles.Count -gt 0) {
                Write-Host "  ✅ 构建成功！($($distFiles.Count) 个文件)" -ForegroundColor Green
                $BuildResults += @{
                    Name = $project.Name
                    Success = $true
                    DistPath = (Join-Path $project.LocalDir "dist")
                    ServerDir = $project.ServerDir
                }
            } else {
                Write-Host "  ❌ 构建失败：dist 目录为空" -ForegroundColor Red
                $BuildResults += @{
                    Name = $project.Name
                    Success = $false
                    Reason = "dist 目录为空"
                }
            }
        } else {
            Write-Host "  ❌ 构建失败：dist 目录不存在" -ForegroundColor Red
            $BuildResults += @{
                Name = $project.Name
                Success = $false
                Reason = "dist 目录不存在"
            }
        }
    } catch {
        Write-Host "  ❌ 构建失败: $_" -ForegroundColor Red
        $BuildResults += @{
            Name = $project.Name
            Success = $false
            Reason = $_.Exception.Message
        }
    } finally {
        Pop-Location
    }
    
    Write-Host ""
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "构建结果" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$SuccessCount = ($BuildResults | Where-Object { $_.Success }).Count
$FailedCount = ($BuildResults | Where-Object { -not $_.Success }).Count

Write-Host "成功: $SuccessCount 个" -ForegroundColor Green
Write-Host "失败: $FailedCount 个" -ForegroundColor $(if ($FailedCount -gt 0) { "Red" } else { "Green" })
Write-Host ""

# 生成上传命令
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "上传到服务器的命令" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "在 PowerShell 中执行以下命令上传 dist 目录：" -ForegroundColor Yellow
Write-Host ""

foreach ($result in $BuildResults) {
    if ($result.Success) {
        $localDist = $result.DistPath
        $serverDir = $result.ServerDir
        
        Write-Host "# 上传 $($result.Name)" -ForegroundColor Cyan
        Write-Host "scp -r `"$localDist`" ubuntu@10.56.198.218:$serverDir/" -ForegroundColor White
        Write-Host ""
    }
}

Write-Host "然后在服务器上执行以下命令启动服务：" -ForegroundColor Yellow
Write-Host ""

foreach ($result in $BuildResults) {
    if ($result.Success) {
        $project = $Projects | Where-Object { $_.Name -eq $result.Name } | Select-Object -First 1
        Write-Host "# 启动 $($result.Name)" -ForegroundColor Cyan
        Write-Host "cd /opt/web3-sites" -ForegroundColor White
        Write-Host "pm2 start serve --name $($project.PM2Name) -- -s $($project.ServerDir)/dist -l $($project.Port)" -ForegroundColor White
        Write-Host ""
    }
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "完成！" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

