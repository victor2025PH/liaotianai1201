#!/bin/bash
# Verify files exist on GitHub remote repository

echo "========================================"
echo "Verify Files on GitHub"
echo "========================================"
echo ""

# Check if we're in a git repo
if [[ ! -d ".git" ]]; then
    echo "Error: Not in a Git repository"
    exit 1
fi

# Get remote URL
REMOTE_URL=$(git remote get-url origin)
echo "Remote Repository: $REMOTE_URL"
echo ""

# Fetch latest from remote
echo "Fetching from remote..."
git fetch origin main 2>&1
echo ""

# Files to check
FILES=(
    "scripts/server_git_check.sh"
    "deploy/fix_and_deploy_frontend_complete.sh"
    "scripts/test_gitignore_rules.ps1"
    "docs/服务器Git问题排查.md"
)

echo "Checking files on remote main branch:"
echo "----------------------------------------"

for file in "${FILES[@]}"; do
    echo -n "Checking: $file ... "
    
    # Check if file exists in remote
    if git ls-tree -r origin/main --name-only | grep -q "^$file$"; then
        echo "✓ EXISTS"
        
        # Show file info
        COMMIT=$(git log -1 --format="%h" origin/main -- "$file" 2>/dev/null)
        DATE=$(git log -1 --format="%ad" --date=short origin/main -- "$file" 2>/dev/null)
        echo "  Commit: $COMMIT, Date: $DATE"
    else
        echo "✗ NOT FOUND"
    fi
    echo ""
done

echo "========================================"
echo ""
echo "To fetch these files on server, run:"
echo "  git fetch origin main"
echo "  git checkout origin/main -- scripts/server_git_check.sh"
echo "  git checkout origin/main -- deploy/fix_and_deploy_frontend_complete.sh"
