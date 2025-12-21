# 简单的项目文件上传脚本
# 使用方法：在 PowerShell 中运行此脚本，然后按提示输入服务器 IP

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "",
    
    [Parameter(Mandatory=$false)]
    [string]$ServerUser = "ubuntu"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "📤 上传项目文件到服务器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 如果没有提供服务器 IP，提示用户输入
if ([string]::IsNullOrEmpty($ServerIP)) {
    Write-Host "请输入服务器 IP 地址：" -ForegroundColor Yellow
    $ServerIP = Read-Host
}

if ([string]::IsNullOrEmpty($ServerIP)) {
    Write-Host "❌ 服务器 IP 不能为空" -ForegroundColor Red
    exit 1
}

Write-Host "服务器 IP: $ServerIP" -ForegroundColor Green
Write-Host "服务器用户: $ServerUser" -ForegroundColor Green
Write-Host ""

# 检查本地项目目录
$LocalBasePath = "D:\telegram-ai-system"
if (-not (Test-Path $LocalBasePath)) {
    Write-Host "❌ 本地项目目录不存在: $LocalBasePath" -ForegroundColor Red
    Write-Host "   请修改脚本中的路径或创建该目录" -ForegroundColor Yellow
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

# 检查 scp 是否可用
$scpCommand = Get-Command scp -ErrorAction SilentlyContinue
if (-not $scpCommand) {
    Write-Host "❌ scp 命令未找到" -ForegroundColor Red
    Write-Host ""
    Write-Host "请安装 OpenSSH 客户端：" -ForegroundColor Yellow
    Write-Host "1. 打开 Windows 设置" -ForegroundColor White
    Write-Host "2. 应用 → 可选功能" -ForegroundColor White
    Write-Host "3. 添加功能 → 选择 'OpenSSH 客户端'" -ForegroundColor White
    Write-Host "4. 重启 PowerShell" -ForegroundColor White
    Write-Host ""
    Write-Host "或者使用 WinSCP（图形界面工具）：" -ForegroundColor Yellow
    Write-Host "  下载地址: https://winscp.net/" -ForegroundColor White
    exit 1
}

Write-Host "✅ scp 命令可用" -ForegroundColor Green
Write-Host ""

# 测试 SSH 连接
Write-Host "🔍 测试 SSH 连接..." -ForegroundColor Cyan
try {
    $testResult = ssh -o ConnectTimeout=5 -o BatchMode=yes "$ServerUser@${ServerIP}" "echo '连接成功'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ SSH 连接测试成功" -ForegroundColor Green
    } else {
        Write-Host "⚠️  SSH 连接测试失败，但继续尝试上传..." -ForegroundColor Yellow
        Write-Host "   如果上传失败，请检查：" -ForegroundColor Yellow
        Write-Host "   - 服务器 IP 是否正确" -ForegroundColor White
        Write-Host "   - SSH 服务是否运行" -ForegroundColor White
        Write-Host "   - 防火墙是否开放端口 22" -ForegroundColor White
    }
} catch {
    Write-Host "⚠️  无法测试 SSH 连接，继续尝试上传..." -ForegroundColor Yellow
}
Write-Host ""

# 上传每个项目
$SuccessCount = 0
$FailedProjects = @()

foreach ($project in $Projects) {
    $LocalProjectPath = Join-Path $LocalBasePath $project.LocalDir
    $ServerProjectPath = "$ServerUser@${ServerIP}:/home/ubuntu/telegram-ai-system/$($project.ServerDir)"
    
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "📤 上传项目: $($project.Name)" -ForegroundColor Cyan
    Write-Host "本地: $LocalProjectPath" -ForegroundColor Gray
    Write-Host "服务器: $ServerProjectPath" -ForegroundColor Gray
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
    if (-not (Test-Path $LocalProjectPath)) {
        Write-Host "❌ 本地项目目录不存在: $LocalProjectPath" -ForegroundColor Red
        Write-Host "   跳过此项目" -ForegroundColor Yellow
        $FailedProjects += "$($project.Name) (本地目录不存在)"
        Write-Host ""
        continue
    }
    
    # 检查 package.json
    $PackageJson = Join-Path $LocalProjectPath "package.json"
    if (-not (Test-Path $PackageJson)) {
        Write-Host "⚠️  警告: package.json 不存在: $PackageJson" -ForegroundColor Yellow
        Write-Host "   继续上传其他文件..." -ForegroundColor Yellow
    } else {
        Write-Host "✅ 找到 package.json" -ForegroundColor Green
    }
    
    # 创建服务器目录
    Write-Host "📁 创建服务器目录..." -ForegroundColor Gray
    try {
        ssh "$ServerUser@${ServerIP}" "mkdir -p /home/ubuntu/telegram-ai-system/$($project.ServerDir)" 2>&1 | Out-Null
        Write-Host "✅ 服务器目录已创建" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  无法创建服务器目录，继续尝试上传..." -ForegroundColor Yellow
    }
    
    # 上传文件（排除 node_modules 和 dist）
    Write-Host "📤 上传文件..." -ForegroundColor Cyan
    Write-Host "   (这可能需要几分钟，请耐心等待...)" -ForegroundColor Gray
    
    try {
        # 使用 scp 上传，排除 node_modules 和 dist
        $excludeArgs = @(
            "-r",
            "--exclude=node_modules",
            "--exclude=dist",
            "--exclude=.git"
        )
        
        # 由于 scp 不支持 --exclude，我们需要手动选择文件
        # 创建一个临时文件列表
        $filesToUpload = Get-ChildItem -Path $LocalProjectPath -File -Recurse | 
            Where-Object { 
                $relativePath = $_.FullName.Substring($LocalProjectPath.Length + 1)
                -not ($relativePath -like "node_modules\*") -and
                -not ($relativePath -like "dist\*") -and
                -not ($relativePath -like ".git\*")
            }
        
        # 使用 tar 压缩并传输（如果可用），否则使用 scp
        $useTar = $false
        try {
            $tarCommand = Get-Command tar -ErrorAction SilentlyContinue
            if ($tarCommand) {
                $useTar = $true
            }
        } catch {}
        
        if ($useTar) {
            # 使用 tar + ssh（更高效）
            Write-Host "   使用 tar 压缩传输..." -ForegroundColor Gray
            $tarOutput = tar -czf - -C $LocalProjectPath --exclude=node_modules --exclude=dist --exclude=.git . 2>&1 | 
                ssh "$ServerUser@${ServerIP}" "cd /home/ubuntu/telegram-ai-system/$($project.ServerDir) && tar -xzf -" 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ 上传成功: $($project.Name)" -ForegroundColor Green
                $SuccessCount++
            } else {
                throw "tar 传输失败"
            }
        } else {
            # 使用 scp（较慢但兼容性好）
            Write-Host "   使用 scp 传输..." -ForegroundColor Gray
            $scpOutput = scp -r "$LocalProjectPath\*" "$ServerProjectPath/" 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ 上传成功: $($project.Name)" -ForegroundColor Green
                $SuccessCount++
            } else {
                # 检查是否是权限问题
                if ($scpOutput -match "Permission denied") {
                    throw "权限被拒绝，请检查 SSH 密钥或密码"
                } elseif ($scpOutput -match "Could not resolve hostname") {
                    throw "无法解析主机名，请检查服务器 IP"
                } else {
                    throw "上传失败: $scpOutput"
                }
            }
        }
    } catch {
        Write-Host "❌ 上传失败: $($project.Name)" -ForegroundColor Red
        Write-Host "   错误: $_" -ForegroundColor Red
        $FailedProjects += "$($project.Name) (上传失败)"
    }
    
    Write-Host ""
}

# 总结
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "📊 上传结果汇总" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "成功: $SuccessCount / $($Projects.Count)" -ForegroundColor $(if ($SuccessCount -eq $Projects.Count) { "Green" } else { "Yellow" })

if ($FailedProjects.Count -gt 0) {
    Write-Host "失败: $($FailedProjects.Count)" -ForegroundColor Red
    Write-Host "失败的项目:" -ForegroundColor Red
    foreach ($failed in $FailedProjects) {
        Write-Host "  - $failed" -ForegroundColor Red
    }
}
Write-Host ""

if ($SuccessCount -gt 0) {
    Write-Host "✅ 部分或全部文件上传成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步操作（在服务器上执行）：" -ForegroundColor Yellow
    Write-Host "1. 验证文件: ls -la /home/ubuntu/telegram-ai-system/*/package.json" -ForegroundColor White
    Write-Host "2. 构建并启动: sudo bash /home/ubuntu/telegram-ai-system/scripts/server/build_and_start_all.sh" -ForegroundColor White
    Write-Host "3. 检查服务: pm2 list" -ForegroundColor White
} else {
    Write-Host "❌ 所有上传都失败了" -ForegroundColor Red
    Write-Host ""
    Write-Host "请检查：" -ForegroundColor Yellow
    Write-Host "1. 服务器 IP 是否正确: $ServerIP" -ForegroundColor White
    Write-Host "2. SSH 服务是否运行" -ForegroundColor White
    Write-Host "3. 防火墙是否开放端口 22" -ForegroundColor White
    Write-Host "4. SSH 密钥或密码是否正确" -ForegroundColor White
    Write-Host ""
    Write-Host "或者使用 WinSCP（图形界面工具）：" -ForegroundColor Yellow
    Write-Host "  下载地址: https://winscp.net/" -ForegroundColor White
}
