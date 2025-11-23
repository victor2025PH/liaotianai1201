# 将本地 .env 文件中的 Telegram API 配置同步到远程服务器
param(
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Continue"
Import-Module Posh-SSH

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  同步环境变量到远程服务器" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 检查本地 .env 文件
$localEnvFile = ".env"
if (-not (Test-Path $localEnvFile)) {
    Write-Host "✗ 本地 .env 文件不存在: $localEnvFile" -ForegroundColor Red
    Write-Host "请先创建 .env 文件并配置 Telegram API 凭证" -ForegroundColor Yellow
    exit 1
}

Write-Host "读取本地 .env 文件..." -ForegroundColor Yellow
$envContent = Get-Content $localEnvFile -Raw

# 提取 Telegram API 配置
$apiId = $null
$apiHash = $null
$sessionName = $null
$openaiKey = $null

if ($envContent -match "TELEGRAM_API_ID\s*=\s*(\d+)") {
    $apiId = $matches[1]
    Write-Host "  ✓ TELEGRAM_API_ID: $apiId" -ForegroundColor Green
} else {
    Write-Host "  ✗ 未找到 TELEGRAM_API_ID" -ForegroundColor Red
}

if ($envContent -match "TELEGRAM_API_HASH\s*=\s*([^\r\n]+)") {
    $apiHash = $matches[1].Trim()
    Write-Host "  ✓ TELEGRAM_API_HASH: $($apiHash.Substring(0, [Math]::Min(20, $apiHash.Length)))..." -ForegroundColor Green
} else {
    Write-Host "  ✗ 未找到 TELEGRAM_API_HASH" -ForegroundColor Red
}

if ($envContent -match "TELEGRAM_SESSION_NAME\s*=\s*([^\r\n]+)") {
    $sessionName = $matches[1].Trim()
    Write-Host "  ✓ TELEGRAM_SESSION_NAME: $sessionName" -ForegroundColor Green
} else {
    Write-Host "  ✗ 未找到 TELEGRAM_SESSION_NAME" -ForegroundColor Red
}

if ($envContent -match "OPENAI_API_KEY\s*=\s*([^\r\n]+)") {
    $openaiKey = $matches[1].Trim()
    Write-Host "  ✓ OPENAI_API_KEY: $($openaiKey.Substring(0, [Math]::Min(20, $openaiKey.Length)))..." -ForegroundColor Green
} else {
    Write-Host "  ✗ 未找到 OPENAI_API_KEY" -ForegroundColor Red
}

if (-not $apiId -or -not $apiHash -or -not $sessionName) {
    Write-Host "`n✗ 缺少必要的 Telegram API 配置" -ForegroundColor Red
    Write-Host "请在 .env 文件中配置以下变量:" -ForegroundColor Yellow
    Write-Host "  - TELEGRAM_API_ID" -ForegroundColor Yellow
    Write-Host "  - TELEGRAM_API_HASH" -ForegroundColor Yellow
    Write-Host "  - TELEGRAM_SESSION_NAME" -ForegroundColor Yellow
    exit 1
}

$servers = @(
    @{IP="165.154.255.48"; Name="洛杉矶"; Pass="8iDcGrYb52Fxpzee"},
    @{IP="165.154.233.179"; Name="马尼拉"; Pass="8iDcGrYb52Fxpzee"},
    @{IP="165.154.254.99"; Name="worker-01"; Pass="Along2025!!!"}
)

foreach ($s in $servers) {
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host "服务器: $($s.Name) ($($s.IP))" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    
    try {
        $pass = ConvertTo-SecureString $s.Pass -AsPlainText -Force
        $cred = New-Object System.Management.Automation.PSCredential("ubuntu", $pass)
        $session = New-SSHSession -ComputerName $s.IP -Credential $cred -AcceptKey -ErrorAction Stop
        
        Write-Host "✓ SSH 连接成功" -ForegroundColor Green
        Write-Host ""
        
        if ($DryRun) {
            Write-Host "[DRY RUN] 将更新以下配置:" -ForegroundColor Yellow
            Write-Host "  TELEGRAM_API_ID=$apiId" -ForegroundColor Gray
            Write-Host "  TELEGRAM_API_HASH=$($apiHash.Substring(0, [Math]::Min(20, $apiHash.Length)))..." -ForegroundColor Gray
            Write-Host "  TELEGRAM_SESSION_NAME=$sessionName" -ForegroundColor Gray
            if ($openaiKey) {
                Write-Host "  OPENAI_API_KEY=$($openaiKey.Substring(0, [Math]::Min(20, $openaiKey.Length)))..." -ForegroundColor Gray
            }
        } else {
            # 读取远程 .env 文件（如果存在）
            Write-Host "读取远程 .env 文件..." -ForegroundColor Cyan
            $r1 = Invoke-SSHCommand -SessionId $session.SessionId -Command "test -f /home/ubuntu/.env && cat /home/ubuntu/.env || echo ''"
            $remoteEnvContent = $r1.Output
            
            # 更新或添加 Telegram API 配置
            $lines = @()
            $updated = $false
            
            if ($remoteEnvContent) {
                $lines = $remoteEnvContent -split "`n"
                $newLines = @()
                
                foreach ($line in $lines) {
                    if ($line -match "^TELEGRAM_API_ID\s*=") {
                        $newLines += "TELEGRAM_API_ID=$apiId"
                        $updated = $true
                    } elseif ($line -match "^TELEGRAM_API_HASH\s*=") {
                        $newLines += "TELEGRAM_API_HASH=$apiHash"
                        $updated = $true
                    } elseif ($line -match "^TELEGRAM_SESSION_NAME\s*=") {
                        $newLines += "TELEGRAM_SESSION_NAME=$sessionName"
                        $updated = $true
                    } elseif ($line -match "^OPENAI_API_KEY\s*=" -and $openaiKey) {
                        $newLines += "OPENAI_API_KEY=$openaiKey"
                        $updated = $true
                    } else {
                        $newLines += $line
                    }
                }
                
                $lines = $newLines
            }
            
            # 如果变量不存在，添加到文件末尾
            $hasApiId = $lines | Where-Object { $_ -match "^TELEGRAM_API_ID\s*=" }
            $hasApiHash = $lines | Where-Object { $_ -match "^TELEGRAM_API_HASH\s*=" }
            $hasSessionName = $lines | Where-Object { $_ -match "^TELEGRAM_SESSION_NAME\s*=" }
            $hasOpenaiKey = $lines | Where-Object { $_ -match "^OPENAI_API_KEY\s*=" }
            
            if (-not $hasApiId) {
                $lines += "TELEGRAM_API_ID=$apiId"
                $updated = $true
            }
            if (-not $hasApiHash) {
                $lines += "TELEGRAM_API_HASH=$apiHash"
                $updated = $true
            }
            if (-not $hasSessionName) {
                $lines += "TELEGRAM_SESSION_NAME=$sessionName"
                $updated = $true
            }
            if (-not $hasOpenaiKey -and $openaiKey) {
                $lines += "OPENAI_API_KEY=$openaiKey"
                $updated = $true
            }
            
            if ($updated) {
                Write-Host "更新远程 .env 文件..." -ForegroundColor Cyan
                $envContentToWrite = $lines -join "`n"
                
                # 使用 here-doc 写入文件
                $updateScript = @"
cat > /home/ubuntu/.env << 'ENVEOF'
$envContentToWrite
ENVEOF
"@
                $r2 = Invoke-SSHCommand -SessionId $session.SessionId -Command $updateScript
                Write-Host "  ✓ .env 文件已更新" -ForegroundColor Green
                
                # 验证更新
                Write-Host "验证配置..." -ForegroundColor Cyan
                $r3 = Invoke-SSHCommand -SessionId $session.SessionId -Command "grep -E '^TELEGRAM_API_ID|^TELEGRAM_API_HASH|^TELEGRAM_SESSION_NAME' /home/ubuntu/.env"
                Write-Host $r3.Output -ForegroundColor Gray
            } else {
                Write-Host "  ✓ 配置已是最新" -ForegroundColor Green
            }
        }
        
        Remove-SSHSession -SessionId $session.SessionId | Out-Null
        
    } catch {
        Write-Host "✗ SSH 连接失败: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
}

if (-not $DryRun) {
    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "  环境变量同步完成" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "下一步: 运行脚本启动 main.py" -ForegroundColor Yellow
    Write-Host "  pwsh -ExecutionPolicy Bypass -File scripts\fix_and_start_remote_main.ps1 -StartMain" -ForegroundColor Gray
}

