#!/bin/bash
# Server-side script to verify and pull all scripts from GitHub

set -e

echo "========================================"
echo "Verify and Pull Scripts from GitHub"
echo "========================================"
echo ""

cd ~/liaotian || {
    echo "❌ Cannot enter project directory"
    exit 1
}

# Ensure on main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo "Switching to main branch..."
    git checkout main
fi

# Fetch latest
echo "Fetching latest from GitHub..."
git fetch origin main

# Pull latest code
echo "Pulling latest code..."
git pull origin main

# List all .sh files in scripts directory from remote
echo ""
echo "Available scripts in remote repository:"
git ls-tree -r origin/main --name-only scripts/ | grep "\.sh$" || echo "No .sh files found in scripts/"

echo ""
echo "Available scripts in deploy directory from remote:"
git ls-tree -r origin/main --name-only deploy/ | grep "\.sh$" || echo "No .sh files found in deploy/"

# Try to checkout specific scripts
echo ""
echo "Checking out scripts..."
SCRIPTS=(
    "scripts/full_auto_complete.sh"
    "scripts/complete_automation.sh"
    "scripts/one_click_deploy.sh"
    "scripts/unify_branches_server.sh"
    "deploy/fix_and_deploy_frontend_complete.sh"
)

mkdir -p scripts deploy

for script in "${SCRIPTS[@]}"; do
    echo ""
    echo "Checking: $script"
    
    # Check if exists in remote
    if git ls-tree -r origin/main --name-only | grep -q "^$script$"; then
        echo "  ✓ Found in remote repository"
        
        # Try to checkout
        if git checkout origin/main -- "$script" 2>/dev/null; then
            echo "  ✓ Successfully checked out"
            chmod +x "$script" 2>/dev/null || true
            echo "  ✓ Added execute permission"
        else
            echo "  ✗ Failed to checkout"
        fi
    else
        echo "  ✗ NOT found in remote repository"
        echo "  Checking alternative paths..."
        
        # Try to find similar files
        ALTERNATIVES=$(git ls-tree -r origin/main --name-only | grep "$(basename "$script")" || true)
        if [[ -n "$ALTERNATIVES" ]]; then
            echo "  Found similar files:"
            echo "$ALTERNATIVES" | sed 's/^/    /'
        fi
    fi
done

echo ""
echo "========================================"
echo "Final Status:"
echo "========================================"

echo ""
echo "Scripts in scripts/ directory:"
ls -la scripts/*.sh 2>/dev/null || echo "No .sh files found"

echo ""
echo "Scripts in deploy/ directory:"
ls -la deploy/*.sh 2>/dev/null | head -10 || echo "No .sh files found"
