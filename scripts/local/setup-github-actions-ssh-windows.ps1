# ============================================================
# GitHub Actions SSH Key 设置脚本（Windows）
# ============================================================
# 
# 功能：
# 1. 生成专用的 SSH 密钥对（用于 GitHub Actions）
# 2. 将公钥添加到服务器
# 3. 显示私钥内容（用于添加到 GitHub Secrets）
# 
# 使用方法：
#   .\scripts\local\setup-github-actions-ssh-windows.ps1 -ServerIP "10.56.61.200" -ServerUser "deployer"
# ============================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "",
    
    [Parameter(Mandatory=$false)]
    [string]$ServerUser = "deployer",
    
    [Parameter(Mandatory=$false)]
    [string]$KeyName = "github_deploy",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipServerSetup = $false
)

$ErrorActionPreference = "Continue"

# 颜色输出函数
function Write-Step { param([string]$Message) Write-Host "`n[$([char]0x2192)] $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message) Write-Host "[✓] $Message" -ForegroundColor Green }
function Write-Error { param([string]$Message) Write-Host "[✗] $Message" -ForegroundColor Red }
function Write-Info { param([string]$Message) Write-Host "[i] $Message" -ForegroundColor Gray }
function Write-Warning { param([string]$Message) Write-Host "[!] $Message" -ForegroundColor Yellow }

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  GitHub Actions SSH Key 设置向导" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取 SSH 目录路径
$sshDir = Join-Path $env:USERPROFILE ".ssh"
$privateKeyPath = Join-Path $sshDir "$KeyName"
$publicKeyPath = "$privateKeyPath.pub"

# ============================================================
# 步骤 1: 检查/创建 .ssh 目录
# ============================================================
Write-Step "步骤 1: 检查 .ssh 目录"

if (-not (Test-Path $sshDir)) {
    Write-Info "创建 .ssh 目录..."
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    Write-Success ".ssh 目录已创建: $sshDir"
} else {
    Write-Success ".ssh 目录已存在: $sshDir"
}

# ============================================================
# 步骤 2: 检查是否已存在密钥
# ============================================================
Write-Step "步骤 2: 检查现有密钥"

if (Test-Path $privateKeyPath) {
    Write-Warning "密钥已存在: $privateKeyPath"
    $overwrite = Read-Host "  是否覆盖现有密钥？(y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Info "使用现有密钥"
    } else {
        Remove-Item $privateKeyPath -Force -ErrorAction SilentlyContinue
        Remove-Item $publicKeyPath -Force -ErrorAction SilentlyContinue
        Write-Info "已删除旧密钥"
    }
}

# ============================================================
# 步骤 3: 生成 SSH 密钥
# ============================================================
Write-Step "步骤 3: 生成 SSH 密钥对"

if (-not (Test-Path $privateKeyPath)) {
    Write-Info "正在生成 SSH 密钥对..."
    Write-Info "密钥文件: $privateKeyPath"
    
    # 使用 ssh-keygen 生成密钥（无密码）
    # 使用 -q 参数安静模式，-f 指定文件路径，-N 指定空密码
    try {
        # 方法1：尝试使用 -N "" 参数（空字符串）
        $process = Start-Process -FilePath "ssh-keygen" `
            -ArgumentList @("-t", "rsa", "-b", "4096", "-f", $privateKeyPath, "-N", '""', "-C", "github-actions-deploy", "-q") `
            -Wait -NoNewWindow -PassThru -RedirectStandardOutput "nul" -RedirectStandardError "nul"
        
        if ($process.ExitCode -eq 0 -and (Test-Path $privateKeyPath)) {
            Write-Success "SSH 密钥对生成成功"
        } else {
            # 方法2：如果失败，尝试交互式生成（但会自动处理）
            Write-Info "尝试使用交互式方式生成密钥..."
            $keygenProcess = Start-Process -FilePath "ssh-keygen" `
                -ArgumentList @("-t", "rsa", "-b", "4096", "-f", $privateKeyPath, "-C", "github-actions-deploy") `
                -NoNewWindow -PassThru
            
            # 等待进程完成
            $keygenProcess.WaitForExit()
            
            if ($keygenProcess.ExitCode -eq 0 -and (Test-Path $privateKeyPath)) {
                Write-Success "SSH 密钥对生成成功"
            } else {
                Write-Error "SSH 密钥生成失败，退出码: $($keygenProcess.ExitCode)"
                Write-Info "请手动运行: ssh-keygen -t rsa -b 4096 -f `"$privateKeyPath`" -N `"`" -C `"github-actions-deploy`""
                exit 1
            }
        }
    } catch {
        Write-Error "无法执行 ssh-keygen: $_"
        Write-Info "请确保 OpenSSH 已安装（Windows 10 1809+ 自带）"
        Write-Info "或手动运行: ssh-keygen -t rsa -b 4096 -f `"$privateKeyPath`" -N `"`""
        exit 1
    }
} else {
    Write-Success "使用现有密钥: $privateKeyPath"
}

# ============================================================
# 步骤 4: 读取公钥内容
# ============================================================
Write-Step "步骤 4: 读取公钥内容"

if (-not (Test-Path $publicKeyPath)) {
    Write-Error "公钥文件不存在: $publicKeyPath"
    exit 1
}

$publicKeyContent = Get-Content $publicKeyPath -Raw
Write-Success "公钥已读取"

# ============================================================
# 步骤 5: 将公钥添加到服务器
# ============================================================
if (-not $SkipServerSetup) {
    if ([string]::IsNullOrWhiteSpace($ServerIP)) {
        Write-Step "步骤 5: 将公钥添加到服务器"
        $ServerIP = Read-Host "  请输入服务器 IP 地址"
    } else {
        Write-Step "步骤 5: 将公钥添加到服务器 ($ServerUser@$ServerIP)"
    }
    
    Write-Info "正在将公钥添加到服务器..."
    
    # 构建 SSH 命令来添加公钥
    $sshCommand = @"
mkdir -p ~/.ssh && 
chmod 700 ~/.ssh && 
echo '$($publicKeyContent.Trim())' >> ~/.ssh/authorized_keys && 
chmod 600 ~/.ssh/authorized_keys && 
echo 'SSH_KEY_ADDED_SUCCESS'
"@
    
    try {
        Write-Info "连接到服务器并添加公钥..."
        Write-Warning "可能需要输入服务器密码（仅首次）"
        
        $result = ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$ServerUser@$ServerIP" $sshCommand 2>&1
        
        if ($result -match "SSH_KEY_ADDED_SUCCESS" -or $LASTEXITCODE -eq 0) {
            Write-Success "公钥已成功添加到服务器"
            
            # 测试 SSH 连接
            Write-Info "测试 SSH 密钥认证..."
            $testResult = ssh -i $privateKeyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$ServerUser@$ServerIP" "echo 'SSH_KEY_TEST_SUCCESS'" 2>&1
            
            if ($testResult -match "SSH_KEY_TEST_SUCCESS" -or $LASTEXITCODE -eq 0) {
                Write-Success "SSH 密钥认证测试成功！"
            } else {
                Write-Warning "SSH 密钥认证测试失败，但公钥已添加"
                Write-Info "可能需要手动测试或检查服务器配置"
            }
        } else {
            Write-Warning "自动添加公钥失败，请手动添加"
            Write-Info ""
            Write-Info "请执行以下步骤："
            Write-Info "1. 复制以下公钥内容："
            Write-Host ""
            Write-Host $publicKeyContent.Trim() -ForegroundColor Yellow
            Write-Host ""
            Write-Info "2. 登录服务器："
            Write-Host "   ssh $ServerUser@$ServerIP" -ForegroundColor Cyan
            Write-Info "3. 在服务器上执行："
            Write-Host "   mkdir -p ~/.ssh" -ForegroundColor Cyan
            Write-Host "   chmod 700 ~/.ssh" -ForegroundColor Cyan
            Write-Host "   nano ~/.ssh/authorized_keys" -ForegroundColor Cyan
            Write-Info "4. 粘贴公钥内容，保存退出（Ctrl+X, Y, Enter）"
            Write-Host "   chmod 600 ~/.ssh/authorized_keys" -ForegroundColor Cyan
        }
    } catch {
        Write-Error "连接服务器失败: $_"
        Write-Info "请检查："
        Write-Info "  1. 服务器 IP 地址是否正确"
        Write-Info "  2. 网络连接是否正常"
        Write-Info "  3. SSH 服务是否运行（端口 22）"
        Write-Info ""
        Write-Info "您可以稍后手动添加公钥（见上面的说明）"
    }
} else {
    Write-Step "步骤 5: 跳过服务器设置（SkipServerSetup = true）"
}

# ============================================================
# 步骤 6: 显示私钥内容（用于 GitHub Secrets）
# ============================================================
Write-Step "步骤 6: 准备添加到 GitHub Secrets"

Write-Info "读取私钥内容..."
$privateKeyContent = Get-Content $privateKeyPath -Raw

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  GitHub Secrets 配置说明" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

Write-Info "1. 打开 GitHub 仓库设置："
Write-Host "   https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions" -ForegroundColor Cyan
Write-Host ""

Write-Info "2. 点击 'New repository secret'，添加以下 Secrets："
Write-Host ""
Write-Host "   Secret 1: SERVER_SSH_KEY" -ForegroundColor Green
Write-Info "   值：复制下面的私钥内容（完整内容，包括 BEGIN 和 END 行）"
Write-Host ""
Write-Host "   Secret 2: SERVER_HOST" -ForegroundColor Green
Write-Info "   值：$ServerIP"
Write-Host ""
Write-Host "   Secret 3: SERVER_USER" -ForegroundColor Green
Write-Info "   值：$ServerUser"
Write-Host ""

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  私钥内容（复制以下全部内容）" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host $privateKeyContent.Trim() -ForegroundColor White -BackgroundColor DarkBlue
Write-Host ""

# 尝试复制到剪贴板
try {
    $privateKeyContent.Trim() | Set-Clipboard
    Write-Success "私钥内容已复制到剪贴板！"
    Write-Info "您可以直接粘贴到 GitHub Secrets 中"
} catch {
    Write-Warning "无法自动复制到剪贴板，请手动复制上面的私钥内容"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Info "下一步："
Write-Info "  1. 将私钥添加到 GitHub Secrets (SERVER_SSH_KEY)"
Write-Info "  2. 确保 SERVER_HOST 和 SERVER_USER Secrets 已设置"
Write-Info "  3. 在 GitHub Actions 中测试部署"
Write-Host ""
