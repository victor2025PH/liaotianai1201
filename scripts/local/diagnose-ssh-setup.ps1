# ============================================================
# SSH 设置诊断脚本
# ============================================================

param(
    [string]$ServerIP = "165.154.254.24",
    [string]$ServerUser = "ubuntu",
    [string]$KeyName = "github_deploy"
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SSH 设置诊断" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$sshDir = "$env:USERPROFILE\.ssh"
$privateKeyPath = "$sshDir\$KeyName"
$publicKeyPath = "$sshDir\$KeyName.pub"

$errors = @()
$warnings = @()

# 1. 检查密钥文件
Write-Host "[1/6] 检查本地密钥文件..." -ForegroundColor Cyan
if (Test-Path $privateKeyPath) {
    Write-Host "  [✓] 私钥文件存在: $privateKeyPath" -ForegroundColor Green
    $privateKeySize = (Get-Item $privateKeyPath).Length
    Write-Host "  [i] 私钥大小: $privateKeySize 字节" -ForegroundColor Gray
} else {
    Write-Host "  [✗] 私钥文件不存在: $privateKeyPath" -ForegroundColor Red
    $errors += "私钥文件不存在"
}

if (Test-Path $publicKeyPath) {
    Write-Host "  [✓] 公钥文件存在: $publicKeyPath" -ForegroundColor Green
    $publicKey = Get-Content $publicKeyPath -Raw
    Write-Host "  [i] 公钥内容:" -ForegroundColor Gray
    Write-Host $publicKey.Trim() -ForegroundColor White
} else {
    Write-Host "  [✗] 公钥文件不存在: $publicKeyPath" -ForegroundColor Red
    $errors += "公钥文件不存在"
}
Write-Host ""

# 2. 检查私钥格式
Write-Host "[2/6] 检查私钥格式..." -ForegroundColor Cyan
if (Test-Path $privateKeyPath) {
    $privateKey = Get-Content $privateKeyPath -Raw
    
    if ($privateKey -match "-----BEGIN.*PRIVATE KEY-----") {
        Write-Host "  [✓] 私钥格式正确（包含 BEGIN 标记）" -ForegroundColor Green
    } else {
        Write-Host "  [✗] 私钥格式错误（缺少 BEGIN 标记）" -ForegroundColor Red
        $errors += "私钥格式错误"
    }
    
    if ($privateKey -match "-----END.*PRIVATE KEY-----") {
        Write-Host "  [✓] 私钥格式正确（包含 END 标记）" -ForegroundColor Green
    } else {
        Write-Host "  [✗] 私钥格式错误（缺少 END 标记）" -ForegroundColor Red
        $errors += "私钥格式错误"
    }
    
    # 检查行数（应该是多行的）
    $lines = ($privateKey -split "`n").Count
    if ($lines -gt 1) {
        Write-Host "  [✓] 私钥包含多行（$lines 行）" -ForegroundColor Green
    } else {
        Write-Host "  [✗] 私钥只有一行，可能格式错误" -ForegroundColor Red
        $errors += "私钥格式可能错误（应该有多行）"
    }
    
    # 检查是否有 Windows 换行符问题
    if ($privateKey -match "`r`n") {
        Write-Host "  [i] 使用 Windows 换行符（CRLF）" -ForegroundColor Yellow
        $warnings += "私钥使用 Windows 换行符，GitHub Actions 可能需要 LF"
    }
} else {
    Write-Host "  [!] 无法检查私钥格式（文件不存在）" -ForegroundColor Yellow
}
Write-Host ""

# 3. 测试本地 SSH 连接
Write-Host "[3/6] 测试本地 SSH 连接..." -ForegroundColor Cyan
if (Test-Path $privateKeyPath) {
    Write-Host "  正在测试连接..." -ForegroundColor Yellow
    $testResult = ssh -i $privateKeyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 "${ServerUser}@${ServerIP}" "echo 'SSH_TEST_SUCCESS'" 2>&1
    $testExitCode = $LASTEXITCODE
    
    if ($testExitCode -eq 0 -and $testResult -match "SSH_TEST_SUCCESS") {
        Write-Host "  [✓] 本地 SSH 连接成功！" -ForegroundColor Green
        Write-Host "  [i] 输出: $testResult" -ForegroundColor Gray
    } else {
        Write-Host "  [✗] 本地 SSH 连接失败" -ForegroundColor Red
        Write-Host "  [i] 退出码: $testExitCode" -ForegroundColor Gray
        Write-Host "  [i] 输出: $testResult" -ForegroundColor Gray
        $errors += "本地 SSH 连接失败"
    }
} else {
    Write-Host "  [!] 无法测试（私钥文件不存在）" -ForegroundColor Yellow
}
Write-Host ""

# 4. 检查服务器上的 authorized_keys
Write-Host "[4/6] 检查服务器上的 authorized_keys..." -ForegroundColor Cyan
if (Test-Path $publicKeyPath) {
    $publicKey = Get-Content $publicKeyPath -Raw
    $publicKeyTrimmed = $publicKey.Trim()
    
    Write-Host "  正在检查服务器..." -ForegroundColor Yellow
    $checkCmd = "grep -F '$($publicKeyTrimmed)' ~/.ssh/authorized_keys 2>/dev/null && echo 'KEY_FOUND' || echo 'KEY_NOT_FOUND'"
    $checkResult = ssh "${ServerUser}@${ServerIP}" $checkCmd 2>&1
    $checkExitCode = $LASTEXITCODE
    
    if ($checkResult -match "KEY_FOUND") {
        Write-Host "  [✓] 公钥已存在于服务器的 authorized_keys" -ForegroundColor Green
    } elseif ($checkResult -match "KEY_NOT_FOUND") {
        Write-Host "  [✗] 公钥未在服务器的 authorized_keys 中找到" -ForegroundColor Red
        $errors += "服务器上未找到公钥"
    } else {
        Write-Host "  [!] 无法检查服务器（可能需要密码）" -ForegroundColor Yellow
        Write-Host "  [i] 输出: $checkResult" -ForegroundColor Gray
        $warnings += "无法检查服务器上的 authorized_keys"
    }
} else {
    Write-Host "  [!] 无法检查（公钥文件不存在）" -ForegroundColor Yellow
}
Write-Host ""

# 5. 显示用于 GitHub Secrets 的私钥内容
Write-Host "[5/6] 生成用于 GitHub Secrets 的私钥..." -ForegroundColor Cyan
if (Test-Path $privateKeyPath) {
    $privateKey = Get-Content $privateKeyPath -Raw
    
    # 转换为 Unix 换行符（GitHub Actions 需要 LF，不是 CRLF）
    $privateKeyUnix = $privateKey -replace "`r`n", "`n" -replace "`r", "`n"
    
    Write-Host "  [i] 以下私钥内容（已转换为 Unix 格式）应该复制到 GitHub Secrets:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host $privateKeyUnix.Trim() -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # 尝试复制到剪贴板
    try {
        $privateKeyUnix.Trim() | Set-Clipboard
        Write-Host "  [✓] 私钥内容已复制到剪贴板（Unix 格式）" -ForegroundColor Green
    } catch {
        Write-Host "  [i] 无法复制到剪贴板，请手动复制" -ForegroundColor Gray
    }
    
    Write-Host "  重要提示：" -ForegroundColor Yellow
    Write-Host "    1. 复制上面的完整内容（包括 -----BEGIN 和 -----END 行）" -ForegroundColor Gray
    Write-Host "    2. 在 GitHub Secrets 中粘贴时，确保换行符正确" -ForegroundColor Gray
    Write-Host "    3. 如果仍然失败，尝试从文件直接读取：cat $privateKeyPath" -ForegroundColor Gray
} else {
    Write-Host "  [✗] 私钥文件不存在" -ForegroundColor Red
}
Write-Host ""

# 6. 诊断总结
Write-Host "[6/6] 诊断总结..." -ForegroundColor Cyan
Write-Host ""

if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "  [✓] 所有检查通过！" -ForegroundColor Green
    Write-Host ""
    Write-Host "如果 GitHub Actions 仍然失败，请检查：" -ForegroundColor Yellow
    Write-Host "  1. GitHub Secrets 中的私钥是否正确（完整复制，包括 BEGIN/END）" -ForegroundColor Gray
    Write-Host "  2. SERVER_HOST 是否正确: $ServerIP" -ForegroundColor Gray
    Write-Host "  3. SERVER_USER 是否正确: $ServerUser" -ForegroundColor Gray
    Write-Host "  4. 服务器防火墙是否允许 SSH 连接（端口 22）" -ForegroundColor Gray
    Write-Host "  5. GitHub Actions 日志中的详细错误信息" -ForegroundColor Gray
} else {
    if ($errors.Count -gt 0) {
        Write-Host "  [✗] 发现 $($errors.Count) 个错误：" -ForegroundColor Red
        foreach ($error in $errors) {
            Write-Host "    - $error" -ForegroundColor Red
        }
        Write-Host ""
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "  [!] 发现 $($warnings.Count) 个警告：" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "    - $warning" -ForegroundColor Yellow
        }
        Write-Host ""
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  下一步操作" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 打开 GitHub Secrets 页面：" -ForegroundColor Yellow
Write-Host "   https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. 确保以下 Secrets 已配置：" -ForegroundColor Yellow
Write-Host "   - SERVER_SSH_KEY: （使用上面显示的私钥内容）" -ForegroundColor Gray
Write-Host "   - SERVER_HOST: $ServerIP" -ForegroundColor Gray
Write-Host "   - SERVER_USER: $ServerUser" -ForegroundColor Gray
Write-Host ""
Write-Host "3. 测试 GitHub Actions 部署" -ForegroundColor Yellow
Write-Host ""
