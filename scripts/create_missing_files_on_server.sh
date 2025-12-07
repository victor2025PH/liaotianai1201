#!/bin/bash
# Create missing files directly on server
# This script creates the files that should exist but are missing

set -e

echo "========================================"
echo "Create Missing Files on Server"
echo "========================================"
echo ""

PROJECT_DIR="$HOME/liaotian"
cd "$PROJECT_DIR" || exit 1

echo "Creating missing scripts..."
echo ""

# 1. Create scripts directory if not exists
mkdir -p scripts
mkdir -p deploy

# 2. Create server_git_check.sh
cat > scripts/server_git_check.sh << 'EOF'
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
EOF
chmod +x scripts/server_git_check.sh
echo "✓ Created scripts/server_git_check.sh"

# 3. Create fix_and_deploy_frontend_complete.sh (first 100 lines)
cat > deploy/fix_and_deploy_frontend_complete.sh << 'DEPLOYEOF'
#!/bin/bash
# Fix and deploy frontend completely

set -e

echo "=========================================="
echo "Fix and Deploy Frontend"
echo "=========================================="

cd ~/liaotian || {
    echo "❌ Cannot enter project directory"
    exit 1
}

# 1. Pull latest code
echo ""
echo "=== 1. Pull Latest Code ==="
git pull origin main || git pull origin master
echo "✅ Code updated"

# 2. Enter frontend directory
echo ""
echo "=== 2. Enter Frontend Directory ==="
cd ~/liaotian/saas-demo || {
    echo "❌ Cannot enter frontend directory"
    exit 1
}

# 3. Install dependencies
echo ""
echo "=== 3. Install Dependencies ==="
npm install
echo "✅ Dependencies installed"

# 4. Clean cache
echo ""
echo "=== 4. Clean Build Cache ==="
rm -rf .next
rm -rf node_modules/.cache
echo "✅ Cache cleaned"

# 5. Build frontend
echo ""
echo "=== 5. Build Frontend ==="
if npm run build; then
    echo "✅ Frontend build successful"
else
    echo "❌ Frontend build failed"
    echo "Check error messages above..."
    exit 1
fi

# 6. Clean old processes
echo ""
echo "=== 6. Clean Old Processes ==="
pkill -f "next-server" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true
pkill -f "npm.*start" 2>/dev/null || true
sleep 3

# Check and clean port 3000
if command -v ss > /dev/null; then
    PID=$(ss -tlnp | grep :3000 | grep -oP 'pid=\K[0-9]+' | head -1 || true)
    if [ -n "$PID" ]; then
        echo "Terminating process on port 3000: $PID"
        kill $PID 2>/dev/null || true
        sleep 2
    fi
fi

# 7. Start frontend service
echo ""
echo "=== 7. Start Frontend Service ==="
nohup npm start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend service started, PID: $FRONTEND_PID"

# 8. Wait and verify
echo ""
echo "=== 8. Verify Service ==="
sleep 10

if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "✅ Frontend process is running (PID: $FRONTEND_PID)"
else
    echo "❌ Frontend process exited"
    echo "Check logs:"
    tail -50 /tmp/frontend.log
    exit 1
fi

# Check port
if command -v ss > /dev/null; then
    if ss -tlnp | grep :3000 > /dev/null; then
        echo "✅ Port 3000 is listening"
        ss -tlnp | grep :3000
    else
        echo "⚠️  Port 3000 is not listening"
        echo "Check logs:"
        tail -30 /tmp/frontend.log
    fi
fi

# Check HTTP response
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "✅ Frontend service responding (HTTP $HTTP_CODE)"
else
    echo "⚠️  Frontend service not responding (HTTP $HTTP_CODE)"
    echo "Check logs: tail -f /tmp/frontend.log"
fi

# 9. Check backend service
echo ""
echo "=== 9. Check Backend Service ==="
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend service is running"
    curl -s http://localhost:8000/health
else
    echo "⚠️  Backend service not responding"
fi

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Service Status:"
echo "  Backend: http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo ""
echo "View Logs:"
echo "  Frontend: tail -f /tmp/frontend.log"
echo "  Backend: tail -f /tmp/backend.log"
echo ""
echo "Check Service Status:"
echo "  ps aux | grep -E 'node|uvicorn' | grep -v grep"
echo "  ss -tlnp | grep -E ':3000|:8000'"
DEPLOYEOF
chmod +x deploy/fix_and_deploy_frontend_complete.sh
echo "✓ Created deploy/fix_and_deploy_frontend_complete.sh"

echo ""
echo "========================================"
echo "✅ Files created successfully!"
echo "========================================"
echo ""
echo "Created files:"
echo "  - scripts/server_git_check.sh"
echo "  - deploy/fix_and_deploy_frontend_complete.sh"
echo ""
echo "Next steps:"
echo "  1. Test the scripts:"
echo "     bash scripts/server_git_check.sh"
echo ""
echo "  2. If you want to add these to Git:"
echo "     git add scripts/ deploy/"
echo "     git commit -m 'Add missing scripts'"
echo "     git push origin main"
