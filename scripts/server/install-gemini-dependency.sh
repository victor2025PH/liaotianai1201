#!/bin/bash
# ============================================================
# 安装 Gemini API 依赖包
# ============================================================

set -e

echo "=========================================="
echo "🔧 安装 Gemini API 依赖包"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
VENV_DIR="$PROJECT_DIR/admin-backend/.venv"
BACKEND_SERVICE="luckyred-api"

# 1. 检查虚拟环境
echo "[1/4] 检查虚拟环境..."
echo "----------------------------------------"
if [ -d "$VENV_DIR" ]; then
    echo "✅ 虚拟环境存在: $VENV_DIR"
    PYTHON="$VENV_DIR/bin/python"
    PIP="$VENV_DIR/bin/pip"
else
    echo "⚠️  虚拟环境不存在，使用系统 Python"
    PYTHON="python3"
    PIP="pip3"
fi
echo ""

# 2. 安装依赖包
echo "[2/4] 安装 google-generativeai..."
echo "----------------------------------------"
$PIP install google-generativeai>=0.3.0
if [ $? -eq 0 ]; then
    echo "✅ google-generativeai 安装成功"
else
    echo "❌ google-generativeai 安装失败"
    exit 1
fi
echo ""

# 3. 验证安装
echo "[3/4] 验证安装..."
echo "----------------------------------------"
$PYTHON -c "import google.generativeai as genai; print('✅ google.generativeai 导入成功')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 依赖包验证成功"
else
    echo "❌ 依赖包验证失败"
    exit 1
fi
echo ""

# 4. 重启后端服务
echo "[4/4] 重启后端服务..."
echo "----------------------------------------"
systemctl restart "$BACKEND_SERVICE"
sleep 3

if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    echo "✅ 后端服务已重启"
else
    echo "❌ 后端服务重启失败"
    systemctl status "$BACKEND_SERVICE" --no-pager -l | head -20
    exit 1
fi
echo ""

echo "=========================================="
echo "✅ 安装完成"
echo "=========================================="
echo ""
echo "现在可以测试 Gemini API Key 了。"
echo ""

