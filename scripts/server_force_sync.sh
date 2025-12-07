#!/bin/bash
# Server Force Sync: Pull all files from GitHub and fix all issues

set -e

echo "========================================"
echo "Server Force Sync - Complete Solution"
echo "========================================"
echo ""

cd ~/liaotian || {
    echo "❌ Cannot enter project directory"
    exit 1
}

# Step 1: Force sync with remote
echo "=== Step 1: Force Sync with Remote ==="
git checkout main 2>/dev/null || git checkout -b main origin/main
git fetch origin main
git reset --hard origin/main
git clean -fd
echo "✅ Code synced"

# Step 2: Create directories
echo ""
echo "=== Step 2: Create Directories ==="
mkdir -p scripts deploy saas-demo/src/components/ui
echo "✅ Directories created"

# Step 3: Checkout all script files from remote
echo ""
echo "=== Step 3: Checkout All Script Files ==="
SCRIPT_COUNT=0

# Get all .sh files from remote
git ls-tree -r origin/main --name-only | grep "\.sh$" | while read file; do
    DIR=$(dirname "$file")
    mkdir -p "$DIR"
    
    if git checkout origin/main -- "$file" 2>/dev/null; then
        chmod +x "$file" 2>/dev/null || true
        echo "✅ $file"
        SCRIPT_COUNT=$((SCRIPT_COUNT + 1))
    fi
done

echo "Checked out $SCRIPT_COUNT script files"

# Step 4: Checkout slider component
echo ""
echo "=== Step 4: Checkout Slider Component ==="
if git checkout origin/main -- saas-demo/src/components/ui/slider.tsx 2>/dev/null; then
    echo "✅ Slider component checked out"
else
    echo "⚠️  Slider component not in remote, checking alternative locations..."
    # Try to find slider file
    git ls-tree -r origin/main --name-only | grep -i slider
fi

# Step 5: Fix frontend dependencies
echo ""
echo "=== Step 5: Fix Frontend Dependencies ==="
if [[ -d "saas-demo" ]]; then
    cd saas-demo
    
    # Ensure package.json is latest
    git checkout origin/main -- package.json 2>/dev/null || true
    
    # Check if slider dependency exists
    if ! grep -q "@radix-ui/react-slider" package.json; then
        echo "Adding slider dependency..."
        npm install @radix-ui/react-slider --save
    fi
    
    # Install all dependencies
    echo "Installing all dependencies..."
    npm install
    
    cd ..
    echo "✅ Dependencies installed"
else
    echo "⚠️  Frontend directory not found"
fi

# Step 6: Verify all key files
echo ""
echo "=== Step 6: Verify Key Files ==="
KEY_FILES=(
    "scripts/server_git_check.sh"
    "scripts/one_click_deploy.sh"
    "deploy/fix_and_deploy_frontend_complete.sh"
    "saas-demo/src/components/ui/slider.tsx"
)

ALL_EXIST=true
for file in "${KEY_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
        ALL_EXIST=false
    fi
done

# Step 7: Cleanup master branch
echo ""
echo "=== Step 7: Cleanup Master Branch ==="
if git show-ref --verify --quiet refs/heads/master; then
    git branch -D master 2>/dev/null || true
    echo "✅ Master branch deleted"
else
    echo "✅ Master branch does not exist"
fi

# Final status
echo ""
echo "========================================"
echo "Final Status"
echo "========================================"
echo ""
echo "Branch: $(git rev-parse --abbrev-ref HEAD)"
echo "Commit: $(git log -1 --oneline)"
echo ""
echo "Files Status:"
if [[ "$ALL_EXIST" == true ]]; then
    echo "✅ All key files exist"
else
    echo "⚠️  Some files are missing"
fi

echo ""
echo "Next steps:"
echo "  1. Verify files: ls -la scripts/*.sh deploy/*.sh"
echo "  2. Build frontend: cd saas-demo && npm run build"
echo "  3. Deploy: bash deploy/fix_and_deploy_frontend_complete.sh"
