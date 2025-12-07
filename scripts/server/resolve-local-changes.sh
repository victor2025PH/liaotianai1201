#!/bin/bash
# ============================================================
# Resolve Local Changes (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Resolve local changes that prevent git pull
# 
# One-click execution: bash scripts/server/resolve-local-changes.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "🔧 Resolve Local Changes"
echo "============================================================"
echo ""

cd "$PROJECT_ROOT"

# Check if it's a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a Git repository"
    exit 1
fi

echo "[1/3] Checking for local changes..."
CHANGED_FILES=$(git status --porcelain | grep -v "^??" | wc -l)

if [ "$CHANGED_FILES" -eq 0 ]; then
    echo "✅ No local changes detected"
    echo ""
    echo "You can now run:"
    echo "  git pull origin main"
    exit 0
fi

echo "⚠️  Found $CHANGED_FILES files with local changes"
echo ""
git status --short

echo ""
echo "Options:"
echo "  1. Stash local changes (recommended - keeps your changes)"
echo "  2. Discard local changes (use remote version)"
echo "  3. Commit local changes first"
echo ""
read -p "Choose option (1/2/3): " OPTION

case $OPTION in
    1)
        echo ""
        echo "[2/3] Stashing local changes..."
        git stash push -m "Stashed before pull $(date +%Y%m%d_%H%M%S)"
        echo "✅ Changes stashed"
        
        echo ""
        echo "[3/3] Pulling from remote..."
        git pull origin main
        echo "✅ Pull successful"
        
        echo ""
        echo "⚠️  Your local changes are in stash."
        echo "To restore: git stash pop"
        echo "To view: git stash list"
        ;;
    2)
        echo ""
        echo "[2/3] Discarding local changes..."
        git checkout -- .
        git clean -fd
        echo "✅ Local changes discarded"
        
        echo ""
        echo "[3/3] Pulling from remote..."
        git pull origin main
        echo "✅ Pull successful"
        ;;
    3)
        echo ""
        echo "[2/3] Committing local changes..."
        git add -A
        git commit -m "Local changes before pull $(date +%Y%m%d_%H%M%S)"
        echo "✅ Changes committed"
        
        echo ""
        echo "[3/3] Pulling from remote..."
        git pull origin main --no-edit || {
            echo "⚠️  Merge conflict detected. Resolving..."
            git merge --abort 2>/dev/null || true
            echo "Please resolve conflicts manually or choose option 1 or 2"
        }
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "Setting execute permissions..."
chmod +x scripts/server/*.sh 2>/dev/null || true

echo ""
echo "============================================================"
echo "✅ Resolution Complete!"
echo "============================================================"

