#!/bin/bash
# Check if script exists on server

echo "=== Checking script location ==="
echo ""

# Check if scripts directory exists
if [ -d "scripts" ]; then
    echo "✅ scripts/ directory exists"
    ls -la scripts/ | head -20
else
    echo "❌ scripts/ directory not found"
    echo "Current directory: $(pwd)"
    echo "Files in current directory:"
    ls -la | head -20
fi

echo ""
echo "=== Checking for setup script ==="
if [ -f "scripts/setup_nginx_and_systemd.sh" ]; then
    echo "✅ scripts/setup_nginx_and_systemd.sh exists"
    ls -lh scripts/setup_nginx_and_systemd.sh
else
    echo "❌ scripts/setup_nginx_and_systemd.sh not found"
    echo ""
    echo "Searching for similar files..."
    find . -name "*nginx*" -o -name "*systemd*" 2>/dev/null | head -10
fi

echo ""
echo "=== Git status ==="
git status scripts/ 2>/dev/null || echo "Not a git repository or scripts/ not tracked"

echo ""
echo "=== Recent commits ==="
git log --oneline -5 2>/dev/null || echo "Cannot get git log"
