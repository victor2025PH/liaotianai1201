#!/bin/bash
PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
# 自动检测项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

echo "正在修复 admin-frontend 端口冲突..."
# 这里写具体的修复逻辑，或者你之后再用 Cursor 编辑它
echo "修复完成！"
