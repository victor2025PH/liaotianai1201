#!/bin/bash
# ============================================================
# Force Pull Latest (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Force pull latest code, resolving all conflicts
# 
# One-click execution: bash scripts/server/force-pull-latest.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "🔄 Force Pull Latest Code"
echo "============================================================"
echo ""

cd "$PROJECT_ROOT"

# Check if it's a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a Git repository"
    echo "Please run: bash scripts/server/setup-server-git.sh"
    exit 1
fi

echo "[1/4] Stashing all local changes..."
git stash push -m "Auto-stashed before force pull $(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
echo "✅ Local changes stashed"

echo ""
echo "[2/4] Fetching latest from remote..."
git fetch origin main
echo "✅ Fetched successfully"

echo ""
echo "[3/4] Resetting to remote version..."
git reset --hard origin/main
echo "✅ Reset to remote version"

echo ""
echo "[4/4] Cleaning untracked files..."
git clean -fd
echo "✅ Cleaned untracked files"

echo ""
echo "Setting execute permissions..."
chmod +x scripts/server/*.sh 2>/dev/null || true

echo ""
echo "============================================================"
echo "✅ Force Pull Complete!"
echo "============================================================"
echo ""
echo "Your local changes are in stash. To restore:"
echo "  git stash list"
echo "  git stash pop"
echo ""
echo "To verify scripts:"
echo "  bash scripts/server/verify-scripts-on-server.sh"
echo ""

