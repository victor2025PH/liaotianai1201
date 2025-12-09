#!/bin/bash
# 重启服务器后构建前端脚本

echo "=========================================="
echo "重启后构建前端"
echo "=========================================="
echo ""

cd /home/ubuntu/telegram-ai-system || exit 1

# 1. 检查系统状态
echo "1. 检查系统状态"
echo "----------------------------------------"
echo "系统运行时间:"
uptime
echo ""
echo "内存使用:"
free -h
echo ""

# 2. 检查 PM2 服务
echo "2. 检查 PM2 服务状态"
echo "----------------------------------------"
pm2 list 2>/dev/null || echo "PM2 未运行"
echo ""

# 3. 停止所有服务（为构建释放内存）
echo "3. 停止服务以释放内存"
echo "----------------------------------------"
pm2 stop all 2>/dev/null || true
echo "✓ 已停止所有服务"
echo ""

# 4. 清理构建文件
echo "4. 清理旧的构建文件"
echo "----------------------------------------"
cd saas-demo
rm -rf .next 2>/dev/null || true
rm -rf node_modules/.cache 2>/dev/null || true
echo "✓ 已清理"
echo ""

# 5. 检查内存（重启后应该很充足）
echo "5. 检查可用内存"
echo "----------------------------------------"
AVAIL_MEM=$(free -m | awk 'NR==2{print $7}')
echo "可用内存: ${AVAIL_MEM}MB"
echo ""

# 6. 根据可用内存设置限制
if [ "$AVAIL_MEM" -gt 1500 ]; then
    MEM_LIMIT=1536
    echo "使用 1.5GB 内存限制"
elif [ "$AVAIL_MEM" -gt 1000 ]; then
    MEM_LIMIT=1024
    echo "使用 1GB 内存限制"
else
    MEM_LIMIT=768
    echo "使用 768MB 内存限制"
fi
echo ""

# 7. 开始构建
echo "6. 开始构建前端"
echo "----------------------------------------"
echo "这可能需要 5-10 分钟，请耐心等待..."
echo ""

export NODE_OPTIONS="--max-old-space-size=${MEM_LIMIT}"
npm run build

# 8. 检查构建结果
echo ""
echo "7. 检查构建结果"
echo "----------------------------------------"
if [ -d ".next" ] && [ -d ".next/static" ]; then
    echo "✓ 构建成功"
    echo ""
    echo "构建文件大小:"
    du -sh .next 2>/dev/null || echo "无法计算大小"
else
    echo "✗ 构建失败"
    echo "请检查错误信息"
    exit 1
fi
echo ""

# 9. 重启所有服务
echo "8. 重启所有服务"
echo "----------------------------------------"
cd ..
pm2 restart all 2>/dev/null || pm2 start ecosystem.config.js
pm2 save
echo "✓ 服务已重启"
echo ""

# 10. 等待服务启动
echo "9. 等待服务启动..."
sleep 5

# 11. 验证服务状态
echo "10. 验证服务状态"
echo "----------------------------------------"
pm2 status
echo ""

# 12. 测试响应
echo "11. 测试服务响应"
echo "----------------------------------------"
BACKEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")

if [ "$BACKEND_CODE" = "200" ]; then
    echo "✓ 后端正常 (HTTP $BACKEND_CODE)"
else
    echo "✗ 后端异常 (HTTP $BACKEND_CODE)"
fi

if [ "$FRONTEND_CODE" = "200" ] || [ "$FRONTEND_CODE" = "301" ] || [ "$FRONTEND_CODE" = "302" ]; then
    echo "✓ 前端正常 (HTTP $FRONTEND_CODE)"
else
    echo "✗ 前端异常 (HTTP $FRONTEND_CODE)"
fi
echo ""

echo "=========================================="
echo "完成"
echo "=========================================="
echo ""
echo "如果前端仍然有问题，请："
echo "1. 检查 PM2 日志: pm2 logs frontend"
echo "2. 检查构建文件: ls -la saas-demo/.next/static"
echo "3. 手动重启: pm2 restart frontend"
echo ""

