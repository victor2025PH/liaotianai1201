#!/bin/bash
# ============================================================
# Setup Server Git Repository (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Complete Git setup for server - check, init, or clone
# 
# One-click execution: bash scripts/server/setup-server-git.sh
# ============================================================

set -e

echo "============================================================"
echo "🔧 Setup Server Git Repository"
echo "============================================================"
echo ""

# Default repository URL (update this with your actual repository)
DEFAULT_REPO_URL="https://github.com/victor2025PH/liaotianai1201.git"

# Check if we're in the right directory
if [ ! -d "$HOME/telegram-ai-system" ]; then
    echo "📁 Creating project directory..."
    mkdir -p "$HOME/telegram-ai-system"
fi

cd "$HOME/telegram-ai-system" || exit 1

# Check if it's already a git repository
if [ -d ".git" ]; then
    echo "✅ Git repository already exists"
    echo ""
    echo "Checking remote..."
    if git remote get-url origin >/dev/null 2>&1; then
        echo "✅ Remote configured: $(git remote get-url origin)"
    else
        echo "⚠️  No remote configured"
        echo "Setting remote to: $DEFAULT_REPO_URL"
        git remote add origin "$DEFAULT_REPO_URL" 2>/dev/null || \
        git remote set-url origin "$DEFAULT_REPO_URL"
    fi
    
    echo ""
    echo "Fetching latest changes..."
    git fetch origin
    
    echo ""
    echo "Current branch: $(git branch --show-current)"
    echo ""
    echo "✅ Ready to pull updates:"
    echo "  git pull origin main"
    exit 0
fi

# Not a git repository - check if directory is empty
if [ -z "$(ls -A 2>/dev/null)" ]; then
    echo "📥 Directory is empty. Cloning repository..."
    cd "$HOME"
    git clone "$DEFAULT_REPO_URL" telegram-ai-system
    cd telegram-ai-system
    echo ""
    echo "✅ Repository cloned successfully"
    echo ""
    echo "Setting execute permissions..."
    chmod +x scripts/server/*.sh 2>/dev/null || true
    echo ""
    echo "✅ Setup complete!"
    exit 0
fi

# Directory has files but is not a git repository
echo "⚠️  Directory has files but is not a Git repository"
echo ""
echo "Initializing Git repository..."
git init
git branch -M main

echo "Adding remote: $DEFAULT_REPO_URL"
git remote add origin "$DEFAULT_REPO_URL" 2>/dev/null || \
git remote set-url origin "$DEFAULT_REPO_URL"

echo ""
echo "✅ Git repository initialized"
echo ""
echo "⚠️  Important: You have existing files that are not in Git"
echo ""
echo "Options:"
echo "  1. Pull and merge (recommended if files are different)"
echo "  2. Stash local changes and pull"
echo ""
read -p "Choose option (1 or 2, or press Enter to skip): " OPTION

case $OPTION in
    1)
        echo ""
        echo "Pulling with allow-unrelated-histories..."
        git pull origin main --allow-unrelated-histories || {
            echo "⚠️  Pull failed. You may need to resolve conflicts manually."
        }
        ;;
    2)
        echo ""
        echo "Stashing local changes..."
        git add .
        git stash
        echo "Pulling from remote..."
        git pull origin main
        echo ""
        echo "⚠️  Your local changes are stashed. To restore: git stash pop"
        ;;
    *)
        echo ""
        echo "Skipping pull. You can manually run:"
        echo "  git pull origin main --allow-unrelated-histories"
        ;;
esac

echo ""
echo "Setting execute permissions..."
chmod +x scripts/server/*.sh 2>/dev/null || true

echo ""
echo "============================================================"
echo "✅ Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  cd ~/telegram-ai-system"
echo "  git pull origin main"
echo "  chmod +x scripts/server/*.sh"
echo "  bash scripts/server/quick-start.sh"
echo ""

