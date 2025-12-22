#!/bin/bash
# ============================================================
# Agent 生产环境启动脚本 (Linux/Mac)
# 连接到生产服务器: https://api.usdt2026.cc
# ============================================================

echo "============================================================"
echo "正在启动 Agent (连接至生产环境: https://api.usdt2026.cc)"
echo "============================================================"
echo ""

# 设置配置文件路径
export AGENT_CONFIG="agent/config_prod.json"

# 检查配置文件是否存在
if [ ! -f "$AGENT_CONFIG" ]; then
    echo "❌ 错误: 配置文件不存在: $AGENT_CONFIG"
    echo "   请确保 agent/config_prod.json 文件存在"
    exit 1
fi

echo "使用配置文件: $AGENT_CONFIG"
echo ""

# 获取脚本所在目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# 启动 Agent
python3 agent/main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Agent 启动失败"
    exit 1
fi
