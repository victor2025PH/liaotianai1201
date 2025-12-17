# ============================================================
# 快速设置 SSH 密钥（Windows 专用）
# ============================================================

param(
    [string]$ServerIP = "165.154.254.24",
    [string]$ServerUser = "ubuntu"
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  快速设置 SSH 密钥" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$sshDir = "$env:USERPROFILE\.ssh"
$keyName = "github_deploy"
$privateKeyPath = "$sshDir\$keyName"
$publicKeyPath = "$sshDir\$keyName.pub"

# 步骤 1: 创建 .ssh 目录
Write-Host "[1/5] 创建 .ssh 目录..." -ForegroundColor Cyan
if (-not (Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    Write-Host "  [✓] 目录已创建: $sshDir" -ForegroundColor Green
} else {
    Write-Host "  [✓] 目录已存在: $sshDir" -ForegroundColor Green
}
Write-Host ""

# 步骤 2: 生成 SSH 密钥
Write-Host "[2/5] 生成 SSH 密钥..." -ForegroundColor Cyan
if (Test-Path $privateKeyPath) {
    Write-Host "  [!] 密钥已存在: $privateKeyPath" -ForegroundColor Yellow
    $overwrite = Read-Host "  是否覆盖？(y/N)"
    if ($overwrite -eq "y" -or $overwrite -eq "Y") {
        Remove-Item $privateKeyPath -Force -ErrorAction SilentlyContinue
        Remove-Item $publicKeyPath -Force -ErrorAction SilentlyContinue
    } else {
        Write-Host "  [i] 使用现有密钥" -ForegroundColor Gray
    }
}

if (-not (Test-Path $privateKeyPath)) {
    Write-Host "  提示：当询问密码时，直接按 Enter（不设置密码）" -ForegroundColor Yellow
    Write-Host ""
    ssh-keygen -t rsa -b 4096 -f $privateKeyPath -C "github-actions-deploy"
    
    if (Test-Path $privateKeyPath) {
        Write-Host "  [✓] 密钥生成成功" -ForegroundColor Green
    } else {
        Write-Host "  [✗] 密钥生成失败" -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# 步骤 3: 显示公钥
Write-Host "[3/5] 公钥内容：" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
$publicKey = Get-Content $publicKeyPath -Raw
Write-Host $publicKey.Trim() -ForegroundColor White
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 步骤 4: 添加到服务器
Write-Host "[4/5] 将公钥添加到服务器..." -ForegroundColor Cyan
$addKey = Read-Host "  是否添加到服务器 ${ServerUser}@${ServerIP}？(Y/n)"

if ($addKey -ne "n" -and $addKey -ne "N") {
    Write-Host "  提示：需要输入服务器密码" -ForegroundColor Yellow
    Write-Host ""
    
    # Windows 上使用 PowerShell 方式添加公钥（因为 ssh-copy-id 不可用）
    $publicKeyContent = Get-Content $publicKeyPath -Raw
    $remoteCommand = "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$($publicKeyContent.Trim())' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo 'KEY_ADDED'"
    
    Write-Host "  正在添加公钥到服务器..." -ForegroundColor Yellow
    $addResult = ssh "${ServerUser}@${ServerIP}" $remoteCommand 2>&1
    $addExitCode = $LASTEXITCODE
    
    if ($addExitCode -eq 0 -or $addResult -match "KEY_ADDED") {
        Write-Host "  [✓] 公钥已添加到服务器" -ForegroundColor Green
        
        # 等待一下让服务器处理
        Start-Sleep -Seconds 2
        
        # 测试连接
        Write-Host "  测试 SSH 连接..." -ForegroundColor Yellow
        $testResult = ssh -i $privateKeyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 "${ServerUser}@${ServerIP}" "echo '连接成功！'" 2>&1
        $testExitCode = $LASTEXITCODE
        
        if ($testExitCode -eq 0) {
            Write-Host "  [✓] SSH 连接测试成功！" -ForegroundColor Green
        } else {
            Write-Host "  [!] 连接测试失败（可能需要手动配置）" -ForegroundColor Yellow
            Write-Host $testResult -ForegroundColor Gray
        }
    } else {
        Write-Host "  [!] 自动添加失败，请手动添加" -ForegroundColor Yellow
        Write-Host "  手动步骤：" -ForegroundColor Yellow
        Write-Host "    1. SSH 登录: ssh ${ServerUser}@${ServerIP}" -ForegroundColor Gray
        Write-Host "    2. 执行: mkdir -p ~/.ssh && chmod 700 ~/.ssh" -ForegroundColor Gray
        Write-Host "    3. 执行: nano ~/.ssh/authorized_keys" -ForegroundColor Gray
        Write-Host "    4. 粘贴上面的公钥内容，保存退出（Ctrl+X, Y, Enter）" -ForegroundColor Gray
        Write-Host "    5. 执行: chmod 600 ~/.ssh/authorized_keys" -ForegroundColor Gray
    }
}
Write-Host ""

# 步骤 5: 显示私钥（用于 GitHub Secrets）
Write-Host "[5/5] 私钥内容（用于 GitHub Secrets）：" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
$privateKey = Get-Content $privateKeyPath -Raw
Write-Host $privateKey.Trim() -ForegroundColor White
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 复制到剪贴板
try {
    $privateKey.Trim() | Set-Clipboard
    Write-Host "[✓] 私钥已复制到剪贴板" -ForegroundColor Green
} catch {
    Write-Host "[i] 无法复制到剪贴板，请手动复制" -ForegroundColor Gray
}

Write-Host "`n下一步：" -ForegroundColor Cyan
Write-Host "1. 打开：https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions" -ForegroundColor Yellow
Write-Host "2. 找到 SERVER_SSH_KEY，点击 Update" -ForegroundColor Yellow
Write-Host "3. 粘贴上面的私钥内容（完整内容）" -ForegroundColor Yellow
Write-Host "4. 确保 SERVER_HOST = $ServerIP" -ForegroundColor Yellow
Write-Host "5. 确保 SERVER_USER = $ServerUser" -ForegroundColor Yellow
Write-Host ""

Write-Host "[✓] 完成！" -ForegroundColor Green
