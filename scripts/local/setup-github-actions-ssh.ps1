# ============================================================
# 设置 GitHub Actions SSH 认证（PowerShell 脚本）
# ============================================================
# 
# 此脚本会：
# 1. 生成专用的 SSH 密钥对
# 2. 将公钥添加到服务器
# 3. 提供私钥内容以便添加到 GitHub Secrets
# ============================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [Parameter(Mandatory=$false)]
    [string]$ServerUser = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$KeyName = "github_deploy"
)

$ErrorActionPreference = "Continue"

function Write-Step { param([string]$Message) Write-Host "`n[$([char]0x2192)] $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message) Write-Host "[✓] $Message" -ForegroundColor Green }
function Write-Error { param([string]$Message) Write-Host "[✗] $Message" -ForegroundColor Red }
function Write-Info { param([string]$Message) Write-Host "[i] $Message" -ForegroundColor Gray }

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  设置 GitHub Actions SSH 认证" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$sshDir = "$env:USERPROFILE\.ssh"
$privateKeyPath = "$sshDir\$KeyName"
$publicKeyPath = "$sshDir\$KeyName.pub"

# 步骤 1: 检查是否已存在密钥
Write-Step "步骤 1: 检查 SSH 密钥"
if (Test-Path $privateKeyPath) {
    Write-Info "检测到已存在的密钥: $privateKeyPath"
    $overwrite = Read-Host "是否覆盖现有密钥？(y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Info "使用现有密钥"
    } else {
        Remove-Item $privateKeyPath -Force -ErrorAction SilentlyContinue
        Remove-Item $publicKeyPath -Force -ErrorAction SilentlyContinue
    }
}

# 步骤 2: 生成 SSH 密钥对
Write-Step "步骤 2: 生成 SSH 密钥对"
if (-not (Test-Path $privateKeyPath)) {
    Write-Info "正在生成 SSH 密钥对..."
    
    # 确保 .ssh 目录存在
    if (-not (Test-Path $sshDir)) {
        New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    }
    
    # 生成密钥（使用 ssh-keygen）
    # Windows 上的 ssh-keygen 需要使用不同的方式处理空密码
    $keygenCmd = "ssh-keygen -t rsa -b 4096 -f `"$privateKeyPath`" -C `"github-actions-deploy`""
    
    # 创建一个临时的 expect-like 脚本或者直接使用 -N 选项（如果支持）
    # 对于 Windows，我们可以尝试使用 echo 来提供空密码
    $process = Start-Process -FilePath "ssh-keygen" -ArgumentList "-t","rsa","-b","4096","-f","`"$privateKeyPath`"","-N","`"`"`"","-C","`"github-actions-deploy`"" -Wait -PassThru -NoNewWindow
    
    if ($process.ExitCode -eq 0) {
        Write-Success "SSH 密钥生成成功"
    } else {
        # 如果上面的方式失败，尝试交互式生成
        Write-Info "尝试交互式生成密钥（将提示输入密码，直接按 Enter 两次）..."
        ssh-keygen -t rsa -b 4096 -f $privateKeyPath -C "github-actions-deploy"
        if (Test-Path $privateKeyPath) {
            Write-Success "SSH 密钥生成成功"
        } else {
            Write-Error "SSH 密钥生成失败"
            exit 1
        }
    }
} else {
    Write-Success "使用现有 SSH 密钥"
}

# 步骤 3: 读取公钥内容
Write-Step "步骤 3: 读取公钥内容"
$publicKey = Get-Content $publicKeyPath -Raw
Write-Info "公钥文件: $publicKeyPath"
Write-Host "`n公钥内容:" -ForegroundColor Yellow
Write-Host $publicKey.Trim()
Write-Host ""

# 步骤 4: 将公钥添加到服务器
Write-Step "步骤 4: 将公钥添加到服务器"
Write-Info "服务器: ${ServerUser}@${ServerIP}"

$copyKey = Read-Host "是否将公钥添加到服务器？(Y/n)"
if ($copyKey -eq "n" -or $copyKey -eq "N") {
    Write-Info "跳过添加公钥到服务器"
    Write-Host "`n请手动执行以下命令：" -ForegroundColor Yellow
    Write-Host "  ssh-copy-id -i $publicKeyPath ${ServerUser}@${ServerIP}" -ForegroundColor Gray
} else {
    Write-Info "正在尝试将公钥添加到服务器..."
    Write-Info "可能需要输入服务器密码..."
    
    # 尝试使用 PowerShell 方式添加公钥
    $publicKeyContent = Get-Content $publicKeyPath -Raw
    $remoteCommand = "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$($publicKeyContent.Trim())' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
    
    $sshResult = ssh "${ServerUser}@${ServerIP}" $remoteCommand 2>&1
    $sshExitCode = $LASTEXITCODE
    
    if ($sshExitCode -eq 0) {
        Write-Success "公钥已成功添加到服务器"
    } else {
        Write-Error "自动添加公钥失败"
        Write-Host "`n请手动执行以下步骤：" -ForegroundColor Yellow
        Write-Host "1. 复制上面的公钥内容" -ForegroundColor Gray
        Write-Host "2. SSH 登录服务器: ssh ${ServerUser}@${ServerIP}" -ForegroundColor Gray
        Write-Host "3. 执行以下命令：" -ForegroundColor Gray
        Write-Host "   mkdir -p ~/.ssh" -ForegroundColor Gray
        Write-Host "   chmod 700 ~/.ssh" -ForegroundColor Gray
        Write-Host "   nano ~/.ssh/authorized_keys" -ForegroundColor Gray
        Write-Host "   （粘贴公钥内容，保存退出）" -ForegroundColor Gray
        Write-Host "   chmod 600 ~/.ssh/authorized_keys" -ForegroundColor Gray
    }
}

# 步骤 5: 测试 SSH 连接
Write-Step "步骤 5: 测试 SSH 连接"
Write-Info "测试 SSH 密钥认证..."

$testCmd = "echo 'SSH 连接成功！'"
$testResult = ssh -i $privateKeyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 "${ServerUser}@${ServerIP}" $testCmd 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Success "SSH 连接测试成功！"
    Write-Host $testResult -ForegroundColor Green
} else {
    Write-Error "SSH 连接测试失败"
    Write-Host $testResult -ForegroundColor Red
    Write-Host "`n请检查：" -ForegroundColor Yellow
    Write-Host "  1. 公钥是否已正确添加到服务器的 ~/.ssh/authorized_keys" -ForegroundColor Gray
    Write-Host "  2. 服务器 SSH 配置是否允许密钥认证" -ForegroundColor Gray
    Write-Host "  3. 防火墙是否允许 SSH 连接（端口 22）" -ForegroundColor Gray
}

# 步骤 6: 显示私钥内容（用于 GitHub Secrets）
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  下一步：添加到 GitHub Secrets" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Info "请按照以下步骤将私钥添加到 GitHub Secrets："
Write-Host ""
Write-Host "1. 打开 GitHub 仓库设置：" -ForegroundColor Yellow
Write-Host "   https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. 找到或创建以下 Secret：" -ForegroundColor Yellow
Write-Host "   - SERVER_SSH_KEY: （更新为下面的私钥内容）" -ForegroundColor Gray
Write-Host "   - SERVER_HOST: $ServerIP" -ForegroundColor Gray
Write-Host "   - SERVER_USER: $ServerUser" -ForegroundColor Gray
Write-Host ""

Write-Host "3. 复制下面的私钥内容（完整内容，包括 -----BEGIN 和 -----END 行）：" -ForegroundColor Yellow
Write-Host ""

# 读取并显示私钥
$privateKey = Get-Content $privateKeyPath -Raw
Write-Host "=========================================" -ForegroundColor Green
Write-Host $privateKey.Trim() -ForegroundColor White
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

Write-Info "提示：私钥内容已复制到剪贴板（如果可能）"
try {
    $privateKey.Trim() | Set-Clipboard
    Write-Success "私钥内容已复制到剪贴板"
} catch {
    Write-Info "无法自动复制到剪贴板，请手动复制"
}

Write-Host ""
Write-Host "4. 在 GitHub Secrets 页面：" -ForegroundColor Yellow
Write-Host "   - 点击 SERVER_SSH_KEY 的 'Update'" -ForegroundColor Gray
Write-Host "   - 粘贴上面的私钥内容" -ForegroundColor Gray
Write-Host "   - 点击 'Update secret'" -ForegroundColor Gray
Write-Host ""

Write-Host "5. 验证其他 Secrets 是否正确：" -ForegroundColor Yellow
Write-Host "   - SERVER_HOST: $ServerIP" -ForegroundColor Gray
Write-Host "   - SERVER_USER: $ServerUser" -ForegroundColor Gray
Write-Host ""

Write-Host "6. 测试 GitHub Actions 部署：" -ForegroundColor Yellow
Write-Host "   - 在 GitHub 仓库的 Actions 页面" -ForegroundColor Gray
Write-Host "   - 找到失败的部署，点击 'Re-run jobs'" -ForegroundColor Gray
Write-Host "   - 查看是否成功" -ForegroundColor Gray
Write-Host ""

Write-Success "设置完成！"
