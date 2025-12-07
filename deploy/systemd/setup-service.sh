#!/bin/bash
# ============================================================
# Setup Systemd Service (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Install and configure systemd service for backend
# 
# One-click execution: bash deploy/systemd/setup-service.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "🔧 Setup Systemd Service"
echo "============================================================"
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root or with sudo"
    echo "Usage: sudo bash deploy/systemd/setup-service.sh"
    exit 1
fi

cd "$PROJECT_ROOT"

# 检查服务文件是否存在
SERVICE_FILE="deploy/systemd/telegram-backend.service"
if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ Error: Service file not found: $SERVICE_FILE"
    exit 1
fi

echo "[1/4] Checking project structure..."
if [ ! -d "admin-backend" ]; then
    echo "❌ Error: admin-backend directory not found"
    exit 1
fi

# 检查虚拟环境
VENV_PATH="admin-backend/venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "⚠️  Virtual environment not found at $VENV_PATH"
    echo "Creating virtual environment..."
    cd admin-backend
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    cd ..
    echo "✅ Virtual environment created"
fi

echo ""
echo "[2/4] Configuring service file..."

# 获取实际路径
PROJECT_ABS_PATH=$(pwd)
USER=$(logname || echo "ubuntu")
GROUP=$(id -gn "$USER")

# 更新服务文件中的路径和用户
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$PROJECT_ABS_PATH/admin-backend|g" "$SERVICE_FILE"
sed -i "s|User=.*|User=$USER|g" "$SERVICE_FILE"
sed -i "s|Group=.*|Group=$GROUP|g" "$SERVICE_FILE"
sed -i "s|Environment=\"PATH=.*|Environment=\"PATH=$PROJECT_ABS_PATH/admin-backend/venv/bin:/usr/local/bin:/usr/bin:/bin\"|g" "$SERVICE_FILE"
sed -i "s|ExecStart=.*|ExecStart=$PROJECT_ABS_PATH/admin-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000|g" "$SERVICE_FILE"

echo "✅ Service file configured"

echo ""
echo "[3/4] Installing service..."
cp "$SERVICE_FILE" /etc/systemd/system/telegram-backend.service
systemctl daemon-reload
echo "✅ Service installed"

echo ""
echo "[4/4] Enabling and starting service..."
systemctl enable telegram-backend
systemctl start telegram-backend
echo "✅ Service enabled and started"

echo ""
echo "============================================================"
echo "✅ Setup Complete!"
echo "============================================================"
echo ""
echo "Service commands:"
echo "  sudo systemctl status telegram-backend    # 查看状态"
echo "  sudo systemctl restart telegram-backend   # 重启服务"
echo "  sudo systemctl stop telegram-backend      # 停止服务"
echo "  sudo systemctl start telegram-backend     # 启动服务"
echo "  sudo journalctl -u telegram-backend -f   # 查看日志"
echo ""

# 显示服务状态
systemctl status telegram-backend --no-pager || true

