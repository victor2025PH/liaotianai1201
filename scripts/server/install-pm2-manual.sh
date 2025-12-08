#!/bin/bash
# ============================================================
# Manual PM2 Installation Script
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Install PM2 with sudo and verify installation
#
# One-click execution: bash scripts/server/install-pm2-manual.sh
# ============================================================

set -e

echo "============================================================"
echo "🔧 Installing PM2 with Sudo"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================
# 1. Check if PM2 is already installed
# ============================================================
echo "[1/3] Checking if PM2 is already installed..."
if command -v pm2 &> /dev/null; then
    PM2_VERSION=$(pm2 -v)
    echo -e "${GREEN}✅ PM2 is already installed (version: $PM2_VERSION)${NC}"
    echo ""
    echo "Skipping installation. Proceeding to verification..."
else
    echo -e "${YELLOW}⚠️  PM2 is not installed. Installing with sudo...${NC}"
    
    # ============================================================
    # 2. Install PM2 with sudo
    # ============================================================
    echo "[2/3] Installing PM2 globally with sudo..."
    sudo npm install -g pm2
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PM2 installed successfully${NC}"
    else
        echo -e "${RED}❌ PM2 installation failed${NC}"
        exit 1
    fi
fi
echo ""

# ============================================================
# 3. Verify PM2 installation
# ============================================================
echo "[3/3] Verifying PM2 installation..."
if command -v pm2 &> /dev/null; then
    PM2_VERSION=$(pm2 -v)
    echo -e "${GREEN}✅ PM2 verification successful${NC}"
    echo -e "${GREEN}   Version: $PM2_VERSION${NC}"
    echo ""
    echo "============================================================"
    echo -e "${GREEN}✅ PM2 Installation Complete${NC}"
    echo "============================================================"
    echo ""
    echo "📝 Next steps:"
    echo "  1. Run: bash scripts/server/setup-pm2.sh"
    echo "  2. Or manually: pm2 start ecosystem.config.js"
    echo ""
else
    echo -e "${RED}❌ PM2 verification failed${NC}"
    echo "Please check the installation output above for errors."
    exit 1
fi

