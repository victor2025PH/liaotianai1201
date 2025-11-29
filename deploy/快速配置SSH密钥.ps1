# SSH 密钥快速配置脚本
# 在 PowerShell 中执行：.\deploy\快速配置SSH密钥.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "配置 SSH 密钥认证" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 步骤 1: 检查是否已有密钥
Write-Host "[步骤 1/4] 检查是否已有 SSH 密钥..." -ForegroundColor Yellow
$pubKeyPath = "$env:USERPROFILE\.ssh\id_rsa.pub"

if (Test-Path $pubKeyPath) {
    Write-Host "[OK] 发现现有 SSH 公钥" -ForegroundColor Green
    Write-Host ""
    Write-Host "公钥内容：" -ForegroundColor Cyan
    Get-Content $pubKeyPath
    Write-Host ""
} else {
    Write-Host "[信息] 未发现 SSH 公钥，正在生成..." -ForegroundColor Yellow
    Write-Host ""
    
    # 创建 .ssh 目录
    if (!(Test-Path "$env:USERPROFILE\.ssh")) {
        New-Item -ItemType Directory -Path "$env:USERPROFILE\.ssh" -Force | Out-Null
    }
    
    # 生成密钥
    $keygenCmd = "ssh-keygen -t rsa -b 4096 -f `"$env:USERPROFILE\.ssh\id_rsa`" -N '""'"
    Invoke-Expression $keygenCmd
    
    if (Test-Path $pubKeyPath) {
        Write-Host "[OK] SSH 密钥对已生成" -ForegroundColor Green
        Write-Host ""
        Write-Host "公钥内容：" -ForegroundColor Cyan
        Get-Content $pubKeyPath
        Write-Host ""
    } else {
        Write-Host "[错误] 密钥生成失败" -ForegroundColor Red
        exit 1
    }
}

# 步骤 2: 将公钥复制到服务器
Write-Host "[步骤 2/4] 将公钥复制到服务器..." -ForegroundColor Yellow
Write-Host "注意：需要输入一次服务器密码" -ForegroundColor Yellow
Write-Host ""

$copyCmd = "type `"$pubKeyPath`" | ssh ubuntu@165.154.233.55 `"mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys`""
Write-Host "执行命令（需要输入密码）：" -ForegroundColor Cyan
Write-Host $copyCmd -ForegroundColor Gray
Write-Host ""

Invoke-Expression $copyCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 公钥复制失败" -ForegroundColor Red
    Write-Host ""
    Write-Host "请手动执行以下步骤：" -ForegroundColor Yellow
    Write-Host "1. 复制上面的公钥内容" -ForegroundColor White
    Write-Host "2. 登录服务器：ssh ubuntu@165.154.233.55" -ForegroundColor White
    Write-Host "3. 执行：" -ForegroundColor White
    Write-Host "   mkdir -p ~/.ssh" -ForegroundColor Gray
    Write-Host "   chmod 700 ~/.ssh" -ForegroundColor Gray
    Write-Host "   nano ~/.ssh/authorized_keys" -ForegroundColor Gray
    Write-Host "4. 粘贴公钥内容，保存退出" -ForegroundColor White
    Write-Host "5. 执行：chmod 600 ~/.ssh/authorized_keys" -ForegroundColor Gray
    exit 1
}

Write-Host "[OK] 公钥已复制到服务器" -ForegroundColor Green
Write-Host ""

# 步骤 3: 测试无密码登录
Write-Host "[步骤 3/4] 测试无密码登录..." -ForegroundColor Yellow
Write-Host ""

$testCmd = 'ssh -o BatchMode=yes -o ConnectTimeout=5 ubuntu@165.154.233.55 "echo `"SSH 密钥认证测试成功！`""'
$testResult = Invoke-Expression $testCmd 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] SSH 密钥认证配置成功！" -ForegroundColor Green
    Write-Host $testResult -ForegroundColor Green
} else {
    Write-Host "[警告] 无密码登录测试失败" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "可能原因：服务器权限设置不正确" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "请在服务器上执行：" -ForegroundColor Cyan
    Write-Host "  chmod 700 ~/.ssh" -ForegroundColor Gray
    Write-Host "  chmod 600 ~/.ssh/authorized_keys" -ForegroundColor Gray
    Write-Host ""
    Write-Host "然后再次运行此脚本测试" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# 步骤 4: 验证配置
Write-Host "[步骤 4/4] 验证配置..." -ForegroundColor Yellow
Write-Host ""

Write-Host "测试执行远程命令（应该不需要密码）：" -ForegroundColor Cyan
ssh ubuntu@165.154.233.55 "whoami && pwd && echo 'SSH 密钥认证工作正常！'"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "配置完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "现在可以无密码执行 SSH 命令了" -ForegroundColor Green
Write-Host "可以运行自动化脚本：" -ForegroundColor Yellow
Write-Host "  - deploy\一键修复WebSocket连接.bat" -ForegroundColor Gray
Write-Host "  - deploy\一键检查WebSocket配置.bat" -ForegroundColor Gray
Write-Host ""

