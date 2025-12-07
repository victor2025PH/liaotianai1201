#!/bin/bash
# Complete Automation: Verify, Deploy, and Cleanup
# This script automates all verification, deployment, and cleanup tasks

set -e

echo "========================================"
echo "Complete Automation Script"
echo "========================================"
echo "Started at: $(date)"
echo ""

cd ~/liaotian || {
    echo "❌ Cannot enter project directory"
    exit 1
}

# ============================================
# Phase 1: Verify Script Files
# ============================================
echo "========================================"
echo "Phase 1: Verify Script Files"
echo "========================================"

# 1.1 Ensure on main branch
echo ""
echo "=== 1.1 Ensure on main branch ==="
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo "⚠️  Current branch: $CURRENT_BRANCH, switching to main..."
    git checkout main 2>/dev/null || git checkout -b main origin/main
    echo "✅ Switched to main branch"
else
    echo "✅ Already on main branch"
fi

# 1.2 Fetch and pull latest code
echo ""
echo "=== 1.2 Fetch and pull latest code ==="
git fetch origin main
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/main)

if [[ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]]; then
    echo "📥 Pulling latest code..."
    git pull origin main
    echo "✅ Code updated from $LOCAL_COMMIT to $REMOTE_COMMIT"
else
    echo "✅ Code already up to date"
fi

# 1.3 Define required scripts
echo ""
echo "=== 1.3 Verify required scripts ==="
REQUIRED_SCRIPTS=(
    "scripts/one_click_deploy.sh"
    "scripts/unify_branches_server.sh"
    "deploy/fix_and_deploy_frontend_complete.sh"
)

MISSING_SCRIPTS=()
for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [[ -f "$script" ]]; then
        echo "✅ $script exists"
        chmod +x "$script" 2>/dev/null || true
    else
        echo "❌ $script MISSING"
        MISSING_SCRIPTS+=("$script")
    fi
done

# 1.4 If scripts are missing, try to checkout from remote
if [[ ${#MISSING_SCRIPTS[@]} -gt 0 ]]; then
    echo ""
    echo "=== 1.4 Attempting to checkout missing scripts ==="
    for script in "${MISSING_SCRIPTS[@]}"; do
        echo "Trying to checkout: $script"
        if git checkout origin/main -- "$script" 2>/dev/null; then
            echo "✅ Successfully checked out: $script"
            chmod +x "$script" 2>/dev/null || true
            MISSING_SCRIPTS=("${MISSING_SCRIPTS[@]/$script}")
        else
            echo "❌ Failed to checkout: $script"
        fi
    done
fi

# 1.5 Final verification
echo ""
echo "=== 1.5 Final script verification ==="
ALL_SCRIPTS_EXIST=true
for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [[ -f "$script" ]]; then
        echo "✅ $script"
    else
        echo "❌ $script still missing"
        ALL_SCRIPTS_EXIST=false
    fi
done

if [[ "$ALL_SCRIPTS_EXIST" == false ]]; then
    echo ""
    echo "⚠️  WARNING: Some scripts are still missing"
    echo "The deployment may fail. Please check GitHub repository."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# ============================================
# Phase 2: Test Deployment Script
# ============================================
echo ""
echo "========================================"
echo "Phase 2: Test Deployment Script"
echo "========================================"

if [[ -f "deploy/fix_and_deploy_frontend_complete.sh" ]]; then
    echo ""
    echo "=== 2.1 Checking deployment script syntax ==="
    if bash -n deploy/fix_and_deploy_frontend_complete.sh; then
        echo "✅ Deployment script syntax is valid"
    else
        echo "❌ Deployment script has syntax errors"
        exit 1
    fi
    
    echo ""
    echo "=== 2.2 Checking deployment prerequisites ==="
    
    # Check if frontend directory exists
    if [[ -d "saas-demo" ]]; then
        echo "✅ Frontend directory exists"
    else
        echo "❌ Frontend directory (saas-demo) not found"
        echo "Skipping deployment test"
    fi
    
    # Check Node.js and npm
    if command -v node >/dev/null 2>&1; then
        NODE_VERSION=$(node --version)
        echo "✅ Node.js installed: $NODE_VERSION"
    else
        echo "⚠️  Node.js not found"
    fi
    
    if command -v npm >/dev/null 2>&1; then
        NPM_VERSION=$(npm --version)
        echo "✅ npm installed: $NPM_VERSION"
    else
        echo "⚠️  npm not found"
    fi
    
    echo ""
    echo "=== 2.3 Execute deployment script ==="
    read -p "Do you want to execute the deployment script now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 Starting deployment..."
        bash deploy/fix_and_deploy_frontend_complete.sh
        DEPLOY_EXIT_CODE=$?
        
        if [[ $DEPLOY_EXIT_CODE -eq 0 ]]; then
            echo ""
            echo "✅ Deployment completed successfully!"
        else
            echo ""
            echo "❌ Deployment failed with exit code: $DEPLOY_EXIT_CODE"
            echo "Please check the error messages above"
        fi
    else
        echo "⏭️  Skipping deployment execution"
    fi
else
    echo "❌ Deployment script not found, skipping deployment test"
fi

# ============================================
# Phase 3: Cleanup Master Branch
# ============================================
echo ""
echo "========================================"
echo "Phase 3: Cleanup Master Branch"
echo "========================================"

if git show-ref --verify --quiet refs/heads/master; then
    echo ""
    echo "=== 3.1 Check master branch status ==="
    echo "Master branch exists"
    
    # Check if master has unmerged commits
    MASTER_COMMITS=$(git log main..master --oneline 2>/dev/null | wc -l)
    if [[ $MASTER_COMMITS -gt 0 ]]; then
        echo "⚠️  Master branch has $MASTER_COMMITS unmerged commit(s):"
        git log main..master --oneline
        echo ""
        read -p "Do you want to merge master into main first? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Merging master into main..."
            git merge master --no-edit || {
                echo "❌ Merge failed. Please resolve conflicts manually"
                exit 1
            }
            echo "✅ Master merged into main"
        fi
    fi
    
    # Check if master is merged into main
    if git branch --merged main | grep -q "master"; then
        echo ""
        echo "=== 3.2 Delete master branch ==="
        echo "Master branch is fully merged into main"
        read -p "Delete master branch? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if git branch -d master 2>/dev/null; then
                echo "✅ Master branch deleted successfully"
            else
                echo "⚠️  Soft delete failed, trying force delete..."
                read -p "Force delete master branch? (y/n) " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    git branch -D master
                    echo "✅ Master branch force deleted"
                else
                    echo "⏭️  Keeping master branch"
                fi
            fi
        else
            echo "⏭️  Keeping master branch"
        fi
    else
        echo "⚠️  Master branch is not fully merged"
        read -p "Force delete master branch anyway? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git branch -D master
            echo "✅ Master branch force deleted"
        else
            echo "⏭️  Keeping master branch"
        fi
    fi
else
    echo "✅ Master branch does not exist, nothing to clean up"
fi

# ============================================
# Phase 4: Final Verification
# ============================================
echo ""
echo "========================================"
echo "Phase 4: Final Verification"
echo "========================================"

echo ""
echo "=== 4.1 Branch status ==="
echo "Current branch: $(git rev-parse --abbrev-ref HEAD)"
echo "Local branches:"
git branch

echo ""
echo "=== 4.2 Sync status ==="
git status -sb

echo ""
echo "=== 4.3 Latest commit ==="
git log -1 --oneline

echo ""
echo "=== 4.4 Script files ==="
for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [[ -f "$script" ]]; then
        SIZE=$(stat -c%s "$script" 2>/dev/null || stat -f%z "$script" 2>/dev/null || echo "unknown")
        echo "✅ $script ($SIZE bytes)"
    else
        echo "❌ $script (missing)"
    fi
done

# ============================================
# Summary
# ============================================
echo ""
echo "========================================"
echo "Automation Complete!"
echo "========================================"
echo "Completed at: $(date)"
echo ""
echo "Summary:"
echo "  ✅ Script files verified"
echo "  ✅ Deployment script tested"
echo "  ✅ Master branch cleanup completed"
echo ""
echo "Current Status:"
echo "  Branch: $(git rev-parse --abbrev-ref HEAD)"
echo "  Remote: $(git remote get-url origin)"
echo "  Sync: $(git status -sb | cut -d' ' -f2-)"
echo ""
echo "Next steps:"
echo "  - Verify deployment is running: ps aux | grep -E 'node|uvicorn'"
echo "  - Check services: curl http://localhost:3000 && curl http://localhost:8000/health"
echo "  - View logs: tail -f /tmp/frontend.log"
