#!/bin/bash
# Complete diagnosis and fix for local-GitHub-server sync issues

set -e

echo "========================================"
echo "Complete Diagnosis and Fix"
echo "========================================"
echo ""

cd ~/liaotian || {
    echo "❌ Cannot enter project directory"
    exit 1
}

# ============================================
# Phase 1: Diagnose Current State
# ============================================
echo "========================================"
echo "Phase 1: Diagnose Current State"
echo "========================================"

# 1.1 Check branch
echo ""
echo "=== 1.1 Current Branch ==="
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"

if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo "⚠️  Not on main branch, switching..."
    git checkout main 2>/dev/null || git checkout -b main origin/main
fi

# 1.2 Check sync status
echo ""
echo "=== 1.2 Sync Status ==="
git fetch origin main
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/main)
echo "Local commit:  $LOCAL_COMMIT"
echo "Remote commit: $REMOTE_COMMIT"

if [[ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]]; then
    echo "⚠️  Local and remote are out of sync"
    NEEDS_PULL=true
else
    echo "✅ Local and remote are in sync"
    NEEDS_PULL=false
fi

# 1.3 Check files in remote vs local
echo ""
echo "=== 1.3 File Comparison ==="
echo "Checking key files..."

KEY_FILES=(
    "scripts/server_git_check.sh"
    "scripts/one_click_deploy.sh"
    "scripts/unify_branches_server.sh"
    "deploy/fix_and_deploy_frontend_complete.sh"
    "saas-demo/src/components/ui/slider.tsx"
)

MISSING_FILES=()
for file in "${KEY_FILES[@]}"; do
    # Check in remote
    if git ls-tree -r origin/main --name-only | grep -q "^$file$"; then
        echo "  ✅ $file exists in remote"
        
        # Check locally
        if [[ -f "$file" ]]; then
            echo "     ✅ Also exists locally"
        else
            echo "     ❌ Missing locally!"
            MISSING_FILES+=("$file")
        fi
    else
        echo "  ❌ $file NOT in remote"
        MISSING_FILES+=("$file")
    fi
done

# ============================================
# Phase 2: Fix Sync Issues
# ============================================
echo ""
echo "========================================"
echo "Phase 2: Fix Sync Issues"
echo "========================================"

# 2.1 Pull latest code
if [[ "$NEEDS_PULL" == true ]]; then
    echo ""
    echo "=== 2.1 Pulling Latest Code ==="
    git pull origin main
    echo "✅ Code pulled"
fi

# 2.2 Force checkout missing files
if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
    echo ""
    echo "=== 2.2 Checking Out Missing Files ==="
    mkdir -p scripts deploy saas-demo/src/components/ui
    
    for file in "${MISSING_FILES[@]}"; do
        echo "Checking out: $file"
        if git checkout origin/main -- "$file" 2>/dev/null; then
            echo "  ✅ Successfully checked out"
            
            # Add execute permission for scripts
            if [[ "$file" == *.sh ]]; then
                chmod +x "$file"
            fi
        else
            echo "  ❌ Failed to checkout"
        fi
    done
fi

# 2.3 Verify all files now exist
echo ""
echo "=== 2.3 Final File Verification ==="
ALL_EXIST=true
for file in "${KEY_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file still missing"
        ALL_EXIST=false
    fi
done

if [[ "$ALL_EXIST" == false ]]; then
    echo ""
    echo "⚠️  Some files are still missing. They may not be in the remote repository."
fi

# ============================================
# Phase 3: Fix Frontend Build
# ============================================
echo ""
echo "========================================"
echo "Phase 3: Fix Frontend Build"
echo "========================================"

if [[ -d "saas-demo" ]]; then
    cd saas-demo
    
    echo ""
    echo "=== 3.1 Check Slider Component ==="
    if [[ -f "src/components/ui/slider.tsx" ]]; then
        echo "✅ Slider component exists"
    else
        echo "❌ Slider component missing"
        echo "This will cause build failure"
    fi
    
    echo ""
    echo "=== 3.2 Check Dependencies ==="
    if grep -q "@radix-ui/react-slider" package.json; then
        echo "✅ @radix-ui/react-slider in package.json"
    else
        echo "⚠️  @radix-ui/react-slider not in package.json"
        echo "Adding dependency..."
        npm install @radix-ui/react-slider
    fi
    
    echo ""
    echo "=== 3.3 Install All Dependencies ==="
    npm install
    
    echo ""
    echo "=== 3.4 Clean and Build ==="
    rm -rf .next node_modules/.cache
    echo "Building frontend..."
    
    if npm run build; then
        echo "✅ Frontend build successful"
        BUILD_SUCCESS=true
    else
        echo "❌ Frontend build failed"
        BUILD_SUCCESS=false
    fi
    
    cd ..
else
    echo "⚠️  Frontend directory not found"
    BUILD_SUCCESS=false
fi

# ============================================
# Phase 4: Cleanup Master Branch
# ============================================
echo ""
echo "========================================"
echo "Phase 4: Cleanup Master Branch"
echo "========================================"

if git show-ref --verify --quiet refs/heads/master; then
    echo "Master branch exists"
    
    # Check if merged
    if git branch --merged main | grep -q "master"; then
        echo "Master is merged into main, deleting..."
        git branch -d master 2>/dev/null || git branch -D master
        echo "✅ Master branch deleted"
    else
        echo "Master is not fully merged"
        echo "Force deleting master branch..."
        git branch -D master 2>/dev/null || true
        echo "✅ Master branch deleted"
    fi
else
    echo "✅ Master branch does not exist"
fi

# ============================================
# Phase 5: Final Status Report
# ============================================
echo ""
echo "========================================"
echo "Phase 5: Final Status Report"
echo "========================================"

echo ""
echo "Branch Status:"
echo "  Current: $(git rev-parse --abbrev-ref HEAD)"
echo "  Local branches:"
git branch | sed 's/^/    /'

echo ""
echo "Sync Status:"
git status -sb | sed 's/^/  /'

echo ""
echo "Latest Commit:"
git log -1 --oneline | sed 's/^/  /'

echo ""
echo "Key Files Status:"
for file in "${KEY_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        SIZE=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null || echo "?")
        echo "  ✅ $file ($SIZE bytes)"
    else
        echo "  ❌ $file (missing)"
    fi
done

echo ""
echo "Build Status:"
if [[ "$BUILD_SUCCESS" == true ]]; then
    echo "  ✅ Frontend build: SUCCESS"
else
    echo "  ❌ Frontend build: FAILED"
fi

echo ""
echo "========================================"
if [[ "$ALL_EXIST" == true && "$BUILD_SUCCESS" == true ]]; then
    echo "✅ All Checks Passed!"
else
    echo "⚠️  Some Issues Remain"
    echo ""
    if [[ "$ALL_EXIST" == false ]]; then
        echo "- Some files are missing"
    fi
    if [[ "$BUILD_SUCCESS" == false ]]; then
        echo "- Frontend build failed"
    fi
fi
echo "========================================"
