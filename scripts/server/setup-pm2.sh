#!/bin/bash
# ============================================================
# Setup PM2 for Zero-Downtime Deployment
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Install PM2 (if needed) and start backend/frontend services
#
# One-click execution: bash scripts/server/setup-pm2.sh
# ============================================================

set -e

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
ECOSYSTEM_CONFIG="$PROJECT_DIR/ecosystem.config.js"

echo "============================================================"
echo "🚀 Setting up PM2 for Zero-Downtime Deployment"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================
# 1. Check if PM2 is installed
# ============================================================
echo "[1/5] Checking PM2 installation..."
if ! command -v pm2 &> /dev/null; then
    echo -e "${YELLOW}⚠️  PM2 is not installed. Installing...${NC}"
    sudo npm install -g pm2
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PM2 installed successfully${NC}"
    else
        echo -e "${RED}❌ PM2 installation failed${NC}"
        exit 1
    fi
else
    PM2_VERSION=$(pm2 -v)
    echo -e "${GREEN}✅ PM2 is already installed (version: $PM2_VERSION)${NC}"
fi
echo ""

# ============================================================
# 2. Verify ecosystem.config.js exists
# ============================================================
echo "[2/5] Verifying ecosystem.config.js..."
if [ ! -f "$ECOSYSTEM_CONFIG" ]; then
    echo -e "${RED}❌ ecosystem.config.js not found at: $ECOSYSTEM_CONFIG${NC}"
    exit 1
fi
echo -e "${GREEN}✅ ecosystem.config.js found${NC}"
echo ""

# ============================================================
# 3. Verify backend virtual environment
# ============================================================
echo "[3/5] Verifying backend virtual environment..."
BACKEND_VENV="$PROJECT_DIR/admin-backend/venv/bin/python"
if [ ! -f "$BACKEND_VENV" ]; then
    echo -e "${YELLOW}⚠️  Backend virtual environment not found. Creating...${NC}"
    cd "$PROJECT_DIR/admin-backend"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Backend virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Backend virtual environment found${NC}"
fi
echo ""

# ============================================================
# 4. Stop existing PM2 processes (if any)
# ============================================================
echo "[4/5] Stopping existing PM2 processes..."
pm2 stop all 2>/dev/null || true
pm2 delete all 2>/dev/null || true
echo -e "${GREEN}✅ Existing processes stopped${NC}"
echo ""

# ============================================================
# 5. Start services with PM2
# ============================================================
echo "[5/5] Starting services with PM2..."
cd "$PROJECT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start PM2 with ecosystem config
pm2 start ecosystem.config.js

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Services started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start services${NC}"
    exit 1
fi
echo ""

# ============================================================
# 6. Save PM2 configuration
# ============================================================
echo "Saving PM2 configuration..."
pm2 save

# Setup PM2 startup script
echo "Setting up PM2 startup script..."
pm2 startup | grep -v "PM2" | bash || true

echo ""
echo "============================================================"
echo -e "${GREEN}✅ PM2 Setup Complete${NC}"
echo "============================================================"
echo ""
echo "📊 Current PM2 Status:"
echo ""
pm2 status
echo ""
echo "📝 Useful Commands:"
echo "  - pm2 status          : View process status"
echo "  - pm2 logs            : View all logs"
echo "  - pm2 logs backend    : View backend logs"
echo "  - pm2 logs frontend   : View frontend logs"
echo "  - pm2 restart all     : Restart all processes"
echo "  - pm2 stop all        : Stop all processes"
echo "  - pm2 delete all      : Delete all processes"
echo ""

