# 创建部署文件包
# 使用方法: .\create_deployment_package.ps1 [-OutputDir <dir>]

param(
    [Parameter(Mandatory=$false)]
    [string]$OutputDir = "deployment-package"
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "创建部署文件包" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 获取项目根目录
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$packageDir = Join-Path $projectRoot $OutputDir

Write-Host "项目根目录: $projectRoot" -ForegroundColor Gray
Write-Host "输出目录: $packageDir`n" -ForegroundColor Gray

# 创建输出目录
if (Test-Path $packageDir) {
    Write-Host "清理现有目录..." -ForegroundColor Yellow
    Remove-Item $packageDir -Recurse -Force
}
New-Item -ItemType Directory -Path $packageDir -Force | Out-Null

Write-Host "[1/5] 复制必要文件..." -ForegroundColor Cyan

# 需要部署的目录和文件
$itemsToCopy = @(
    "admin-backend",
    "group_ai_service",
    "utils",
    "main.py",
    "config.py",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "README.md"
)

foreach ($item in $itemsToCopy) {
    $sourcePath = Join-Path $projectRoot $item
    $destPath = Join-Path $packageDir $item
    
    if (Test-Path $sourcePath) {
        Write-Host "  复制: $item" -ForegroundColor Gray
        if (Test-Path $sourcePath -PathType Container) {
            Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force
        } else {
            Copy-Item -Path $sourcePath -Destination $destPath -Force
        }
    } else {
        Write-Host "  跳过: $item (不存在)" -ForegroundColor Yellow
    }
}

Write-Host "`n[2/5] 清理不需要的文件..." -ForegroundColor Cyan

# 需要删除的文件和目录
$patternsToRemove = @(
    "**\__pycache__",
    "**\*.pyc",
    "**\*.pyo",
    "**\*.pyd",
    "**\.pytest_cache",
    "**\htmlcov",
    "**\dist",
    "**\build",
    "**\*.egg-info",
    "**\.env",
    "**\.env.local",
    "**\*.log",
    "**\node_modules",
    "**\.next",
    "**\out",
    "**\dist",
    "**\sessions",
    "**\backups"
)

foreach ($pattern in $patternsToRemove) {
    $files = Get-ChildItem -Path $packageDir -Include $pattern -Recurse -ErrorAction SilentlyContinue
    if ($files) {
        Write-Host "  删除: $pattern ($($files.Count) 个文件)" -ForegroundColor Gray
        $files | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "`n[3/5] 创建部署说明文件..." -ForegroundColor Cyan

$deployInstructions = @"
# 部署说明

## 文件上传

1. 将整个 deployment-package 目录上传到服务器的以下位置：
   - 洛杉矶/马尼拉服务器: ~/telegram-ai-system/
   - worker-01: /opt/group-ai/

2. 上传方式：
   - 使用 WinSCP、FileZilla 或其他 FTP/SCP 客户端
   - 或使用 scp 命令：
     ```bash
     scp -r deployment-package/* ubuntu@165.154.255.48:~/telegram-ai-system/
     ```

## 部署步骤

### 1. 上传文件后，SSH 连接到服务器

```bash
ssh ubuntu@165.154.255.48
# 或
ssh ubuntu@165.154.233.179
# 或 worker-01
ssh ubuntu@165.154.254.99
```

### 2. 进入部署目录

**洛杉矶/马尼拉服务器:**
```bash
cd ~/telegram-ai-system
```

**worker-01:**
```bash
cd /opt/group-ai
```

### 3. 安装 Python 依赖

```bash
# 如果有 poetry
cd admin-backend
poetry install --no-dev

# 或使用 pip
pip3 install -r requirements.txt
```

### 4. 创建 .env 文件

```bash
cd admin-backend
cat > .env << 'EOF'
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
```

### 5. 创建必要目录

```bash
mkdir -p sessions
mkdir -p logs
chmod 700 sessions
chmod 755 logs
```

### 6. 启动服务

**洛杉矶/马尼拉服务器:**
```bash
cd admin-backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
echo $! > ../backend.pid
```

**worker-01 (使用 systemd):**
```bash
sudo systemctl start group-ai-worker
sudo systemctl enable group-ai-worker
```

### 7. 验证部署

```bash
# 检查进程
ps aux | grep uvicorn

# 检查端口
netstat -tlnp | grep 8000

# 健康检查
curl http://localhost:8000/health
```

## 服务器信息

### 洛杉矶服务器
- IP: 165.154.255.48
- 用户名: ubuntu
- 密码: 8iDcGrYb52Fxpzee
- 部署目录: ~/telegram-ai-system

### 马尼拉服务器
- IP: 165.154.233.179
- 用户名: ubuntu
- 密码: 8iDcGrYb52Fxpzee
- 部署目录: ~/telegram-ai-system

### worker-01
- IP: 165.154.254.99
- 用户名: ubuntu
- 密码: Along2025!!!
- 部署目录: /opt/group-ai

## 注意事项

1. 确保服务器已安装 Python 3.11+
2. 确保防火墙允许 8000 端口
3. 首次部署需要安装依赖，可能需要 5-10 分钟
4. 部署后需要手动配置环境变量（如 API keys）

"@

$instructionsPath = Join-Path $packageDir "DEPLOY_INSTRUCTIONS.md"
$deployInstructions | Out-File -FilePath $instructionsPath -Encoding UTF8
Write-Host "  ✓ 已创建: DEPLOY_INSTRUCTIONS.md" -ForegroundColor Green

Write-Host "`n[4/5] 计算文件大小..." -ForegroundColor Cyan
$totalSize = (Get-ChildItem -Path $packageDir -Recurse -File | Measure-Object -Property Length -Sum).Sum
$sizeMB = [math]::Round($totalSize / 1MB, 2)
Write-Host "  总大小: $sizeMB MB" -ForegroundColor Green

Write-Host "`n[5/5] 创建压缩包..." -ForegroundColor Cyan

# 创建压缩包
$zipFile = Join-Path $projectRoot "$OutputDir.zip"
if (Test-Path $zipFile) {
    Remove-Item $zipFile -Force
}

Compress-Archive -Path $packageDir -DestinationPath $zipFile -Force
$zipSize = [math]::Round((Get-Item $zipFile).Length / 1MB, 2)

Write-Host "  ✓ 压缩包已创建: $OutputDir.zip ($zipSize MB)" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "部署文件包创建完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "文件位置:" -ForegroundColor Yellow
Write-Host "  目录: $packageDir" -ForegroundColor Cyan
Write-Host "  压缩包: $zipFile" -ForegroundColor Cyan
Write-Host "`n下一步:" -ForegroundColor Yellow
Write-Host "  1. 使用 FTP/SCP 客户端上传 $OutputDir 目录或 $OutputDir.zip" -ForegroundColor White
Write-Host "  2. 参考 $packageDir\DEPLOY_INSTRUCTIONS.md 进行部署" -ForegroundColor White
Write-Host "`n推荐上传方式:" -ForegroundColor Yellow
Write-Host "  • WinSCP (Windows)" -ForegroundColor Gray
Write-Host "  • FileZilla (跨平台)" -ForegroundColor Gray
Write-Host "  • scp 命令" -ForegroundColor Gray

