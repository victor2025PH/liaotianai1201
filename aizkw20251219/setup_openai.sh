#!/bin/bash
# OpenAI API Key 快速配置脚本

# 请在此处设置您的 OpenAI API Key
OPENAI_API_KEY="sk-proj-your-openai-api-key-here"

echo "===== OpenAI API Key 配置脚本 ====="
echo ""

# 检查项目目录
PROJECT_DIR="/home/ubuntu/aizkw20251219"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 项目目录不存在: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR" || exit 1

# 创建 .env.local 文件
echo "正在创建 .env.local 文件..."
cat > .env.local << EOF
# OpenAI API Key
OPENAI_API_KEY=$OPENAI_API_KEY

# Gemini API Key (可选，作为备用)
# GEMINI_API_KEY=your-gemini-api-key-here
EOF

echo "✓ .env.local 文件已创建"

# 检查是否已安装依赖
if [ ! -d "node_modules" ]; then
    echo ""
    echo "正在安装依赖..."
    npm install
else
    echo "✓ 依赖已安装"
fi

# 检查是否有 openai 包
if ! npm list openai > /dev/null 2>&1; then
    echo ""
    echo "正在安装 OpenAI SDK..."
    npm install openai@^4.28.0
    echo "✓ OpenAI SDK 已安装"
else
    echo "✓ OpenAI SDK 已存在"
fi

echo ""
echo "===== 配置完成 ====="
echo ""
echo "下一步操作:"
echo "1. 开发环境: npm run dev"
echo "2. 生产环境: npm run build && sudo systemctl reload nginx"
echo ""
echo "验证配置:"
echo "  - 检查 .env.local 文件: cat .env.local"
echo "  - 测试 AI 对话功能"

