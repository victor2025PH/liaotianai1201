# 交互式遠程部署腳本
# 用於在遠程服務器上部署群組AI工作節點

param(
    [string]$RemoteHost = "165.154.254.99",
    [string]$RemoteUser = "root",
    [string]$RemotePassword = "Along2025!!!",
    [string]$NodeId = "worker-01",
    [string]$DeployDir = "/opt/group-ai",
    [int]$MaxAccounts = 5
)

$ErrorActionPreference = "Continue"

# 顏色輸出
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

# 創建遠程部署腳本內容
$remoteScript = @"
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
mkdir -p `$DEPLOY_DIR/{sessions,logs,configs,ai_models/group_scripts,data}
chmod -R 755 `$DEPLOY_DIR

# 8. 創建Python虛擬環境
echo "[8/8] 創建Python虛擬環境..."
python3.11 -m venv `$DEPLOY_DIR/venv
`$DEPLOY_DIR/venv/bin/pip install --upgrade pip setuptools wheel

echo "=== 基礎環境部署完成 ==="
"@

# 將遠程腳本保存到臨時文件
$tempScript = [System.IO.Path]::GetTempFileName()
$remoteScript | Out-File -FilePath $tempScript -Encoding UTF8 -NoNewline

Write-Green "[步驟1] 清理SSH主機密鑰..."
ssh-keygen -R $RemoteHost -f "$env:USERPROFILE\.ssh\known_hosts" -ErrorAction SilentlyContinue

Write-Green "[步驟2] 上傳並執行遠程部署腳本..."
Write-Yellow "提示: 當提示輸入密碼時，請輸入: $RemotePassword"
Write-Output ""

# 使用SCP上傳腳本
Write-Output "正在上傳部署腳本..."
scp -o StrictHostKeyChecking=accept-new $tempScript "${RemoteUser}@${RemoteHost}:/tmp/remote_deploy.sh"

# 使用SSH執行腳本
Write-Output "正在執行遠程部署（這可能需要幾分鐘）..."
ssh -o StrictHostKeyChecking=accept-new "${RemoteUser}@${RemoteHost}" "chmod +x /tmp/remote_deploy.sh && /tmp/remote_deploy.sh"

# 清理臨時文件
Remove-Item $tempScript -ErrorAction SilentlyContinue

Write-Green "✓ 基礎環境部署完成"
Write-Output ""
Write-Yellow "下一步: 請手動執行以下命令完成部署："
Write-Output ""
Write-Output "1. 上傳項目文件:"
Write-Output "   scp -r group_ai_service admin-backend/app/api/group_ai config.py ${RemoteUser}@${RemoteHost}:${DeployDir}/"
Write-Output ""
Write-Output "2. 安裝Python依賴:"
Write-Output "   ssh ${RemoteUser}@${RemoteHost} 'cd ${DeployDir} && source venv/bin/activate && pip install -r requirements.txt'"
Write-Output ""
Write-Output "3. 配置環境變量:"
Write-Output "   ssh ${RemoteUser}@${RemoteHost} 'vi ${DeployDir}/.env'"
Write-Output ""

