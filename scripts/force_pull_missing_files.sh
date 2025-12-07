#!/bin/bash
# Force pull missing files from GitHub

set -e

echo "========================================"
echo "Force Pull Missing Files from GitHub"
echo "========================================"
echo ""

# Check if we're in a git repo
if [[ ! -d ".git" ]]; then
    echo "Error: Not in a Git repository"
    echo "Please run: cd ~/liaotian"
    exit 1
fi

# Get current directory
CURRENT_DIR=$(pwd)
echo "Current Directory: $CURRENT_DIR"
echo ""

# Get remote info
REMOTE_URL=$(git remote get-url origin)
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Remote: $REMOTE_URL"
echo "Current Branch: $CURRENT_BRANCH"
echo ""

# Fetch latest from remote
echo "Step 1: Fetching latest from remote..."
git fetch origin main
echo "✓ Fetch completed"
echo ""

# Files to pull
FILES=(
    "scripts/server_git_check.sh"
    "deploy/fix_and_deploy_frontend_complete.sh"
    "scripts/test_gitignore_rules.ps1"
    "scripts/verify_git_push.ps1"
    "scripts/complete_push_workflow.ps1"
    "scripts/diagnose_git_issue.ps1"
    "docs/服务器Git问题排查.md"
    "docs/部署流程-完整指南.md"
    "docs/GITIGNORE规则说明.md"
)

echo "Step 2: Checking and pulling files..."
echo "----------------------------------------"

PULLED=0
NOT_FOUND=0

for file in "${FILES[@]}"; do
    # Check if file exists in remote
    if git ls-tree -r origin/main --name-only | grep -q "^$file$"; then
        echo -n "Pulling: $file ... "
        
        # Checkout file from remote
        if git checkout origin/main -- "$file" 2>/dev/null; then
            echo "✓ SUCCESS"
            PULLED=$((PULLED + 1))
        else
            echo "✗ FAILED"
            NOT_FOUND=$((NOT_FOUND + 1))
        fi
    else
        echo "✗ NOT FOUND in remote: $file"
        NOT_FOUND=$((NOT_FOUND + 1))
    fi
done

echo ""
echo "========================================"
echo "Summary:"
echo "  Files pulled: $PULLED"
echo "  Files not found: $NOT_FOUND"
echo "========================================"
echo ""

# Verify pulled files
echo "Step 3: Verifying pulled files..."
echo "----------------------------------------"

for file in "${FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✓ $file"
        
        # Add execute permission for .sh files
        if [[ "$file" == *.sh ]]; then
            chmod +x "$file"
            echo "  → Added execute permission"
        fi
    else
        echo "✗ $file (still missing)"
    fi
done

echo ""
echo "Done!"
echo ""
echo "Next steps:"
echo "  1. Review the files: ls -la scripts/ deploy/"
echo "  2. Test the scripts: bash scripts/server_git_check.sh"
echo "  3. Commit if needed: git add . && git commit -m 'Add missing files'"
