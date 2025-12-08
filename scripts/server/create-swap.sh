#!/bin/bash
# ============================================================
# Create Swap File to Prevent OOM (Out of Memory)
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Create a 4GB swap file to prevent OOM errors
#
# One-click execution: bash scripts/server/create-swap.sh
# ============================================================

set -e

echo "============================================================"
echo "💾 Creating 4GB Swap File to Prevent OOM"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SWAPFILE="/swapfile"
SWAP_SIZE="4G"

# ============================================================
# 1. Check if swap already exists
# ============================================================
echo "[1/6] Checking existing swap..."
if [ -f "$SWAPFILE" ]; then
    echo -e "${YELLOW}⚠️  Swap file already exists at $SWAPFILE${NC}"
    read -p "Do you want to remove it and create a new one? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing swap file..."
        sudo swapoff "$SWAPFILE" 2>/dev/null || true
        sudo rm -f "$SWAPFILE"
        echo -e "${GREEN}✅ Existing swap file removed${NC}"
    else
        echo -e "${YELLOW}⚠️  Keeping existing swap file. Exiting.${NC}"
        exit 0
    fi
fi

# Check if swap is already active
if swapon --show | grep -q "$SWAPFILE"; then
    echo -e "${YELLOW}⚠️  Swap is already active${NC}"
    echo "Current swap status:"
    free -h
    exit 0
fi

echo -e "${GREEN}✅ No existing swap file found${NC}"
echo ""

# ============================================================
# 2. Check available disk space
# ============================================================
echo "[2/6] Checking available disk space..."
AVAILABLE_SPACE=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 4 ]; then
    echo -e "${RED}❌ Not enough disk space. Available: ${AVAILABLE_SPACE}G, Required: 4G${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Sufficient disk space available (${AVAILABLE_SPACE}G)${NC}"
echo ""

# ============================================================
# 3. Create swap file
# ============================================================
echo "[3/6] Creating ${SWAP_SIZE} swap file..."
sudo fallocate -l "$SWAP_SIZE" "$SWAPFILE"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Swap file created${NC}"
else
    echo -e "${RED}❌ Failed to create swap file${NC}"
    exit 1
fi
echo ""

# ============================================================
# 4. Set correct permissions
# ============================================================
echo "[4/6] Setting swap file permissions..."
sudo chmod 600 "$SWAPFILE"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Permissions set${NC}"
else
    echo -e "${RED}❌ Failed to set permissions${NC}"
    exit 1
fi
echo ""

# ============================================================
# 5. Format as swap
# ============================================================
echo "[5/6] Formatting swap file..."
sudo mkswap "$SWAPFILE"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Swap file formatted${NC}"
else
    echo -e "${RED}❌ Failed to format swap file${NC}"
    exit 1
fi
echo ""

# ============================================================
# 6. Enable swap
# ============================================================
echo "[6/6] Enabling swap..."
sudo swapon "$SWAPFILE"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Swap enabled${NC}"
else
    echo -e "${RED}❌ Failed to enable swap${NC}"
    exit 1
fi
echo ""

# ============================================================
# 7. Make swap permanent
# ============================================================
echo "Making swap permanent..."
if ! grep -q "$SWAPFILE" /etc/fstab; then
    echo "$SWAPFILE none swap sw 0 0" | sudo tee -a /etc/fstab
    echo -e "${GREEN}✅ Swap added to /etc/fstab${NC}"
else
    echo -e "${YELLOW}⚠️  Swap already in /etc/fstab${NC}"
fi
echo ""

# ============================================================
# 8. Verify swap
# ============================================================
echo "============================================================"
echo -e "${GREEN}✅ Swap File Creation Complete${NC}"
echo "============================================================"
echo ""
echo "📊 Current Memory Status:"
echo ""
free -h
echo ""
echo "📝 Swap File Details:"
swapon --show
echo ""
echo "✅ Swap file is now active and will persist after reboot"
echo ""

