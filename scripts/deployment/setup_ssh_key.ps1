# SSH密鑰配置腳本
# 用於將本地SSH公鑰複製到遠程服務器

param(
    [string]$ConfigPath = "data/master_config.json"
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SSH密鑰配置工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 讀取配置
Write-Host "[初始化] 讀取配置文件..." -ForegroundColor Yellow
if (-not (Test-Path $ConfigPath)) {
    Write-Host "✗ 配置文件不存在: $ConfigPath" -ForegroundColor Red
    exit 1
}

$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
$servers = $config.servers

if ($null -eq $servers -or $servers.Count -eq 0) {
    Write-Host "✗ 未找到服務器配置" -ForegroundColor Red
    exit 1
}

# 檢查SSH公鑰
Write-Host "[檢查] 查找SSH公鑰..." -ForegroundColor Yellow

$publicKeyPath = "$env:USERPROFILE\.ssh\id_rsa.pub"
if (-not (Test-Path $publicKeyPath)) {
    $publicKeyPath = "$env:USERPROFILE\.ssh\id_ed25519.pub"
    if (-not (Test-Path $publicKeyPath)) {
        Write-Host "✗ 未找到SSH公鑰文件" -ForegroundColor Red
        Write-Host "  請先生成SSH密鑰：ssh-keygen -t rsa -b 4096" -ForegroundColor Yellow
        exit 1
    }
}

$publicKey = Get-Content $publicKeyPath -Raw
Write-Host "✓ 找到SSH公鑰: $publicKeyPath" -ForegroundColor Green
Write-Host "  公鑰內容: $($publicKey.Substring(0, [Math]::Min(50, $publicKey.Length)))..." -ForegroundColor Gray
Write-Host ""

# 處理每個服務器
foreach ($nodeId in $servers.PSObject.Properties.Name) {
    $server = $servers.$nodeId
    $remoteHost = $server.host
    $user = $server.user
    $password = $server.password
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  配置節點: $nodeId" -ForegroundColor Cyan
    Write-Host "  主機: $remoteHost" -ForegroundColor Cyan
    Write-Host "  用戶: $user" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "[步驟 1/3] 測試SSH連接..." -ForegroundColor Yellow
    
    # 測試SSH連接
    $testResult = Test-NetConnection -ComputerName $remoteHost -Port 22 -InformationLevel Quiet -WarningAction SilentlyContinue
    if (-not $testResult) {
        Write-Host "✗ 無法連接到 $remoteHost:22" -ForegroundColor Red
        Write-Host "  請檢查：網絡連接、防火牆設置、主機是否在線" -ForegroundColor Yellow
        continue
    }
    
    Write-Host "✓ SSH端口可達" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "[步驟 2/3] 複製SSH公鑰到遠程服務器..." -ForegroundColor Yellow
    Write-Host "  注意：此步驟需要輸入遠程服務器密碼" -ForegroundColor Gray
    Write-Host ""
    
    # 方法1：嘗試使用 ssh-copy-id（如果可用）
    $sshCopyId = Get-Command ssh-copy-id -ErrorAction SilentlyContinue
    if ($sshCopyId) {
        Write-Host "  使用 ssh-copy-id..." -ForegroundColor Gray
        $copyCmd = "ssh-copy-id -o StrictHostKeyChecking=no ${user}@${remoteHost}"
        Invoke-Expression $copyCmd
    } else {
        # 方法2：手動複製（使用臨時腳本）
        Write-Host "  使用SSH手動複製..." -ForegroundColor Gray
        
        # 方法：直接使用SSH命令複製公鑰
        Write-Host "  請手動執行以下步驟：" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  1. 複製SSH公鑰內容：" -ForegroundColor Yellow
        Write-Host "     $publicKey" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  2. 登錄到遠程服務器（需要輸入密碼）：" -ForegroundColor Yellow
        Write-Host "     ssh ${user}@${remoteHost}" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  3. 在遠程服務器上執行以下命令：" -ForegroundColor Yellow
        Write-Host "     mkdir -p ~/.ssh" -ForegroundColor Gray
        Write-Host "     chmod 700 ~/.ssh" -ForegroundColor Gray
        Write-Host "     nano ~/.ssh/authorized_keys" -ForegroundColor Gray
        Write-Host "     （將公鑰內容粘貼到文件中，保存退出）" -ForegroundColor Gray
        Write-Host "     chmod 600 ~/.ssh/authorized_keys" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  或使用一條命令（需要輸入密碼）：" -ForegroundColor Yellow
        Write-Host "     ssh ${user}@${remoteHost} \"mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$publicKey' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys\"" -ForegroundColor Gray
        Write-Host ""
        
        # 嘗試自動執行
        Write-Host "  正在嘗試自動複製..." -ForegroundColor Yellow
        $command = "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$publicKey' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo 'SUCCESS'"
        
        try {
            Write-Host "  執行SSH命令（需要輸入密碼）..." -ForegroundColor Gray
            $result = ssh -o StrictHostKeyChecking=no ${user}@${remoteHost} $command 2>&1
            
            $resultString = $result | Out-String
            if ($resultString -match "SUCCESS") {
                Write-Host "✓ SSH公鑰複製成功！" -ForegroundColor Green
            } else {
                Write-Host "⚠ 執行結果: $resultString" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "✗ 複製失敗: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host ""
            Write-Host "  手動複製步驟：" -ForegroundColor Yellow
            Write-Host "  1. 複製以下公鑰內容：" -ForegroundColor Yellow
            Write-Host "     $publicKey" -ForegroundColor Gray
            Write-Host ""
            Write-Host "  2. 登錄到遠程服務器：" -ForegroundColor Yellow
            Write-Host "     ssh ${user}@${remoteHost}" -ForegroundColor Gray
            Write-Host ""
            Write-Host "  3. 執行以下命令：" -ForegroundColor Yellow
            Write-Host "     mkdir -p ~/.ssh" -ForegroundColor Gray
            Write-Host "     chmod 700 ~/.ssh" -ForegroundColor Gray
            Write-Host "     echo '$publicKey' >> ~/.ssh/authorized_keys" -ForegroundColor Gray
            Write-Host "     chmod 600 ~/.ssh/authorized_keys" -ForegroundColor Gray
        }
    }
    
    Write-Host ""
    Write-Host "[步驟 3/3] 測試SSH密鑰認證..." -ForegroundColor Yellow
    
    # 測試SSH連接（應該不需要密碼）
    $testCmd = "ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes ${user}@${remoteHost} 'echo SSH密鑰認證成功' 2>&1"
    
    try {
        $testOutput = Invoke-Expression $testCmd 2>&1
        $testOutputString = $testOutput | Out-String
        
        if ($testOutputString -match "SSH密鑰認證成功") {
            Write-Host "✓ SSH密鑰認證成功！" -ForegroundColor Green
            Write-Host "  現在可以使用診斷腳本而不需要輸入密碼" -ForegroundColor Green
        } elseif ($testOutputString -match "Permission denied|Host key verification failed") {
            Write-Host "⚠ SSH密鑰認證可能未完全配置" -ForegroundColor Yellow
            Write-Host "  輸出: $testOutputString" -ForegroundColor Gray
            Write-Host "  請檢查遠程服務器的 ~/.ssh/authorized_keys 文件" -ForegroundColor Yellow
        } else {
            Write-Host "⚠ 測試結果: $testOutputString" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠ 測試時出現問題: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "  可能需要手動測試SSH連接" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SSH密鑰配置完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "  運行診斷腳本: pwsh -ExecutionPolicy Bypass -File scripts\deployment\diagnose_and_fix_service.ps1" -ForegroundColor Gray

