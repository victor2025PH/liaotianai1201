#!/bin/bash
# ============================================================
# 安装 AI Provider 所需的依赖包
# ============================================================

echo "=========================================="
echo "安装 AI Provider 依赖包"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"

# 检查后端目录
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ 后端目录不存在: $BACKEND_DIR"
    exit 1
fi

cd "$BACKEND_DIR" || exit 1

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

echo "[1/3] 检查当前依赖..."
pip list | grep -E "google-generativeai|openai|requests" || echo "  未找到相关依赖"

echo ""
echo "[2/3] 安装 AI Provider 依赖包..."
echo "  安装 google-generativeai (Gemini)..."
pip install --quiet google-generativeai>=0.3.0 || {
    echo "  ❌ google-generativeai 安装失败"
    exit 1
}

echo "  安装 openai (OpenAI)..."
pip install --quiet openai>=1.3.7 || {
    echo "  ⚠️  openai 安装失败（可能已安装）"
}

echo "  安装 requests (Grok)..."
pip install --quiet requests || {
    echo "  ⚠️  requests 安装失败（可能已安装）"
}

echo ""
echo "[3/3] 验证安装..."
echo "  检查 google-generativeai..."
python3 -c "import google.generativeai as genai; print('  ✅ google-generativeai 已安装')" 2>/dev/null || {
    echo "  ❌ google-generativeai 导入失败"
    exit 1
}

echo "  检查 openai..."
python3 -c "import openai; print('  ✅ openai 已安装')" 2>/dev/null || {
    echo "  ⚠️  openai 导入失败"
}

echo "  检查 requests..."
python3 -c "import requests; print('  ✅ requests 已安装')" 2>/dev/null || {
    echo "  ⚠️  requests 导入失败"
}

echo ""
echo "=========================================="
echo "✅ 依赖包安装完成"
echo "=========================================="
echo ""
echo "建议操作："
echo "  1. 重启后端服务: sudo systemctl restart luckyred-api"
echo "  2. 等待10秒后测试 API Key"
echo ""

