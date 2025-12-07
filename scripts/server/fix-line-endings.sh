#!/bin/bash
# ============================================================
# Fix Line Endings (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Fix CRLF/LF line ending issues in scripts
# 
# One-click execution: bash scripts/server/fix-line-endings.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "🔧 Fix Line Endings"
echo "============================================================"
echo ""

cd "$PROJECT_ROOT"

# Configure Git to handle line endings
echo "[1/3] Configuring Git line endings..."
git config core.autocrlf false
git config core.eol lf

echo ""
echo "[2/3] Refreshing Git index..."
git add --renormalize .

echo ""
echo "[3/3] Checking for modified files..."
MODIFIED=$(git status --short | wc -l)

if [ "$MODIFIED" -gt 0 ]; then
    echo "Found $MODIFIED modified files (likely line ending changes)"
    echo ""
    echo "Options:"
    echo "  1. Commit the changes"
    echo "  2. Discard the changes (use remote version)"
    echo ""
    read -p "Choose option (1/2): " OPTION
    
    case $OPTION in
        1)
            echo ""
            echo "Committing line ending fixes..."
            git commit -m "Fix line endings (CRLF to LF)"
            echo "✅ Changes committed"
            ;;
        2)
            echo ""
            echo "Discarding local changes..."
            git checkout -- .
            echo "✅ Changes discarded"
            ;;
        *)
            echo "⚠️  No action taken"
            ;;
    esac
else
    echo "✅ No line ending issues detected"
fi

echo ""
echo "Setting execute permissions..."
chmod +x scripts/server/*.sh 2>/dev/null || true

echo ""
echo "============================================================"
echo "✅ Fix Complete!"
echo "============================================================"

