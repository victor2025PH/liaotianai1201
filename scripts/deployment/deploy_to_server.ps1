# 自动化部署脚本 - PowerShell 版本
# 使用方法: .\deploy_to_server.ps1 -ServerIP <ip> -Username <user> -Password <pass> -ServerName <name>

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "165.154.255.48",
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$Password = "8iDcGrYb52Fxpzee",
    
    [Parameter(Mandatory=$false)]
    [string]$ServerName = "server"
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "自动化部署到远程服务器" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "服务器: $ServerName ($ServerIP)" -ForegroundColor Cyan
Write-Host "用户名: $Username`n" -ForegroundColor Cyan

# 检查 Posh-SSH 模块
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Write-Host "安装 Posh-SSH 模块..." -ForegroundColor Yellow
    Install-Module -Name Posh-SSH -Force -Scope CurrentUser
}

Import-Module Posh-SSH

# 测试连接
Write-Host "[1/8] 测试服务器连接..." -ForegroundColor Cyan
try {
    $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential($Username, $securePassword)
    
    $session = New-SSHSession -ComputerName $ServerIP -Credential $credential -AcceptKey
    if ($session) {
        Write-Host "✓ 服务器连接成功" -ForegroundColor Green
    } else {
        Write-Host "✗ 服务器连接失败" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ 连接错误: $_" -ForegroundColor Red
    exit 1
}

# 检查系统环境
Write-Host "[2/8] 检查系统环境..." -ForegroundColor Cyan
$result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
echo "=== 系统信息 ==="
uname -a
echo ""
echo "=== Python ==="
python3 --version || echo "Python3 未安装"
echo ""
echo "=== Node.js ==="
node --version || echo "Node.js 未安装"
echo ""
echo "=== Docker ==="
docker --version || echo "Docker 未安装"
echo ""
echo "=== 磁盘空间 ==="
df -h / | tail -1
"@
Write-Host $result.Output

# 创建部署目录
Write-Host "[3/8] 创建部署目录..." -ForegroundColor Cyan
Invoke-SSHCommand -SessionId $session.SessionId -Command @"
mkdir -p ~/telegram-ai-system
mkdir -p ~/telegram-ai-system/backups
mkdir -p ~/telegram-ai-system/sessions
mkdir -p ~/telegram-ai-system/logs
echo '部署目录已创建'
"@ | Out-Null

# 打包项目文件
Write-Host "[4/8] 打包项目文件..." -ForegroundColor Cyan
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$tempDir = [System.IO.Path]::GetTempPath()
$tarFile = Join-Path $tempDir "telegram-ai-system.tar.gz"

# 使用 7-Zip 或 tar（如果可用）
if (Get-Command tar -ErrorAction SilentlyContinue) {
    Push-Location $projectRoot
    tar --exclude='.git' `
        --exclude='node_modules' `
        --exclude='__pycache__' `
        --exclude='*.pyc' `
        --exclude='.env' `
        --exclude='.env.local' `
        --exclude='backups' `
        --exclude='sessions' `
        --exclude='*.log' `
        -czf $tarFile .
    Pop-Location
    Write-Host "✓ 项目文件已打包" -ForegroundColor Green
} else {
    Write-Host "警告: tar 命令不可用，将使用压缩文件" -ForegroundColor Yellow
    # 使用 PowerShell 压缩
    Compress-Archive -Path "$projectRoot\*" -DestinationPath "$tempDir\telegram-ai-system.zip" -Force
    $tarFile = "$tempDir\telegram-ai-system.zip"
}

# 上传项目文件
Write-Host "[5/8] 上传项目文件..." -ForegroundColor Cyan
$uploadSuccess = $false

# 方法 1: 使用原生 SCP 命令（最可靠）
if (Get-Command scp -ErrorAction SilentlyContinue) {
    try {
        Write-Host "  使用 SCP 上传..." -ForegroundColor Gray
        $env:SSHPASS = $Password
        $scpOutput = scp -o StrictHostKeyChecking=no -o ConnectTimeout=30 "$tarFile" "${Username}@${ServerIP}:~/telegram-ai-system/" 2>&1
        Remove-Item Env:\SSHPASS -ErrorAction SilentlyContinue
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ 文件上传完成" -ForegroundColor Green
            $uploadSuccess = $true
        } else {
            Write-Host "  SCP 失败: $scpOutput" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  SCP 错误: $_" -ForegroundColor Yellow
    }
}

# 方法 2: 使用 Posh-SSH
if (-not $uploadSuccess) {
    try {
        Write-Host "  尝试使用 Posh-SSH..." -ForegroundColor Gray
        
        # 尝试 Set-SCPItem (3.x)
        if (Get-Command Set-SCPItem -ErrorAction SilentlyContinue) {
            Set-SCPItem -Session $session -Path $tarFile -Destination "~/telegram-ai-system/" -ErrorAction Stop
            Write-Host "✓ 文件上传完成" -ForegroundColor Green
            $uploadSuccess = $true
        }
        # 尝试 Set-SCPFile (2.x)
        elseif (Get-Command Set-SCPFile -ErrorAction SilentlyContinue) {
            # 检查参数格式
            try {
                Set-SCPFile -Session $session -LocalFile $tarFile -RemotePath "~/telegram-ai-system/" -ErrorAction Stop
            } catch {
                Set-SCPFile -SessionId $session.SessionId -LocalFile $tarFile -RemotePath "~/telegram-ai-system/" -ErrorAction Stop
            }
            Write-Host "✓ 文件上传完成" -ForegroundColor Green
            $uploadSuccess = $true
        }
    } catch {
        Write-Host "  Posh-SSH 失败: $_" -ForegroundColor Yellow
    }
}

# 方法 3: 分块传输（最后手段）
if (-not $uploadSuccess) {
    Write-Host "  使用分块传输..." -ForegroundColor Yellow
    try {
        $fileBytes = [IO.File]::ReadAllBytes($tarFile)
        $chunkSize = 16384  # 16KB chunks
        $totalChunks = [Math]::Ceiling($fileBytes.Length / $chunkSize)
        $fileName = Split-Path $tarFile -Leaf
        $remoteFile = "~/telegram-ai-system/$fileName"
        
        # 在远程服务器上创建文件
        Invoke-SSHCommand -SessionId $session.SessionId -Command "rm -f $remoteFile; touch $remoteFile" | Out-Null
        
        # 分块传输
        for ($i = 0; $i -lt $totalChunks; $i++) {
            $start = $i * $chunkSize
            $length = [Math]::Min($chunkSize, $fileBytes.Length - $start)
            $chunk = $fileBytes[$start..($start + $length - 1)]
            $base64Chunk = [Convert]::ToBase64String($chunk)
            
            $result = Invoke-SSHCommand -SessionId $session.SessionId -Command @"
echo '$base64Chunk' | base64 -d >> $remoteFile
"@
            
            if ($result.ExitStatus -ne 0) {
                throw "分块传输失败 (块 $($i+1)/$totalChunks)"
            }
            
            if (($i + 1) % 20 -eq 0 -or ($i + 1) -eq $totalChunks) {
                Write-Host "    进度: $($i+1)/$totalChunks" -ForegroundColor Gray
            }
        }
        
        Write-Host "✓ 文件上传完成（分块传输）" -ForegroundColor Green
        $uploadSuccess = $true
    } catch {
        Write-Host "✗ 分块传输失败: $_" -ForegroundColor Red
        throw "所有文件上传方法都失败了"
    }
}

# 解压并部署
Write-Host "[6/8] 解压并部署..." -ForegroundColor Cyan
if ($tarFile -like "*.zip") {
    Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd ~/telegram-ai-system
unzip -q -o telegram-ai-system.zip
rm telegram-ai-system.zip
echo '项目文件已解压'
"@ | Out-Null
} else {
    Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd ~/telegram-ai-system
tar -xzf telegram-ai-system.tar.gz
rm telegram-ai-system.tar.gz
echo '项目文件已解压'
"@ | Out-Null
}

# 安装依赖和配置
Write-Host "[7/8] 安装依赖和配置..." -ForegroundColor Cyan
Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd ~/telegram-ai-system

# 安装 Python 依赖
if command -v poetry &> /dev/null; then
    echo '使用 Poetry 安装依赖...'
    cd admin-backend
    poetry install --no-dev
    cd ..
elif [ -f 'admin-backend/requirements.txt' ]; then
    echo '使用 pip 安装依赖...'
    pip3 install -r admin-backend/requirements.txt
fi

# 创建 .env 文件（如果不存在）
if [ ! -f 'admin-backend/.env' ]; then
    echo '创建 .env 文件...'
    # 生成 JWT Secret（使用 Python 或 openssl）
    if command -v openssl &> /dev/null; then
        JWT_SECRET=`$(openssl rand -hex 32)
    elif command -v python3 &> /dev/null; then
        JWT_SECRET=`$(python3 -c "import secrets; print(secrets.token_hex(32))")
    else
        JWT_SECRET=change_me_please_change_in_production_`$(date +%s)
    fi
    
    cat > admin-backend/.env << EOF
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=`$JWT_SECRET
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
fi

# 初始化数据库
if [ -f 'admin-backend/alembic.ini' ]; then
    echo '运行数据库迁移...'
    cd admin-backend
    if command -v poetry &> /dev/null; then
        poetry run alembic upgrade head || echo '迁移失败，将使用自动创建表'
    else
        alembic upgrade head || echo '迁移失败，将使用自动创建表'
    fi
    cd ..
fi

echo '依赖安装和配置完成'
"@ | Out-Null

# 启动服务
Write-Host "[8/8] 启动服务..." -ForegroundColor Cyan
Invoke-SSHCommand -SessionId $session.SessionId -Command @"
cd ~/telegram-ai-system

# 检查服务是否已运行
if pgrep -f 'uvicorn app.main:app' > /dev/null; then
    echo '后端服务已在运行，跳过启动'
else
    echo '启动后端服务...'
    cd admin-backend
    nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
    echo `$! > ../backend.pid
    cd ..
    echo \"后端服务已启动 (PID: `$(cat backend.pid))\"
fi

# 等待服务启动
sleep 5

# 健康检查
if curl -s http://localhost:8000/health > /dev/null; then
    echo '✓ 后端服务健康检查通过'
else
    echo '✗ 后端服务健康检查失败'
fi
"@ | Out-Null

# 清理临时文件
Remove-Item $tarFile -ErrorAction SilentlyContinue

# 断开连接
Remove-SSHSession -SessionId $session.SessionId | Out-Null

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "服务器地址: http://${ServerIP}:8000" -ForegroundColor Cyan
Write-Host "API 文档: http://${ServerIP}:8000/docs" -ForegroundColor Cyan
Write-Host "健康检查: http://${ServerIP}:8000/health`n" -ForegroundColor Cyan

Write-Host "查看日志: ssh ${Username}@${ServerIP} 'tail -f ~/telegram-ai-system/logs/backend.log'" -ForegroundColor Yellow
Write-Host "停止服务: ssh ${Username}@${ServerIP} 'kill \$(cat ~/telegram-ai-system/backend.pid)'`n" -ForegroundColor Yellow

