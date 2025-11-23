# 服務診斷與修復腳本
# 用於診斷和修復 group-ai-worker 服務啟動失敗問題
#
# 改進說明：
# - 為所有遠程命令添加超時控制，避免長時間阻塞
# - 添加詳細的進度日誌輸出
# - 增強錯誤處理和異常捕獲
# - 為長時間運行的命令（如 pip install）設置更長的超時時間

param(
    [string]$ConfigPath = "data/master_config.json",
    [string]$ServiceName = "group-ai-worker",
    [int]$DefaultTimeoutSeconds = 30,      # 默認命令超時時間（秒）
    [int]$LongRunningTimeoutSeconds = 300  # 長時間運行的命令超時時間（秒，如 pip install）
)

$ErrorActionPreference = "Continue"  # 改為 Continue 以便繼續執行並輸出錯誤

# 顏色輸出函數
function Write-ColorOutput($ForegroundColor, $Message) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Message
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Green($Message) { Write-ColorOutput Green $Message }
function Write-Yellow($Message) { Write-ColorOutput Yellow $Message }
function Write-Red($Message) { Write-ColorOutput Red $Message }
function Write-Blue($Message) { Write-ColorOutput Cyan $Message }

Write-Blue "========================================"
Write-Blue "  服務診斷與修復工具"
Write-Blue "========================================"
Write-Output ""
Write-Yellow "⚠ SSH認證說明:"
Write-Output "  此腳本支持兩種SSH認證方式："
Write-Output "  1. SSH密鑰認證（推薦）：請先配置SSH密鑰"
Write-Output "     ssh-copy-id ${User}@${RemoteHost}"
Write-Output "  2. 密碼認證：需要安裝sshpass工具"
Write-Output "     Windows: 使用WSL或Git Bash中的sshpass"
Write-Output "     Linux/Mac: sudo apt install sshpass 或 brew install hudochenkov/sshpass/sshpass"
Write-Output ""
Write-Output "  如果連接超時，請檢查："
Write-Output "  - SSH密鑰是否已配置"
Write-Output "  - 遠程主機是否可達（Test-NetConnection -ComputerName <host> -Port 22）"
Write-Output "  - 防火牆是否允許SSH連接"
Write-Output ""

# 讀取配置
Write-Output "[初始化] 讀取配置文件..."
if (-not (Test-Path $ConfigPath)) {
    Write-Red "✗ 配置文件不存在: $ConfigPath"
    exit 1
}

try {
    $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    $servers = $config.servers
    
    if ($null -eq $servers -or $servers.Count -eq 0) {
        Write-Red "✗ 未找到服務器配置"
        exit 1
    }
    Write-Green "✓ 配置文件讀取成功，找到 $($servers.Count) 個服務器節點"
} catch {
    Write-Red "✗ 讀取配置文件失敗: $($_.Exception.Message)"
    exit 1
}

# 在遠程服務器上執行命令（帶超時控制）
# 新增功能：超時控制、錯誤處理、進度日誌
# 注意：此函數依賴SSH密鑰認證，如果遠程主機需要密碼，請配置SSH密鑰或使用Python版本的腳本（使用paramiko）
function Invoke-RemoteCommand {
    param(
        [string]$RemoteHost,
        [string]$User,
        [string]$Password,  # 注意：PowerShell的ssh不支持非交互式密碼輸入，請使用SSH密鑰
        [string]$Command,
        [int]$TimeoutSeconds = 30,
        [switch]$Silent = $false  # 是否靜默執行（不輸出進度）
    )
    
    if (-not $Silent) {
        Write-Output "  [執行遠程命令] 超時: ${TimeoutSeconds}秒 | 主機: ${RemoteHost} | 用戶: ${User}"
    }
    
    $startTime = Get-Date
    
    try {
        # 檢查是否可以使用sshpass（如果已安裝）
        $useSshpass = $false
        if ($Password -and $Password.Trim() -ne "") {
            $sshpassCheck = Get-Command sshpass -ErrorAction SilentlyContinue
            if ($sshpassCheck) {
                $useSshpass = $true
                Write-Output "  [信息] 檢測到sshpass，將使用密碼認證"
            } else {
                Write-Yellow "  [警告] 未安裝sshpass，如果遠程主機需要密碼，請配置SSH密鑰"
                Write-Yellow "          或在Linux/Mac上安裝sshpass，或使用Python版本的腳本"
            }
        }
        
        # 構建SSH命令參數
        # 注意：Command 參數是原始的 shell 命令字符串（不包含外層引號）
        # 為遠程命令添加雙重超時保護：1) SSH 連接超時 2) PowerShell Job 超時
        # 遠程系統如果有 timeout 命令，也使用它作為第三重保護
        
        # 使用 printf %q 正確轉義命令，避免引號問題
        # 先嘗試使用 timeout 命令（如果遠程系統支持）
        # 如果不支持，遠程會報錯但命令仍會執行，由 Job 超時控制
        # 注意：Command 可能包含特殊字符，使用 base64 編碼更安全，但這裡用 printf %q 也足夠
        $escapedCommand = $Command -replace "'", "'\\''"  # 轉義單引號
        $remoteCommand = "timeout ${TimeoutSeconds} bash -c '$escapedCommand' 2>&1 || bash -c '$escapedCommand' 2>&1"
        
        if ($useSshpass) {
            # 使用sshpass進行密碼認證
            $sshArgs = @(
                "-p", $Password,
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=10",
                "-o", "ServerAliveInterval=5",
                "-o", "ServerAliveCountMax=2",
                "${User}@${RemoteHost}",
                $remoteCommand
            )
            $commandToRun = "sshpass"
        } else {
            # 使用SSH密鑰認證（默認）
            $sshArgs = @(
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=10",
                "-o", "ServerAliveInterval=5",
                "-o", "ServerAliveCountMax=2",
                "${User}@${RemoteHost}",
                $remoteCommand
            )
            $commandToRun = "ssh"
        }
        
        # 使用 Start-Job 實現超時控制
        # 這樣即使遠程系統沒有 timeout 命令，也能在本地層面控制超時
        $job = Start-Job -ScriptBlock {
            param($CommandToRun, $SshArgs)
            try {
                & $CommandToRun $SshArgs 2>&1
            } catch {
                # 捕獲 SSH 連接錯誤
                "SSH_CONNECTION_ERROR: $($_.Exception.Message)"
            }
        } -ArgumentList (,$commandToRun, $sshArgs)
        
        # 等待作業完成，最多等待 TimeoutSeconds + 10 秒（給 SSH 連接和遠程執行一些額外時間）
        $totalTimeout = $TimeoutSeconds + 10
        $waitResult = $job | Wait-Job -Timeout $totalTimeout
        
        $elapsed = ((Get-Date) - $startTime).TotalSeconds
        
        if ($waitResult) {
            # 作業完成（正常完成或被 timeout 命令終止）
            $result = $job | Receive-Job
            $job | Remove-Job -Force -ErrorAction SilentlyContinue
            
            if (-not $Silent) {
                Write-Output "  [完成] 耗時: ${elapsed}秒"
            }
            
            # 檢查結果中是否包含超時標記
            $resultString = $result -join " "
            if ($resultString -match "timeout:|TIMEOUT_ERROR") {
                Write-Yellow "  ⚠ 遠程命令可能超時（由遠程系統 timeout 命令終止）"
            }
            
            return $result
        } else {
            # PowerShell Job 層面超時
            try {
                $job | Stop-Job -ErrorAction SilentlyContinue
                $partialResult = $job | Receive-Job -ErrorAction SilentlyContinue
            } catch {
                $partialResult = @()
            }
            $job | Remove-Job -Force -ErrorAction SilentlyContinue
            
            $elapsed = ((Get-Date) - $startTime).TotalSeconds
            Write-Red "  [超時] 命令執行超過 ${TimeoutSeconds} 秒（實際等待 ${elapsed} 秒）"
            Write-Yellow "  命令: $Command"
            if ($partialResult) {
                Write-Yellow "  部分輸出: $($partialResult -join ' ')"
            }
            return @("TIMEOUT_ERROR: Command exceeded timeout of ${TimeoutSeconds} seconds")
        }
    } catch {
        $elapsed = ((Get-Date) - $startTime).TotalSeconds
        Write-Red "  [錯誤] SSH 執行失敗: $($_.Exception.Message)（耗時 ${elapsed} 秒）"
        Write-Yellow "  錯誤類型: $($_.Exception.GetType().FullName)"
        return @("SSH_ERROR: $($_.Exception.Message)")
    }
}

# 診斷服務問題（添加更多進度日誌和錯誤處理）
function Diagnose-Service {
    param(
        [string]$RemoteHost,
        [string]$User,
        [string]$Password,
        [string]$DeployDir,
        [string]$ServiceName
    )
    
    Write-Green "`n[診斷] 開始診斷服務問題..."
    Write-Output "  遠程主機: $RemoteHost"
    Write-Output "  用戶: $User"
    Write-Output "  部署目錄: $DeployDir"
    Write-Output "  服務名稱: $ServiceName"
    
    try {
        # 1. 檢查服務是否存在
        Write-Output "`n  [步驟 1/9] 檢查服務狀態..."
        $statusCmd = "sudo systemctl status $ServiceName --no-pager 2>&1 || echo 'SERVICE_NOT_FOUND'"
        Write-Output "  執行命令: systemctl status $ServiceName"
        $statusResult = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command $statusCmd -TimeoutSeconds $DefaultTimeoutSeconds
        
        Write-Output "  服務狀態檢查結果:"
        $statusOutput = $statusResult -join "`n  "
        if ($statusOutput.Length -gt 500) {
            Write-Output "  $($statusOutput.Substring(0, 500))...（已截斷）"
        } else {
            Write-Output "  $statusOutput"
        }
        
        # 2. 查看服務日誌（減少日誌行數以加快速度）
        Write-Output "`n  [步驟 2/9] 查看服務日誌（最近30行）..."
        $logCmd = "sudo journalctl -u $ServiceName -n 30 --no-pager 2>&1"
        Write-Output "  執行命令: journalctl -u $ServiceName -n 30"
        $logResult = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command $logCmd -TimeoutSeconds $DefaultTimeoutSeconds
        
        if ($logResult -match "No entries") {
            Write-Yellow "  ⚠ 未找到服務日誌，服務可能未運行或未正確配置"
        } else {
            Write-Output "  最近日誌（前200字符）:"
            $logOutput = $logResult -join "`n"
            if ($logOutput.Length -gt 200) {
                Write-Output "  $($logOutput.Substring(0, 200))...（已截斷，完整日誌見下方）"
            } else {
                Write-Output "  $logOutput"
            }
        }
        
        # 3. 檢查systemd服務文件
        Write-Output "`n  [步驟 3/9] 檢查systemd服務文件..."
        $serviceFileCmd = "sudo cat /etc/systemd/system/$ServiceName.service 2>&1 || echo 'FILE_NOT_FOUND'"
        $serviceFileResult = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command $serviceFileCmd -TimeoutSeconds $DefaultTimeoutSeconds
        
        if ($serviceFileResult -match "FILE_NOT_FOUND") {
            Write-Yellow "  ⚠ systemd服務文件不存在"
            return @{Issue = "SERVICE_FILE_MISSING"}
        } else {
            Write-Output "  服務文件已存在（內容已讀取）"
        }
        
        # 4. 檢查啟動腳本
        Write-Output "`n  [步驟 4/9] 檢查啟動腳本..."
        $startScriptCmd = "test -f $DeployDir/start.sh && cat $DeployDir/start.sh || echo 'SCRIPT_NOT_FOUND'"
        $startScriptResult = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command $startScriptCmd -TimeoutSeconds $DefaultTimeoutSeconds
        
        if ($startScriptResult -match "SCRIPT_NOT_FOUND") {
            Write-Yellow "  ⚠ 啟動腳本不存在"
            return @{Issue = "START_SCRIPT_MISSING"}
        } else {
            Write-Output "  啟動腳本已存在"
        }
        
        # 5. 檢查虛擬環境
        Write-Output "`n  [步驟 5/9] 檢查虛擬環境..."
        $venvCmd = "test -f $DeployDir/venv/bin/python && $DeployDir/venv/bin/python --version || echo 'VENV_NOT_FOUND'"
        $venvResult = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command $venvCmd -TimeoutSeconds $DefaultTimeoutSeconds
        
        if ($venvResult -match "VENV_NOT_FOUND") {
            Write-Yellow "  ⚠ 虛擬環境不存在"
            return @{Issue = "VENV_MISSING"}
        } else {
            Write-Output "  虛擬環境存在: $($venvResult -join ' ')"
        }
        
        # 6. 檢查部署目錄結構
        Write-Output "`n  [步驟 6/9] 檢查部署目錄結構..."
        $dirCheckCmd = "ls -la $DeployDir 2>&1 | head -20"
        $dirCheckResult = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command $dirCheckCmd -TimeoutSeconds $DefaultTimeoutSeconds
        Write-Output "  目錄結構檢查完成"
        
        # 7. 檢查端口占用
        Write-Output "`n  [步驟 7/9] 檢查端口占用..."
        $portCheckCmd = "sudo netstat -tlnp 2>/dev/null | grep ':8000' || echo 'PORT_FREE'"
        $portCheckResult = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command $portCheckCmd -TimeoutSeconds $DefaultTimeoutSeconds
        Write-Output "  端口8000狀態: $($portCheckResult -join ' ')"
        
        # 8. 檢查Python依賴
        Write-Output "`n  [步驟 8/9] 檢查Python依賴..."
        $depsCheckCmd = "$DeployDir/venv/bin/pip list 2>&1 | grep -E '(fastapi|uvicorn)' || echo 'DEPS_MISSING'"
        $depsCheckResult = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command $depsCheckCmd -TimeoutSeconds $DefaultTimeoutSeconds
        
        if ($depsCheckResult -match "DEPS_MISSING") {
            Write-Yellow "  ⚠ Python依賴缺失"
            return @{Issue = "DEPS_MISSING"}
        } else {
            Write-Output "  依賴已安裝: $($depsCheckResult -join ' ')"
        }
        
        # 9. 檢查admin-backend目錄
        Write-Output "`n  [步驟 9/9] 檢查admin-backend目錄..."
        $backendCheckCmd = "test -d $DeployDir/admin-backend/app && echo 'BACKEND_EXISTS' || echo 'BACKEND_MISSING'"
        $backendCheckResult = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command $backendCheckCmd -TimeoutSeconds $DefaultTimeoutSeconds
        
        if ($backendCheckResult -match "BACKEND_MISSING") {
            Write-Yellow "  ⚠ admin-backend目錄不存在"
            return @{Issue = "BACKEND_MISSING"}
        } else {
            Write-Output "  admin-backend目錄存在"
        }
        
        Write-Green "`n  ✓ 診斷完成，未發現明顯問題"
        return @{Issue = "NONE"}
        
    } catch {
        Write-Red "`n  ✗ 診斷過程中發生錯誤: $($_.Exception.Message)"
        return @{Issue = "DIAGNOSIS_ERROR"; Error = $_.Exception.Message}
    }
}

# 修復服務問題（增強錯誤處理和超時控制）
function Fix-Service {
    param(
        [string]$RemoteHost,
        [string]$User,
        [string]$Password,
        [string]$DeployDir,
        [string]$ServiceName,
        [string]$Issue
    )
    
    Write-Green "`n[修復] 開始修復服務問題: $Issue"
    
    try {
        switch ($Issue) {
            "SERVICE_FILE_MISSING" {
                Write-Output "  [修復操作] 創建systemd服務文件..."
                
                $serviceContent = @"
[Unit]
Description=Group AI Worker Node Service
After=network.target

[Service]
Type=simple
User=$User
WorkingDirectory=$DeployDir
Environment=`"PATH=$DeployDir/venv/bin`"
Environment=`"PYTHONPATH=$DeployDir`"
ExecStart=$DeployDir/start.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"@
                
                # 使用base64編碼傳輸內容，避免引號轉義問題
                $base64Content = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($serviceContent))
                $createServiceCmd = "echo '$base64Content' | base64 -d | sudo tee /etc/systemd/system/$ServiceName.service > /dev/null"
                
                $result = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command $createServiceCmd -TimeoutSeconds $DefaultTimeoutSeconds -Silent
                
                if ($result -match "TIMEOUT_ERROR|SSH_ERROR") {
                    throw "創建服務文件失敗: $result"
                }
                
                Write-Green "  ✓ 服務文件已創建"
            }
            
            "START_SCRIPT_MISSING" {
                Write-Output "  [修復操作] 創建啟動腳本..."
                
                $startScriptContent = @"
#!/bin/bash
cd ${DeployDir}
source venv/bin/activate
export PYTHONPATH=${DeployDir}:`$PYTHONPATH

if [ -d "admin-backend/app" ]; then
    cd admin-backend
    ${DeployDir}/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    echo "Worker service placeholder"
    sleep infinity
fi
"@
                
                # 使用base64編碼傳輸內容
                $base64Content = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($startScriptContent))
                $createScriptCmd = "echo '$base64Content' | base64 -d > $DeployDir/start.sh && chmod +x $DeployDir/start.sh"
                
                $result = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command $createScriptCmd -TimeoutSeconds $DefaultTimeoutSeconds -Silent
                
                if ($result -match "TIMEOUT_ERROR|SSH_ERROR") {
                    throw "創建啟動腳本失敗: $result"
                }
                
                Write-Green "  ✓ 啟動腳本已創建"
            }
            
            "VENV_MISSING" {
                Write-Output "  [修復操作] 創建虛擬環境（這可能需要較長時間）..."
                
                $createVenvCmd = "cd $DeployDir && python3 -m venv venv && $DeployDir/venv/bin/pip install --upgrade pip setuptools wheel"
                
                $result = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command $createVenvCmd -TimeoutSeconds $LongRunningTimeoutSeconds
                
                if ($result -match "TIMEOUT_ERROR") {
                    Write-Yellow "  ⚠ 虛擬環境創建可能超時，請手動檢查"
                } elseif ($result -match "SSH_ERROR") {
                    throw "創建虛擬環境失敗: $result"
                } else {
                    Write-Green "  ✓ 虛擬環境已創建"
                }
            }
            
            "DEPS_MISSING" {
                Write-Output "  [修復操作] 安裝Python依賴（這可能需要5-10分鐘）..."
                
                $installDepsCmd = "cd $DeployDir && $DeployDir/venv/bin/pip install -r requirements.txt"
                
                $result = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command $installDepsCmd -TimeoutSeconds $LongRunningTimeoutSeconds
                
                if ($result -match "TIMEOUT_ERROR") {
                    Write-Yellow "  ⚠ 依賴安裝超時，可能仍在進行中，請手動檢查"
                } elseif ($result -match "SSH_ERROR") {
                    Write-Yellow "  ⚠ 依賴安裝過程中出現錯誤: $result"
                } else {
                    Write-Green "  ✓ 依賴安裝完成"
                }
            }
            
            "BACKEND_MISSING" {
                Write-Yellow "  ⚠ admin-backend目錄不存在，需要手動上傳項目文件"
                Write-Output "  請使用部署腳本上傳項目文件到: $DeployDir"
            }
            
            default {
                Write-Yellow "  ⚠ 未識別的問題類型: $Issue，跳過自動修復"
            }
        }
        
        # 通用修復步驟
        Write-Output "  [通用修復] 重新加載systemd..."
        $result = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command "sudo systemctl daemon-reload" -TimeoutSeconds $DefaultTimeoutSeconds -Silent
        
        if ($result -match "TIMEOUT_ERROR|SSH_ERROR") {
            Write-Yellow "  ⚠ systemd重新加載可能失敗: $result"
        } else {
            Write-Green "  ✓ systemd已重新加載"
        }
        
        Write-Output "  [通用修復] 啟用服務..."
        $result = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command "sudo systemctl enable $ServiceName" -TimeoutSeconds $DefaultTimeoutSeconds -Silent
        
        if ($result -match "TIMEOUT_ERROR|SSH_ERROR") {
            Write-Yellow "  ⚠ 服務啟用可能失敗: $result"
        } else {
            Write-Green "  ✓ 服務已啟用"
        }
        
    } catch {
        Write-Red "  ✗ 修復過程中發生錯誤: $($_.Exception.Message)"
        throw
    }
}

# 重啟服務（增強錯誤處理）
function Restart-Service {
    param(
        [string]$RemoteHost,
        [string]$User,
        [string]$Password,
        [string]$ServiceName
    )
    
    Write-Green "`n[重啟] 開始重啟服務..."
    
    try {
        Write-Output "  [步驟 1/3] 停止服務..."
        $result = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command "sudo systemctl stop $ServiceName" -TimeoutSeconds $DefaultTimeoutSeconds -Silent
        
        if ($result -match "TIMEOUT_ERROR|SSH_ERROR") {
            Write-Yellow "  ⚠ 停止服務時出現問題: $result，繼續執行..."
        }
        
        Start-Sleep -Seconds 2
        
        Write-Output "  [步驟 2/3] 啟動服務..."
        $result = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command "sudo systemctl start $ServiceName" -TimeoutSeconds $DefaultTimeoutSeconds -Silent
        
        if ($result -match "TIMEOUT_ERROR|SSH_ERROR") {
            Write-Red "  ✗ 啟動服務失敗: $result"
            return $false
        }
        
        Start-Sleep -Seconds 3
        
        Write-Output "  [步驟 3/3] 檢查服務狀態..."
        $statusCmd = "sudo systemctl is-active $ServiceName"
        $status = Invoke-RemoteCommand -RemoteHost $RemoteHost -User $User -Password $Password -Command $statusCmd -TimeoutSeconds $DefaultTimeoutSeconds -Silent
        
        $statusText = $status -join " " | Out-String
        $statusText = $statusText.Trim()
        
        if ($statusText -match "active") {
            Write-Green "  ✓ 服務運行中 (狀態: $statusText)"
            return $true
        } else {
            Write-Red "  ✗ 服務未運行，狀態: $statusText"
            return $false
        }
        
    } catch {
        Write-Red "  ✗ 重啟服務時發生錯誤: $($_.Exception.Message)"
        return $false
    }
}

# 驗證API端點（已有超時，但增強錯誤處理和日誌）
function Test-APIEndpoint {
    param(
        [string]$RemoteHost,
        [int]$Port = 8000
    )
    
    Write-Green "`n[驗證] 測試API端點..."
    
    try {
        $healthUrl = "http://${RemoteHost}:${Port}/health"
        Write-Output "  測試URL: $healthUrl"
        Write-Output "  超時設置: 10秒"
        
        $startTime = Get-Date
        $response = Invoke-WebRequest -Uri $healthUrl -Method Get -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        $elapsed = ((Get-Date) - $startTime).TotalSeconds
        
        if ($response.StatusCode -eq 200) {
            Write-Green "  ✓ API端點可訪問（耗時: ${elapsed}秒）"
            Write-Output "  響應內容: $($response.Content)"
            return $true
        } else {
            Write-Yellow "  ⚠ API端點返回非200狀態碼: $($response.StatusCode)"
            return $false
        }
    } catch [System.Net.WebException] {
        $elapsed = ((Get-Date) - $startTime).TotalSeconds
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
            Write-Red "  ✗ API端點無法訪問: HTTP $statusCode（耗時: ${elapsed}秒）"
        } else {
            Write-Red "  ✗ API端點無法訪問: $($_.Exception.Message)（耗時: ${elapsed}秒）"
            Write-Yellow "    可能原因：服務未啟動、防火牆阻擋、網絡不通"
        }
        return $false
    } catch {
        $elapsed = ((Get-Date) - $startTime).TotalSeconds
        Write-Red "  ✗ API端點測試失敗: $($_.Exception.Message)（耗時: ${elapsed}秒）"
        return $false
    }
}

# 主流程（增強錯誤處理）
Write-Output "[主流程] 開始處理服務器節點..."
$nodeCount = ($servers.PSObject.Properties.Name | Measure-Object).Count
$currentNode = 0

foreach ($nodeId in $servers.PSObject.Properties.Name) {
    $currentNode++
    $server = $servers.$nodeId
    $remoteHost = $server.host
    $user = $server.user
    $password = $server.password
    $deployDir = $server.deploy_dir
    
    Write-Blue "`n========================================"
    Write-Blue "  處理節點: $nodeId ($currentNode/$nodeCount)"
    Write-Blue "  主機: $remoteHost"
    Write-Blue "========================================"
    
    try {
        # 1. 診斷問題
        Write-Output "`n[階段 1/3] 診斷問題..."
        $diagnosis = Diagnose-Service -RemoteHost $remoteHost -User $user -Password $password -DeployDir $deployDir -ServiceName $ServiceName
        
        if ($null -eq $diagnosis) {
            Write-Red "  ✗ 診斷失敗，跳過此節點"
            continue
        }
        
        # 2. 修復問題
        if ($diagnosis.Issue -ne "NONE" -and $diagnosis.Issue -ne "DIAGNOSIS_ERROR") {
            Write-Output "`n[階段 2/3] 修復問題..."
            Fix-Service -RemoteHost $remoteHost -User $user -Password $password -DeployDir $deployDir -ServiceName $ServiceName -Issue $diagnosis.Issue
        } else {
            Write-Output "`n[階段 2/3] 跳過修復（無需修復）"
        }
        
        # 3. 重啟服務並驗證
        Write-Output "`n[階段 3/3] 重啟服務並驗證..."
        $restartSuccess = Restart-Service -RemoteHost $remoteHost -User $user -Password $password -ServiceName $ServiceName
        
        if ($restartSuccess) {
            # 4. 查看最新日誌
            Write-Output "`n[驗證] 查看最新服務日誌..."
            $latestLogs = Invoke-RemoteCommand -RemoteHost $remoteHost -User $user -Password $password -Command "sudo journalctl -u $ServiceName -n 20 --no-pager" -TimeoutSeconds $DefaultTimeoutSeconds
            
            if ($latestLogs -and $latestLogs.Count -gt 0) {
                $logOutput = $latestLogs -join "`n"
                if ($logOutput.Length -gt 500) {
                    Write-Output "  $($logOutput.Substring(0, 500))...（已截斷）"
                } else {
                    Write-Output "  $logOutput"
                }
            }
            
            # 5. 驗證API端點
            $apiAccessible = Test-APIEndpoint -RemoteHost $remoteHost
            
            if ($apiAccessible) {
                Write-Green "`n✓✓✓ 節點 $nodeId 服務已正常運行 ✓✓✓"
            } else {
                Write-Yellow "`n⚠ 節點 $nodeId 服務已啟動，但API端點無法訪問"
                Write-Yellow "  請檢查：1) 防火牆設置 2) 服務是否真的在監聽8000端口 3) 網絡連接"
            }
        } else {
            Write-Red "`n✗ 節點 $nodeId 服務啟動失敗"
            
            # 顯示詳細錯誤日誌
            Write-Yellow "`n[錯誤日誌] 查看詳細錯誤..."
            $errorLogs = Invoke-RemoteCommand -RemoteHost $remoteHost -User $user -Password $password -Command "sudo journalctl -u $ServiceName -n 30 --no-pager -p err" -TimeoutSeconds $DefaultTimeoutSeconds
            
            if ($errorLogs -and $errorLogs.Count -gt 0) {
                $errorOutput = $errorLogs -join "`n"
                if ($errorOutput.Length -gt 500) {
                    Write-Output "  $($errorOutput.Substring(0, 500))...（已截斷）"
                } else {
                    Write-Output "  $errorOutput"
                }
            }
        }
        
    } catch {
        Write-Red "`n✗✗✗ 處理節點 $nodeId 時發生嚴重錯誤 ✗✗✗"
        Write-Red "  錯誤詳情: $($_.Exception.Message)"
        Write-Red "  錯誤位置: $($_.InvocationInfo.ScriptLineNumber) 行"
        Write-Yellow "  繼續處理下一個節點..."
    }
}

Write-Blue "`n========================================"
Write-Blue "  診斷與修復完成"
Write-Blue "========================================"
