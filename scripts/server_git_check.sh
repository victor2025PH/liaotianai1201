#!/bin/bash
# Server Git Repository Check Script
# Check if current directory is a Git repository and provide guidance

echo "========================================"
echo "Git Repository Check"
echo "========================================"
echo ""

# Check current directory
CURRENT_DIR=$(pwd)
echo "Current Directory: $CURRENT_DIR"
echo ""

# Check if .git exists
if [[ -d ".git" ]]; then
    echo "✓ This IS a Git repository"
    echo ""
    
    # Get Git information
    echo "Git Information:"
    echo "  Remote URL: $(git remote get-url origin 2>/dev/null || echo 'Not configured')"
    echo "  Current Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'Unknown')"
    echo ""
    
    # Show status
    echo "Repository Status:"
    git status --short
    echo ""
    
    # Show last commit
    echo "Last Commit:"
    git log -1 --oneline 2>/dev/null || echo "No commits yet"
    echo ""
    
else
    echo "✗ This is NOT a Git repository"
    echo ""
    echo "Possible Solutions:"
    echo ""
    
    # Check if parent directory is Git repo
    PARENT_DIR=$(dirname "$CURRENT_DIR")
    if [[ -d "$PARENT_DIR/.git" ]]; then
        echo "1. Parent directory appears to be a Git repository:"
        echo "   cd $PARENT_DIR"
        echo ""
    fi
    
    # Common project directory
    if [[ -d "$HOME/liaotian/.git" ]]; then
        echo "2. Project repository found at:"
        echo "   cd ~/liaotian"
        echo ""
    fi
    
    echo "3. If you need to initialize a new Git repository:"
    echo "   git init"
    echo ""
    
    echo "4. If you need to clone the repository:"
    echo "   git clone <repository-url>"
    echo ""
fi

echo "========================================"
