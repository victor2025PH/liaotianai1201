# ============================================================
# 简单生成 SSH 密钥脚本（适用于 Windows）
# ============================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "165.154.254.24",
    
    [Parameter(Mandatory=$false)]
    [string]$ServerUser = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$KeyName = "github_deploy"
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  生成 SSH 密钥并配置 GitHub Actions" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$sshDir = "$env:USERPROFILE\.ssh"
$privateKeyPath = "$sshDir\$KeyName"
$publicKeyPath = "$sshDir\$KeyName.pub"

# 确保 .ssh 目录存在
Write-Host "检查 .ssh 目录..." -ForegroundColor Cyan
if (-not (Test-Path $sshDir)) {
    Write-Host "创建 .ssh 目录: $sshDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    if (Test-Path $sshDir) {
        Write-Host "[✓] .ssh 目录创建成功" -ForegroundColor Green
    } else {
        Write-Host "[✗] .ssh 目录创建失败" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[✓] .ssh 目录已存在: $sshDir" -ForegroundColor Green
}

# 步骤 1: 生成 SSH 密钥
Write-Host "`n步骤 1: 生成 SSH 密钥" -ForegroundColor Cyan
Write-Host "提示：当提示输入密码时，直接按 Enter（不设置密码）" -ForegroundColor Yellow
Write-Host ""

if (Test-Path $privateKeyPath) {
    $overwrite = Read-Host "密钥已存在，是否覆盖？(y/N)"
    if ($overwrite -eq "y" -or $overwrite -eq "Y") {
        Remove-Item $privateKeyPath -Force -ErrorAction SilentlyContinue
        Remove-Item $publicKeyPath -Force -ErrorAction SilentlyContinue
    } else {
        Write-Host "[i] 使用现有密钥" -ForegroundColor Gray
    }
}

if (-not (Test-Path $privateKeyPath)) {
    # 使用交互式方式生成密钥（更可靠）
    ssh-keygen -t rsa -b 4096 -f $privateKeyPath -C "github-actions-deploy"
    
    if (Test-Path $privateKeyPath) {
        Write-Host "[✓] SSH 密钥生成成功" -ForegroundColor Green
    } else {
        Write-Host "[✗] SSH 密钥生成失败" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[✓] 使用现有 SSH 密钥" -ForegroundColor Green
}

# 步骤 2: 显示公钥
Write-Host "`n步骤 2: 公钥内容" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
$publicKey = Get-Content $publicKeyPath -Raw
Write-Host $publicKey.Trim() -ForegroundColor White
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 步骤 3: 将公钥添加到服务器
Write-Host "`n步骤 3: 将公钥添加到服务器" -ForegroundColor Cyan
$addToServer = Read-Host "是否将公钥添加到服务器 ${ServerUser}@${ServerIP}？(Y/n)"

if ($addToServer -ne "n" -and $addToServer -ne "N") {
    Write-Host "正在使用 ssh-copy-id..." -ForegroundColor Yellow
    Write-Host "提示：需要输入服务器密码" -ForegroundColor Yellow
    Write-Host ""
    
    ssh-copy-id -i $publicKeyPath "${ServerUser}@${ServerIP}"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[✓] 公钥已添加到服务器" -ForegroundColor Green
    } else {
        Write-Host "[✗] ssh-copy-id 失败，请手动添加" -ForegroundColor Red
        Write-Host "`n手动添加步骤：" -ForegroundColor Yellow
        Write-Host "1. SSH 登录服务器: ssh ${ServerUser}@${ServerIP}" -ForegroundColor Gray
        Write-Host "2. 执行以下命令：" -ForegroundColor Gray
        Write-Host "   mkdir -p ~/.ssh" -ForegroundColor Gray
        Write-Host "   chmod 700 ~/.ssh" -ForegroundColor Gray
        Write-Host "   nano ~/.ssh/authorized_keys" -ForegroundColor Gray
        Write-Host "   （粘贴上面的公钥内容，保存退出）" -ForegroundColor Gray
        Write-Host "   chmod 600 ~/.ssh/authorized_keys" -ForegroundColor Gray
    }
}

# 步骤 4: 测试连接
Write-Host "`n步骤 4: 测试 SSH 连接" -ForegroundColor Cyan
$testResult = ssh -i $privateKeyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 "${ServerUser}@${ServerIP}" "echo 'SSH 连接成功！'" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[✓] SSH 连接测试成功！" -ForegroundColor Green
    Write-Host $testResult -ForegroundColor Green
} else {
    Write-Host "[✗] SSH 连接测试失败" -ForegroundColor Red
    Write-Host $testResult -ForegroundColor Red
}

# 步骤 5: 显示私钥内容
Write-Host "`n步骤 5: 添加到 GitHub Secrets" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. 打开：https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions" -ForegroundColor Yellow
Write-Host "2. 找到 SERVER_SSH_KEY，点击 Update" -ForegroundColor Yellow
Write-Host "3. 复制下面的私钥内容（完整内容，包括 -----BEGIN 和 -----END 行）：" -ForegroundColor Yellow
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
$privateKey = Get-Content $privateKeyPath -Raw
Write-Host $privateKey.Trim() -ForegroundColor White
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 尝试复制到剪贴板
try {
    $privateKey.Trim() | Set-Clipboard
    Write-Host "[✓] 私钥内容已复制到剪贴板" -ForegroundColor Green
} catch {
    Write-Host "[i] 无法自动复制到剪贴板，请手动复制" -ForegroundColor Gray
}

Write-Host "`n4. 确保其他 Secrets 正确配置：" -ForegroundColor Yellow
Write-Host "   - SERVER_HOST: $ServerIP" -ForegroundColor Gray
Write-Host "   - SERVER_USER: $ServerUser" -ForegroundColor Gray
Write-Host ""

Write-Host "[✓] 设置完成！" -ForegroundColor Green
