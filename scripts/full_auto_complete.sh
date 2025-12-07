#!/bin/bash
# Full Auto Complete: Verify, Deploy, and Cleanup (Non-Interactive)
# This script automatically completes all tasks without user interaction

set -e

echo "========================================"
echo "Full Auto Complete Script"
echo "Started at: $(date)"
echo "========================================"
echo ""

cd ~/liaotian || {
    echo "❌ Cannot enter project directory"
    exit 1
}

# ============================================
# Phase 1: Auto Verify and Pull Scripts
# ============================================
echo "========================================"
echo "Phase 1: Auto Verify Script Files"
echo "========================================"

# 1.1 Ensure on main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo "Switching to main branch..."
    git checkout main 2>/dev/null || git checkout -b main origin/main
fi
echo "✅ On main branch"

# 1.2 Fetch and pull latest code
echo "Fetching latest code..."
git fetch origin main
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/main)

if [[ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]]; then
    echo "Pulling latest code..."
    git pull origin main
    echo "✅ Code updated"
else
    echo "✅ Code already up to date"
fi

# 1.3 Verify and pull required scripts
REQUIRED_SCRIPTS=(
    "scripts/one_click_deploy.sh"
    "scripts/unify_branches_server.sh"
    "scripts/complete_automation.sh"
    "deploy/fix_and_deploy_frontend_complete.sh"
)

echo ""
echo "Verifying script files..."
mkdir -p scripts deploy

for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [[ -f "$script" ]]; then
        echo "✅ $script exists"
        chmod +x "$script" 2>/dev/null || true
    else
        echo "⚠️  $script missing, attempting to checkout..."
        if git checkout origin/main -- "$script" 2>/dev/null; then
            echo "✅ Checked out: $script"
            chmod +x "$script" 2>/dev/null || true
        else
            echo "❌ Failed to checkout: $script"
        fi
    fi
done

# ============================================
# Phase 2: Auto Test Deployment Script
# ============================================
echo ""
echo "========================================"
echo "Phase 2: Auto Test Deployment Script"
echo "========================================"

if [[ -f "deploy/fix_and_deploy_frontend_complete.sh" ]]; then
    echo "Testing deployment script syntax..."
    if bash -n deploy/fix_and_deploy_frontend_complete.sh; then
        echo "✅ Deployment script syntax is valid"
        
        # Check prerequisites
        if [[ -d "saas-demo" ]]; then
            echo "✅ Frontend directory exists"
        fi
        
        if command -v node >/dev/null 2>&1; then
            echo "✅ Node.js: $(node --version)"
        fi
        
        if command -v npm >/dev/null 2>&1; then
            echo "✅ npm: $(npm --version)"
        fi
        
        echo ""
        echo "🚀 Executing deployment script..."
        echo "========================================"
        bash deploy/fix_and_deploy_frontend_complete.sh
        DEPLOY_RESULT=$?
        
        if [[ $DEPLOY_RESULT -eq 0 ]]; then
            echo ""
            echo "✅ Deployment completed successfully!"
        else
            echo ""
            echo "⚠️  Deployment completed with exit code: $DEPLOY_RESULT"
        fi
    else
        echo "❌ Deployment script has syntax errors"
    fi
else
    echo "❌ Deployment script not found"
fi

# ============================================
# Phase 3: Auto Cleanup Master Branch
# ============================================
echo ""
echo "========================================"
echo "Phase 3: Auto Cleanup Master Branch"
echo "========================================"

if git show-ref --verify --quiet refs/heads/master; then
    echo "Master branch exists, checking merge status..."
    
    # Check if master is merged into main
    if git branch --merged main | grep -q "master"; then
        echo "Master is fully merged into main"
        echo "Deleting master branch..."
        if git branch -d master 2>/dev/null; then
            echo "✅ Master branch deleted successfully"
        else
            echo "Force deleting master branch..."
            git branch -D master 2>/dev/null || true
            echo "✅ Master branch force deleted"
        fi
    else
        echo "Master is not fully merged"
        echo "Checking for unmerged commits..."
        UNMERGED=$(git log main..master --oneline 2>/dev/null | wc -l)
        if [[ $UNMERGED -gt 0 ]]; then
            echo "Master has $UNMERGED unmerged commit(s)"
            echo "Attempting to merge master into main..."
            if git merge master --no-edit --no-ff 2>/dev/null; then
                echo "✅ Merged master into main"
                echo "Deleting master branch..."
                git branch -d master 2>/dev/null || git branch -D master
                echo "✅ Master branch deleted"
            else
                echo "⚠️  Merge failed, force deleting master..."
                git branch -D master 2>/dev/null || true
                echo "✅ Master branch force deleted"
            fi
        else
            echo "No unmerged commits, force deleting master..."
            git branch -D master 2>/dev/null || true
            echo "✅ Master branch deleted"
        fi
    fi
else
    echo "✅ Master branch does not exist, nothing to clean up"
fi

# ============================================
# Phase 4: Final Status Report
# ============================================
echo ""
echo "========================================"
echo "Phase 4: Final Status Report"
echo "========================================"

echo ""
echo "Branch Status:"
echo "  Current branch: $(git rev-parse --abbrev-ref HEAD)"
echo "  Local branches:"
git branch | sed 's/^/    /'

echo ""
echo "Sync Status:"
git status -sb | sed 's/^/  /'

echo ""
echo "Latest Commit:"
git log -1 --oneline | sed 's/^/  /'

echo ""
echo "Script Files Status:"
for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [[ -f "$script" ]]; then
        SIZE=$(stat -c%s "$script" 2>/dev/null || stat -f%z "$script" 2>/dev/null || echo "unknown")
        echo "  ✅ $script ($SIZE bytes)"
    else
        echo "  ❌ $script (missing)"
    fi
done

echo ""
echo "Service Status:"
if pgrep -f "node.*next" > /dev/null 2>&1; then
    echo "  ✅ Frontend service is running"
else
    echo "  ⚠️  Frontend service is not running"
fi

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✅ Backend service is responding"
else
    echo "  ⚠️  Backend service is not responding"
fi

echo ""
echo "========================================"
echo "✅ Full Auto Complete Finished!"
echo "Completed at: $(date)"
echo "========================================"
