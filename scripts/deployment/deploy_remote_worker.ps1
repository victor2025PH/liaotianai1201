# 遠程工作節點自動部署腳本 (PowerShell版本)
# 用於在遠程服務器上部署群組AI工作節點

param(
    [string]$RemoteHost = "165.154.254.99",
    [string]$RemoteUser = "root",
    [string]$RemotePassword = "Along2025!!!",
    [string]$NodeId = "worker-01",
    [string]$DeployDir = "/opt/group-ai",
    [int]$MaxAccounts = 5
)

$ErrorActionPreference = "Stop"

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
Write-Blue "  群組AI工作節點遠程部署腳本"
Write-Blue "========================================"
Write-Output ""
Write-Green "部署目標:"
Write-Output "  主機: $RemoteHost"
Write-Output "  用戶: $RemoteUser"
Write-Output "  節點ID: $NodeId"
Write-Output "  部署目錄: $DeployDir"
Write-Output "  最大帳號數: $MaxAccounts"
Write-Output ""

# 檢查必要的工具
function Test-Requirements {
    Write-Green "[1/10] 檢查本地環境..."
    
    # 檢查SSH
    if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
        Write-Red "✗ SSH 未安裝，請安裝 OpenSSH"
        exit 1
    }
    
    # 檢查plink或使用sshpass替代方案
    Write-Green "✓ 環境檢查完成"
}

# 測試SSH連接
function Test-SSHConnection {
    Write-Green "[2/10] 測試SSH連接..."
    
    $testCommand = "echo 'SSH連接成功'"
    $sshArgs = @(
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        "${RemoteUser}@${RemoteHost}",
        $testCommand
    )
    
    try {
        $result = & ssh $sshArgs 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Green "✓ SSH連接成功"
        } else {
            throw "SSH連接失敗"
        }
    } catch {
        Write-Red "✗ SSH連接失敗，請檢查："
        Write-Output "  - 服務器IP地址: $RemoteHost"
        Write-Output "  - 用戶名: $RemoteUser"
        Write-Output "  - 密碼: $RemotePassword"
        Write-Output "  - 防火牆是否開放22端口"
        exit 1
    }
}

# 在遠程服務器上執行命令
function Invoke-RemoteCommand {
    param([string]$Command)
    
    $sshArgs = @(
        "-o", "StrictHostKeyChecking=no",
        "${RemoteUser}@${RemoteHost}",
        $Command
    )
    
    & ssh $sshArgs
}

# 上傳文件到遠程服務器
function Send-RemoteFile {
    param(
        [string]$LocalFile,
        [string]$RemoteFile
    )
    
    $scpArgs = @(
        "-o", "StrictHostKeyChecking=no",
        $LocalFile,
        "${RemoteUser}@${RemoteHost}:${RemoteFile}"
    )
    
    & scp $scpArgs
}

# 部署腳本主體
function Start-RemoteDeployment {
    Write-Green "[3/10] 準備遠程部署環境..."
    
    $deployScript = @"
#!/bin/bash
set -e

DEPLOY_DIR="$DeployDir"
NODE_ID="$NodeId"
MAX_ACCOUNTS="$MaxAccounts"

echo "=== 開始遠程部署 ==="
echo "部署目錄: `$DEPLOY_DIR"
echo "節點ID: `$NODE_ID"
echo "最大帳號數: `$MAX_ACCOUNTS"

# 1. 更新系統
echo "[1/8] 更新系統..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq

# 2. 安裝基礎工具
echo "[2/8] 安裝基礎工具..."
apt-get install -y -qq curl wget git vim htop net-tools ufw build-essential software-properties-common python3-pip python3-venv python3-dev

# 3. 安裝Python 3.11
echo "[3/8] 安裝Python 3.11..."
add-apt-repository -y ppa:deadsnakes/ppa > /dev/null 2>&1
apt-get update -qq
apt-get install -y -qq python3.11 python3.11-venv python3.11-dev

# 4. 配置系統限制
echo "[4/8] 配置系統限制..."
cat >> /etc/security/limits.conf << EOF
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
EOF

# 5. 配置時區
echo "[5/8] 配置時區..."
timedatectl set-timezone Asia/Shanghai

# 6. 配置防火牆
echo "[6/8] 配置防火牆..."
ufw --force enable
ufw allow 22/tcp
ufw allow 8000/tcp

# 7. 創建部署目錄結構
echo "[7/8] 創建目錄結構..."
mkdir -p `$DEPLOY_DIR/{sessions,logs,configs,ai_models/group_scripts}
chmod -R 755 `$DEPLOY_DIR

# 8. 創建Python虛擬環境
echo "[8/8] 創建Python虛擬環境..."
python3.11 -m venv `$DEPLOY_DIR/venv
`$DEPLOY_DIR/venv/bin/pip install --upgrade pip setuptools wheel

echo "=== 基礎環境部署完成 ==="
"@
    
    # 將腳本寫入臨時文件
    $tempScript = [System.IO.Path]::GetTempFileName()
    $deployScript | Out-File -FilePath $tempScript -Encoding UTF8
    
    # 上傳並執行
    Send-RemoteFile -LocalFile $tempScript -RemoteFile "/tmp/remote_deploy.sh"
    Invoke-RemoteCommand "chmod +x /tmp/remote_deploy.sh && /tmp/remote_deploy.sh $DeployDir $NodeId $MaxAccounts"
    
    Remove-Item $tempScript
    Write-Green "✓ 遠程環境準備完成"
}

# 主函數
function Main {
    Test-Requirements
    Test-SSHConnection
    Start-RemoteDeployment
    
    Write-Output ""
    Write-Blue "========================================"
    Write-Green "  部署完成！"
    Write-Blue "========================================"
    Write-Output ""
    Write-Yellow "下一步操作:"
    Write-Output "  1. 編輯配置文件:"
    Write-Output "     ssh ${RemoteUser}@${RemoteHost}"
    Write-Output "     vi ${DeployDir}/.env"
    Write-Output ""
    Write-Output "  2. 上傳Session文件到:"
    Write-Output "     ${DeployDir}/sessions/"
    Write-Output ""
}

Main

