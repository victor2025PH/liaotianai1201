# ============================================================
# GitHub Actions SSH Key 设置脚本（简化版）
# ============================================================
# 
# 功能：生成 SSH 密钥并显示配置说明
# 
# 使用方法：
#   .\scripts\local\setup-github-actions-ssh-simple.ps1
# ============================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "10.56.61.200",
    
    [Parameter(Mandatory=$false)]
    [string]$ServerUser = "deployer"
)

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GitHub Actions SSH Key 设置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取 SSH 目录路径
$sshDir = Join-Path $env:USERPROFILE ".ssh"
$keyName = "github_deploy"
$privateKeyPath = Join-Path $sshDir $keyName
$publicKeyPath = "$privateKeyPath.pub"

# 步骤 1: 检查/创建 .ssh 目录
Write-Host "[步骤 1] 检查 .ssh 目录..." -ForegroundColor Yellow
if (-not (Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    Write-Host "  [OK] .ssh 目录已创建" -ForegroundColor Green
} else {
    Write-Host "  [OK] .ssh 目录已存在" -ForegroundColor Green
}
Write-Host ""

# 步骤 2: 检查现有密钥
Write-Host "[步骤 2] 检查现有密钥..." -ForegroundColor Yellow
if (Test-Path $privateKeyPath) {
    Write-Host "  [警告] 密钥已存在: $privateKeyPath" -ForegroundColor Yellow
    $overwrite = Read-Host "  是否覆盖现有密钥？(y/N)"
    if ($overwrite -eq "y" -or $overwrite -eq "Y") {
        Remove-Item $privateKeyPath -Force -ErrorAction SilentlyContinue
        Remove-Item $publicKeyPath -Force -ErrorAction SilentlyContinue
        Write-Host "  [OK] 已删除旧密钥" -ForegroundColor Green
    } else {
        Write-Host "  [信息] 使用现有密钥" -ForegroundColor Gray
    }
}
Write-Host ""

# 步骤 3: 生成 SSH 密钥
Write-Host "[步骤 3] 生成 SSH 密钥对..." -ForegroundColor Yellow
if (-not (Test-Path $privateKeyPath)) {
    Write-Host "  正在生成密钥，请稍候..." -ForegroundColor Gray
    
    # 使用更简单的方法生成密钥
    $keygenCommand = "ssh-keygen -t rsa -b 4096 -f `"$privateKeyPath`" -N `"`" -C `"github-actions-deploy`" -q"
    
    # 执行命令
    $null = Invoke-Expression $keygenCommand
    
    if (Test-Path $privateKeyPath) {
        Write-Host "  [OK] SSH 密钥对生成成功" -ForegroundColor Green
    } else {
        Write-Host "  [错误] SSH 密钥生成失败" -ForegroundColor Red
        Write-Host "  请手动运行以下命令：" -ForegroundColor Yellow
        Write-Host "    ssh-keygen -t rsa -b 4096 -f `"$privateKeyPath`" -N `"`" -C `"github-actions-deploy`"" -ForegroundColor Cyan
        exit 1
    }
} else {
    Write-Host "  [OK] 使用现有密钥" -ForegroundColor Green
}
Write-Host ""

# 步骤 4: 读取公钥
Write-Host "[步骤 4] 读取公钥内容..." -ForegroundColor Yellow
if (-not (Test-Path $publicKeyPath)) {
    Write-Host "  [错误] 公钥文件不存在" -ForegroundColor Red
    exit 1
}

$publicKeyContent = Get-Content $publicKeyPath -Raw
Write-Host "  [OK] 公钥已读取" -ForegroundColor Green
Write-Host ""

# 步骤 5: 显示配置说明
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  下一步操作" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "1. 将公钥添加到服务器：" -ForegroundColor Cyan
Write-Host ""
Write-Host "   方法 A（自动，需要密码）：" -ForegroundColor Gray
Write-Host "   ssh $ServerUser@$ServerIP `"mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$($publicKeyContent.Trim())' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys`"" -ForegroundColor White
Write-Host ""
Write-Host "   方法 B（手动）：" -ForegroundColor Gray
Write-Host "   1) 复制下面的公钥内容" -ForegroundColor Gray
Write-Host "   2) SSH 登录服务器: ssh $ServerUser@$ServerIP" -ForegroundColor Gray
Write-Host "   3) 执行: mkdir -p ~/.ssh && chmod 700 ~/.ssh" -ForegroundColor Gray
Write-Host "   4) 执行: nano ~/.ssh/authorized_keys" -ForegroundColor Gray
Write-Host "   5) 粘贴公钥内容，保存退出（Ctrl+X, Y, Enter）" -ForegroundColor Gray
Write-Host "   6) 执行: chmod 600 ~/.ssh/authorized_keys" -ForegroundColor Gray
Write-Host ""

Write-Host "   公钥内容：" -ForegroundColor Yellow
Write-Host $publicKeyContent.Trim() -ForegroundColor White -BackgroundColor DarkBlue
Write-Host ""

Write-Host "2. 将私钥添加到 GitHub Secrets：" -ForegroundColor Cyan
Write-Host ""
Write-Host "   打开: https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions" -ForegroundColor Cyan
Write-Host ""
Write-Host "   添加以下 Secrets：" -ForegroundColor Yellow
Write-Host "   - SERVER_SSH_KEY: (下面的私钥内容)" -ForegroundColor Gray
Write-Host "   - SERVER_HOST: $ServerIP" -ForegroundColor Gray
Write-Host "   - SERVER_USER: $ServerUser" -ForegroundColor Gray
Write-Host ""

Write-Host "   私钥内容（复制以下全部内容）：" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green

$privateKeyContent = Get-Content $privateKeyPath -Raw
Write-Host $privateKeyContent.Trim() -ForegroundColor White -BackgroundColor DarkBlue
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 尝试复制到剪贴板
try {
    $privateKeyContent.Trim() | Set-Clipboard
    Write-Host "  [OK] 私钥内容已复制到剪贴板" -ForegroundColor Green
} catch {
    Write-Host "  [警告] 无法自动复制到剪贴板，请手动复制" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "3. 测试 SSH 连接：" -ForegroundColor Cyan
Write-Host "   ssh -i `"$privateKeyPath`" $ServerUser@$ServerIP `"echo 'SSH 密钥认证成功'`"" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
