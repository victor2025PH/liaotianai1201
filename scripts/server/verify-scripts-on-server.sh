#!/bin/bash
# ============================================================
# Verify Scripts on Server (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Verify that all server scripts exist and are executable
# 
# One-click execution: bash scripts/server/verify-scripts-on-server.sh
# ============================================================

# Don't exit on error, we want to check all scripts

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "🔍 Verify Server Scripts"
echo "============================================================"
echo ""

cd "$PROJECT_ROOT"

# Check if scripts/server directory exists
if [ ! -d "scripts/server" ]; then
    echo "❌ Error: scripts/server directory not found"
    echo ""
    echo "Please run:"
    echo "  cd ~/telegram-ai-system"
    echo "  git pull origin main"
    exit 1
fi

echo "[1/3] Checking script files..."
echo ""

# List of required scripts
REQUIRED_SCRIPTS=(
    "install-dependencies.sh"
    "setup-server.sh"
    "quick-start.sh"
    "start-all-services.sh"
    "verify-services.sh"
    "auto-test-and-fix.sh"
)

MISSING_SCRIPTS=()
EXISTS_BUT_NOT_EXECUTABLE=()

for script in "${REQUIRED_SCRIPTS[@]}"; do
    script_path="scripts/server/$script"
    if [ ! -f "$script_path" ]; then
        MISSING_SCRIPTS+=("$script")
        echo "  ❌ $script - NOT FOUND"
    elif [ ! -x "$script_path" ]; then
        EXISTS_BUT_NOT_EXECUTABLE+=("$script")
        echo "  ⚠️  $script - EXISTS but not executable"
    else
        echo "  ✅ $script - OK"
    fi
done

echo ""
echo "[2/3] Fixing permissions..."
for script in "${REQUIRED_SCRIPTS[@]}"; do
    script_path="scripts/server/$script"
    if [ -f "$script_path" ]; then
        chmod +x "$script_path"
        echo "  ✓ Set executable: $script"
    fi
done

echo ""
echo "[3/3] Summary..."
echo ""

if [ ${#MISSING_SCRIPTS[@]} -eq 0 ] && [ ${#EXISTS_BUT_NOT_EXECUTABLE[@]} -eq 0 ]; then
    echo "✅ All scripts are present and executable"
    echo ""
    echo "You can now run:"
    echo "  bash scripts/server/quick-start.sh"
    exit 0
else
    if [ ${#MISSING_SCRIPTS[@]} -gt 0 ]; then
        echo "❌ Missing scripts:"
        for script in "${MISSING_SCRIPTS[@]}"; do
            echo "   - $script"
        done
        echo ""
        echo "Please run:"
        echo "  cd ~/telegram-ai-system"
        echo "  git pull origin main"
    fi
    
    if [ ${#EXISTS_BUT_NOT_EXECUTABLE[@]} -gt 0 ]; then
        echo "⚠️  Fixed permissions for:"
        for script in "${EXISTS_BUT_NOT_EXECUTABLE[@]}"; do
            echo "   - $script"
        done
    fi
    
    exit 1
fi

