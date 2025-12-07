#!/bin/bash
# ============================================================
# Fix Local Changes and Pull (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Resolve local changes and pull latest code
# 
# One-click execution: bash scripts/server/fix-and-pull.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "🔧 Fix Local Changes and Pull"
echo "============================================================"
echo ""

cd "$PROJECT_ROOT"

# Check if it's a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a Git repository"
    exit 1
fi

echo "[1/3] Checking for local changes..."
if git status --porcelain | grep -qv "^??"; then
    echo "⚠️  Found local changes. Stashing..."
    git stash push -m "Auto-stashed before pull $(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    echo "✅ Local changes stashed"
else
    echo "✅ No local changes"
fi

echo ""
echo "[2/3] Pulling latest code..."
git pull origin main || {
    echo "⚠️  Pull failed, trying with allow-unrelated-histories..."
    git pull origin main --allow-unrelated-histories || {
        echo "❌ Pull failed. Please check manually."
        exit 1
    }
}

echo ""
echo "[3/3] Setting execute permissions..."
chmod +x scripts/server/*.sh 2>/dev/null || true
chmod +x deploy/systemd/*.sh 2>/dev/null || true

echo ""
echo "============================================================"
echo "✅ Pull Complete!"
echo "============================================================"
echo ""
echo "You can now run:"
echo "  bash scripts/server/quick-deploy-setup.sh"
echo ""

