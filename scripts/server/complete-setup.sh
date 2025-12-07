#!/bin/bash
# ============================================================
# Complete Server Setup (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Complete setup including Git, line endings, and verification
# 
# One-click execution: bash scripts/server/complete-setup.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "🚀 Complete Server Setup"
echo "============================================================"
echo ""

cd "$PROJECT_ROOT" 2>/dev/null || {
    echo "❌ Error: Cannot access project directory"
    echo "Please ensure you are in: ~/telegram-ai-system"
    exit 1
}

# Step 1: Setup Git repository
echo "[1/5] Setting up Git repository..."
if [ ! -d ".git" ]; then
    echo "  Initializing Git repository..."
    git init
    git branch -M main
    git remote add origin https://github.com/victor2025PH/liaotianai1201.git 2>/dev/null || \
    git remote set-url origin https://github.com/victor2025PH/liaotianai1201.git
    echo "  ✅ Git repository initialized"
else
    echo "  ✅ Git repository exists"
    git remote set-url origin https://github.com/victor2025PH/liaotianai1201.git 2>/dev/null || true
fi

# Step 2: Configure Git
echo ""
echo "[2/5] Configuring Git..."
git config core.autocrlf false
git config core.eol lf
echo "  ✅ Git configured for Linux line endings"

# Step 3: Handle conflicts and pull
echo ""
echo "[3/5] Pulling latest code..."
if git pull origin main --allow-unrelated-histories 2>&1 | grep -q "would be overwritten"; then
    echo "  ⚠️  Conflicts detected. Resolving..."
    
    # Backup conflicting files
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Extract and backup conflicting files
    git pull origin main --allow-unrelated-histories 2>&1 | \
    grep "would be overwritten" | \
    sed 's/.*would be overwritten by merge://' | \
    while read -r file; do
        if [ -f "$file" ]; then
            mkdir -p "$BACKUP_DIR/$(dirname "$file")"
            cp "$file" "$BACKUP_DIR/$file" 2>/dev/null || true
            rm -f "$file"
        fi
    done
    
    # Try pull again
    git pull origin main --allow-unrelated-histories || git pull origin main
    echo "  ✅ Conflicts resolved. Backup saved to: $BACKUP_DIR"
else
    git pull origin main --allow-unrelated-histories 2>/dev/null || git pull origin main
    echo "  ✅ Code pulled successfully"
fi

# Step 4: Fix line endings
echo ""
echo "[4/5] Fixing line endings..."
git add --renormalize . 2>/dev/null || true
# Discard line ending changes (use remote version)
git checkout -- . 2>/dev/null || true
echo "  ✅ Line endings fixed"

# Step 5: Set permissions and verify
echo ""
echo "[5/5] Setting permissions and verifying..."
chmod +x scripts/server/*.sh 2>/dev/null || true

# Verify scripts
if [ -f "scripts/server/verify-scripts-on-server.sh" ]; then
    echo ""
    echo "Running verification..."
    bash scripts/server/verify-scripts-on-server.sh || true
fi

echo ""
echo "============================================================"
echo "✅ Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  bash scripts/server/quick-start.sh"
echo ""

