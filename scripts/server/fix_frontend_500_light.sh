#!/bin/bash
# 轻量级前端修复脚本（避免内存问题）

echo "=========================================="
echo "轻量级前端修复"
echo "=========================================="
echo ""

cd /home/ubuntu/telegram-ai-system || exit 1

# 1. 简单检查服务状态
echo "1. 检查服务状态"
pm2 list 2>/dev/null | head -n 5 || echo "PM2 未运行"
echo ""

# 2. 停止前端（如果运行）
echo "2. 停止前端服务"
pm2 stop frontend 2>/dev/null || true
echo "✓ 已停止"
echo ""

# 3. 清理构建文件
echo "3. 清理构建文件"
cd saas-demo
rm -rf .next 2>/dev/null || true
echo "✓ 已清理"
echo ""

# 4. 检查内存
echo "4. 检查内存"
free -h | head -n 2
echo ""

# 5. 使用内存限制构建
echo "5. 开始构建（使用内存限制）"
echo "   这可能需要几分钟，请耐心等待..."
echo ""

# 设置 Node.js 内存限制为 1.5GB，避免 OOM
export NODE_OPTIONS="--max-old-space-size=1536"

# 执行构建
npm run build

# 检查构建结果
if [ -d ".next" ] && [ -d ".next/static" ]; then
    echo ""
    echo "✓ 构建成功"
else
    echo ""
    echo "✗ 构建失败"
    echo "请手动检查: cd saas-demo && npm run build"
    exit 1
fi

# 6. 重启服务
echo ""
echo "6. 重启服务"
cd ..
pm2 restart frontend 2>/dev/null || pm2 start ecosystem.config.js --only frontend
pm2 save

# 7. 等待并检查
sleep 5
echo ""
echo "7. 检查服务状态"
pm2 status frontend | head -n 3

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="
echo ""
echo "如果构建仍然失败，请："
echo "1. 增加 Swap: sudo swapon --show"
echo "2. 手动构建: cd saas-demo && NODE_OPTIONS='--max-old-space-size=1536' npm run build"
echo "3. 查看错误: cd saas-demo && npm run build 2>&1 | tail -n 50"
echo ""

