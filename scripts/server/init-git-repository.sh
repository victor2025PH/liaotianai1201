#!/bin/bash
# ============================================================
# Initialize Git Repository on Server (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Initialize Git repository or clone from GitHub if not exists
# 
# One-click execution: bash scripts/server/init-git-repository.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "🔧 Initialize Git Repository on Server"
echo "============================================================"
echo ""

cd "$PROJECT_ROOT" 2>/dev/null || {
    echo "❌ Error: Cannot access project root directory"
    echo ""
    echo "Please ensure you are in the project directory:"
    echo "  cd ~/telegram-ai-system"
    exit 1
}

# Check if .git directory exists
if [ -d ".git" ]; then
    echo "✅ Git repository already exists"
    echo ""
    echo "Checking remote configuration..."
    git remote -v || {
        echo "⚠️  No remote configured. Adding origin..."
        read -p "Enter GitHub repository URL (e.g., https://github.com/user/repo.git): " REPO_URL
        if [ -n "$REPO_URL" ]; then
            git remote add origin "$REPO_URL"
            echo "✅ Remote added: $REPO_URL"
        fi
    }
    echo ""
    echo "Current status:"
    git status --short
    echo ""
    echo "You can now run:"
    echo "  git pull origin main"
    exit 0
fi

# If not a git repository, check if directory is empty
if [ -z "$(ls -A)" ]; then
    echo "📁 Directory is empty. Cloning from GitHub..."
    echo ""
    read -p "Enter GitHub repository URL (e.g., https://github.com/user/repo.git): " REPO_URL
    if [ -z "$REPO_URL" ]; then
        echo "❌ Error: Repository URL is required"
        exit 1
    fi
    
    cd ..
    git clone "$REPO_URL" telegram-ai-system
    cd telegram-ai-system
    echo ""
    echo "✅ Repository cloned successfully"
    exit 0
fi

# Directory has files but is not a git repository
echo "⚠️  Directory exists but is not a Git repository"
echo ""
echo "Options:"
echo "  1. Initialize new repository (will keep existing files)"
echo "  2. Clone from GitHub (will overwrite existing files)"
echo ""
read -p "Choose option (1 or 2): " OPTION

case $OPTION in
    1)
        echo ""
        echo "Initializing Git repository..."
        git init
        git branch -M main
        
        read -p "Enter GitHub repository URL (e.g., https://github.com/user/repo.git): " REPO_URL
        if [ -n "$REPO_URL" ]; then
            git remote add origin "$REPO_URL"
            echo "✅ Remote added: $REPO_URL"
        fi
        
        echo ""
        echo "✅ Git repository initialized"
        echo ""
        echo "Next steps:"
        echo "  1. Add files: git add ."
        echo "  2. Commit: git commit -m 'Initial commit'"
        echo "  3. Push: git push -u origin main"
        echo ""
        echo "Or pull from remote:"
        echo "  git pull origin main --allow-unrelated-histories"
        ;;
    2)
        echo ""
        read -p "⚠️  This will overwrite existing files. Continue? (y/N): " CONFIRM
        if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
            echo "Cancelled"
            exit 0
        fi
        
        read -p "Enter GitHub repository URL (e.g., https://github.com/user/repo.git): " REPO_URL
        if [ -z "$REPO_URL" ]; then
            echo "❌ Error: Repository URL is required"
            exit 1
        fi
        
        cd ..
        rm -rf telegram-ai-system
        git clone "$REPO_URL" telegram-ai-system
        cd telegram-ai-system
        echo ""
        echo "✅ Repository cloned successfully"
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

# ============================================================
# Step-by-step execution instructions:
# ============================================================
# 
# Option 1: Initialize new repository
#   cd ~/telegram-ai-system
#   git init
#   git branch -M main
#   git remote add origin https://github.com/user/repo.git
#   git pull origin main --allow-unrelated-histories
# 
# Option 2: Clone from GitHub
#   cd ~
#   rm -rf telegram-ai-system
#   git clone https://github.com/user/repo.git telegram-ai-system
#   cd telegram-ai-system
# ============================================================

