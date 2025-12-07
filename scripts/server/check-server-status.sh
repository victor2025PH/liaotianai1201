#!/bin/bash
# ============================================================
# Check Server Status (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Comprehensive server status check
# 
# One-click execution: bash scripts/server/check-server-status.sh
# ============================================================

set -e

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
SERVICE_NAME="telegram-backend"

echo "============================================================"
echo "🔍 Server Status Check"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================
# 1. Service Status
# ============================================================
echo "[1/7] Service Status..."
echo "----------------------------------------"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✅ Service is RUNNING${NC}"
    systemctl status "$SERVICE_NAME" --no-pager -l | head -n 8
else
    echo -e "${RED}❌ Service is NOT RUNNING${NC}"
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        echo -e "${YELLOW}⚠️  Service is enabled but not running${NC}"
    else
        echo -e "${YELLOW}⚠️  Service is not enabled${NC}"
    fi
    systemctl status "$SERVICE_NAME" --no-pager -l | head -n 8 || true
fi
echo ""

# ============================================================
# 2. Port Status
# ============================================================
echo "[2/7] Port Status..."
echo "----------------------------------------"
if ss -tlnp 2>/dev/null | grep -q ":8000"; then
    echo -e "${GREEN}✅ Port 8000 is LISTENING${NC}"
    ss -tlnp 2>/dev/null | grep ":8000"
else
    echo -e "${RED}❌ Port 8000 is NOT LISTENING${NC}"
fi
echo ""

# ============================================================
# 3. Health Check
# ============================================================
echo "[3/7] Health Check..."
echo "----------------------------------------"
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check PASSED${NC}"
    curl -s http://localhost:8000/health | head -n 5
else
    echo -e "${RED}❌ Health check FAILED${NC}"
    echo "Service may not be running or not responding"
fi
echo ""

# ============================================================
# 4. Git Repository Status
# ============================================================
echo "[4/7] Git Repository Status..."
echo "----------------------------------------"
if [ -d "$PROJECT_DIR/.git" ]; then
    cd "$PROJECT_DIR"
    echo "Current branch: $(git branch --show-current)"
    echo "Last commit: $(git log -1 --oneline --no-decorate 2>/dev/null || echo 'No commits')"
    
    # Check if behind remote
    git fetch origin main > /dev/null 2>&1 || true
    LOCAL=$(git rev-parse HEAD 2>/dev/null || echo "")
    REMOTE=$(git rev-parse origin/main 2>/dev/null || echo "")
    
    if [ -z "$LOCAL" ] || [ -z "$REMOTE" ]; then
        echo -e "${YELLOW}⚠️  Cannot determine sync status${NC}"
    elif [ "$LOCAL" = "$REMOTE" ]; then
        echo -e "${GREEN}✅ Code is UP TO DATE with origin/main${NC}"
    else
        echo -e "${YELLOW}⚠️  Code is BEHIND origin/main${NC}"
        echo "  Local:  $LOCAL"
        echo "  Remote: $REMOTE"
    fi
    
    # Check for uncommitted changes
    if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
        echo -e "${YELLOW}⚠️  Has uncommitted changes${NC}"
    else
        echo -e "${GREEN}✅ No uncommitted changes${NC}"
    fi
else
    echo -e "${RED}❌ Not a Git repository${NC}"
fi
echo ""

# ============================================================
# 5. Workflow File Status
# ============================================================
echo "[5/7] GitHub Workflow File Status..."
echo "----------------------------------------"
if [ -f "$PROJECT_DIR/.github/workflows/deploy.yml" ]; then
    echo -e "${GREEN}✅ deploy.yml exists${NC}"
    
    # Check if it uses correct secrets
    if grep -q "secrets.SERVER_HOST" "$PROJECT_DIR/.github/workflows/deploy.yml" && \
       grep -q "secrets.SERVER_USER" "$PROJECT_DIR/.github/workflows/deploy.yml" && \
       grep -q "secrets.SERVER_SSH_KEY" "$PROJECT_DIR/.github/workflows/deploy.yml"; then
        echo -e "${GREEN}✅ Using correct secrets variables${NC}"
    else
        echo -e "${YELLOW}⚠️  May not be using correct secrets variables${NC}"
    fi
else
    echo -e "${RED}❌ deploy.yml not found${NC}"
fi
echo ""

# ============================================================
# 6. Virtual Environment Status
# ============================================================
echo "[6/7] Virtual Environment Status..."
echo "----------------------------------------"
if [ -d "$PROJECT_DIR/admin-backend/venv" ]; then
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
    
    # Check if uvicorn is installed
    if [ -f "$PROJECT_DIR/admin-backend/venv/bin/uvicorn" ]; then
        echo -e "${GREEN}✅ uvicorn is installed${NC}"
    else
        echo -e "${RED}❌ uvicorn is NOT installed${NC}"
    fi
    
    # Check Python version
    PYTHON_VERSION=$("$PROJECT_DIR/admin-backend/venv/bin/python" --version 2>/dev/null || echo "Unknown")
    echo "Python version: $PYTHON_VERSION"
else
    echo -e "${RED}❌ Virtual environment NOT found${NC}"
    echo "  Expected: $PROJECT_DIR/admin-backend/venv"
fi
echo ""

# ============================================================
# 7. Recent Service Logs
# ============================================================
echo "[7/7] Recent Service Logs (last 10 lines)..."
echo "----------------------------------------"
if systemctl list-units --type=service | grep -q "$SERVICE_NAME"; then
    sudo journalctl -u "$SERVICE_NAME" -n 10 --no-pager || true
else
    echo -e "${YELLOW}⚠️  Service unit not found${NC}"
fi
echo ""

# ============================================================
# Summary
# ============================================================
echo "============================================================"
echo "📊 Summary"
echo "============================================================"
echo ""

# Count issues
ISSUES=0

if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${RED}❌ Service is not running${NC}"
    ISSUES=$((ISSUES + 1))
fi

if ! ss -tlnp 2>/dev/null | grep -q ":8000"; then
    echo -e "${RED}❌ Port 8000 is not listening${NC}"
    ISSUES=$((ISSUES + 1))
fi

if ! curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}❌ Health check failed${NC}"
    ISSUES=$((ISSUES + 1))
fi

if [ ! -d "$PROJECT_DIR/admin-backend/venv" ]; then
    echo -e "${RED}❌ Virtual environment missing${NC}"
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Server is healthy.${NC}"
else
    echo -e "${YELLOW}⚠️  Found $ISSUES issue(s)${NC}"
    echo ""
    echo "Recommended actions:"
    echo "  1. Check service logs: sudo journalctl -u $SERVICE_NAME -n 50"
    echo "  2. Restart service: sudo systemctl restart $SERVICE_NAME"
    echo "  3. Check service file: cat /etc/systemd/system/$SERVICE_NAME.service"
    echo "  4. Run diagnosis: bash scripts/server/diagnose-service.sh"
fi

echo ""
echo "============================================================"

