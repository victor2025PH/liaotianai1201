#!/bin/bash
# ============================================================
# Fix Git Pull Conflicts (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Handle untracked files conflict during git pull
# 
# One-click execution: bash scripts/server/fix-git-pull-conflicts.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "🔧 Fix Git Pull Conflicts"
echo "============================================================"
echo ""

cd "$PROJECT_ROOT"

# Check if it's a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a Git repository"
    echo "Please run: bash scripts/server/setup-server-git.sh"
    exit 1
fi

echo "[1/4] Checking for untracked files that would conflict..."
CONFLICT_FILES=$(git pull origin main --allow-unrelated-histories 2>&1 | grep "would be overwritten" | sed 's/.*would be overwritten by merge://' | tr '\n' ' ')

if [ -z "$CONFLICT_FILES" ]; then
    echo "✅ No conflicts detected. Pulling..."
    git pull origin main --allow-unrelated-histories || git pull origin main
    echo "✅ Pull successful"
    exit 0
fi

echo ""
echo "⚠️  Found conflicting untracked files"
echo ""
echo "Options:"
echo "  1. Backup and remove conflicting files (recommended)"
echo "  2. Stash local changes and pull"
echo "  3. Force overwrite with remote version"
echo ""
read -p "Choose option (1/2/3): " OPTION

case $OPTION in
    1)
        echo ""
        echo "[2/4] Creating backup..."
        BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        # Extract file list from error message
        git pull origin main --allow-unrelated-histories 2>&1 | \
        grep "would be overwritten" | \
        sed 's/.*would be overwritten by merge://' | \
        while read -r file; do
            if [ -f "$file" ]; then
                mkdir -p "$BACKUP_DIR/$(dirname "$file")"
                cp "$file" "$BACKUP_DIR/$file"
                echo "  ✓ Backed up: $file"
            fi
        done
        
        echo ""
        echo "[3/4] Removing conflicting files..."
        git pull origin main --allow-unrelated-histories 2>&1 | \
        grep "would be overwritten" | \
        sed 's/.*would be overwritten by merge://' | \
        while read -r file; do
            if [ -f "$file" ]; then
                rm -f "$file"
                echo "  ✓ Removed: $file"
            fi
        done
        
        echo ""
        echo "[4/4] Pulling from remote..."
        git pull origin main --allow-unrelated-histories || git pull origin main
        echo ""
        echo "✅ Pull successful!"
        echo "📦 Backup saved to: $BACKUP_DIR"
        ;;
    2)
        echo ""
        echo "[2/4] Stashing local changes..."
        git add -A
        git stash
        
        echo ""
        echo "[3/4] Pulling from remote..."
        git pull origin main --allow-unrelated-histories || git pull origin main
        
        echo ""
        echo "[4/4] Restoring stashed changes..."
        git stash pop || true
        
        echo ""
        echo "✅ Pull successful!"
        echo "⚠️  Your local changes are in stash. Review with: git stash list"
        ;;
    3)
        echo ""
        echo "[2/4] Removing conflicting files..."
        git pull origin main --allow-unrelated-histories 2>&1 | \
        grep "would be overwritten" | \
        sed 's/.*would be overwritten by merge://' | \
        while read -r file; do
            if [ -f "$file" ]; then
                rm -f "$file"
                echo "  ✓ Removed: $file"
            fi
        done
        
        echo ""
        echo "[3/4] Pulling from remote..."
        git pull origin main --allow-unrelated-histories || git pull origin main
        
        echo ""
        echo "✅ Pull successful!"
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
echo "✅ Fix Complete!"
echo "============================================================"

