#!/bin/bash
# 修复 admin-frontend 端口冲突问题
# 将 admin-frontend 从 3006 改为 3008，避免与 ai-monitor-frontend 冲突

set -e

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || exit 1

echo "🔧 修复 admin-frontend 端口冲突..."
echo "   将端口从 3006 改为 3008"
echo ""

# 1. 备份文件
echo "📦 备份文件..."
BACKUP_DIR="$PROJECT_ROOT/backup/port_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp scripts/deploy_admin_frontend.sh "$BACKUP_DIR/" 2>/dev/null || true
cp scripts/check_admin_frontend.sh "$BACKUP_DIR/" 2>/dev/null || true
cp scripts/verify_admin_frontend.sh "$BACKUP_DIR/" 2>/dev/null || true
cp docs/ADMIN_FRONTEND_DEPLOYMENT.md "$BACKUP_DIR/" 2>/dev/null || true

echo "✅ 备份完成: $BACKUP_DIR"
echo ""

# 2. 修改部署脚本
echo "📝 修改部署脚本..."

# deploy_admin_frontend.sh
if [ -f "scripts/deploy_admin_frontend.sh" ]; then
    sed -i.bak 's/PORT=3006/PORT=3008/g' scripts/deploy_admin_frontend.sh
    sed -i.bak 's/:3006/:3008/g' scripts/deploy_admin_frontend.sh
    sed -i.bak 's/3006/3008/g' scripts/deploy_admin_frontend.sh
    # 恢复 ai-monitor-frontend 的引用（如果有）
    sed -i.bak 's/ai-monitor-frontend.*3008/ai-monitor-frontend.*3006/g' scripts/deploy_admin_frontend.sh || true
    rm -f scripts/deploy_admin_frontend.sh.bak
    echo "✅ 已更新: scripts/deploy_admin_frontend.sh"
fi

# check_admin_frontend.sh
if [ -f "scripts/check_admin_frontend.sh" ]; then
    sed -i.bak 's/:3006/:3008/g' scripts/check_admin_frontend.sh
    sed -i.bak 's/3006/3008/g' scripts/check_admin_frontend.sh
    rm -f scripts/check_admin_frontend.sh.bak
    echo "✅ 已更新: scripts/check_admin_frontend.sh"
fi

# verify_admin_frontend.sh
if [ -f "scripts/verify_admin_frontend.sh" ]; then
    sed -i.bak 's/:3006/:3008/g' scripts/verify_admin_frontend.sh
    sed -i.bak 's/3006/3008/g' scripts/verify_admin_frontend.sh
    rm -f scripts/verify_admin_frontend.sh.bak
    echo "✅ 已更新: scripts/verify_admin_frontend.sh"
fi

echo ""

# 3. 更新文档
echo "📚 更新文档..."

if [ -f "docs/ADMIN_FRONTEND_DEPLOYMENT.md" ]; then
    sed -i.bak 's/127\.0\.0\.1:3006/127.0.0.1:3008/g' docs/ADMIN_FRONTEND_DEPLOYMENT.md
    sed -i.bak 's/端口 3006/端口 3008/g' docs/ADMIN_FRONTEND_DEPLOYMENT.md
    sed -i.bak 's/PORT=3006/PORT=3008/g' docs/ADMIN_FRONTEND_DEPLOYMENT.md
    sed -i.bak 's/:3006/:3008/g' docs/ADMIN_FRONTEND_DEPLOYMENT.md
    # 保留 ai-monitor 的 3006 引用
    sed -i.bak 's/ai-monitor.*3008/ai-monitor.*3006/g' docs/ADMIN_FRONTEND_DEPLOYMENT.md || true
    rm -f docs/ADMIN_FRONTEND_DEPLOYMENT.md.bak
    echo "✅ 已更新: docs/ADMIN_FRONTEND_DEPLOYMENT.md"
fi

echo ""

# 4. 检查修改结果
echo "🔍 检查修改结果..."
echo ""

echo "检查是否还有 admin-frontend 使用 3006 的引用:"
REMAINING=$(grep -r "admin-frontend.*3006\|3006.*admin-frontend" scripts/ docs/ 2>/dev/null | grep -v ".backup\|backup/" | grep -v "fix_admin_frontend_port.sh\|ADMIN_SYSTEM" | wc -l)
if [ "$REMAINING" -eq 0 ]; then
    echo "✅ 未发现剩余引用"
else
    echo "⚠️  发现 $REMAINING 个剩余引用:"
    grep -r "admin-frontend.*3006\|3006.*admin-frontend" scripts/ docs/ 2>/dev/null | grep -v ".backup\|backup/" | grep -v "fix_admin_frontend_port.sh\|ADMIN_SYSTEM"
fi

echo ""
echo "检查新端口 3008 的引用:"
NEW_REFS=$(grep -r "admin-frontend.*3008\|3008.*admin-frontend" scripts/ docs/ 2>/dev/null | grep -v ".backup\|backup/" | wc -l)
if [ "$NEW_REFS" -gt 0 ]; then
    echo "✅ 发现 $NEW_REFS 个新端口引用（预期）"
else
    echo "⚠️  未发现新端口引用，可能需要手动检查"
fi

echo ""
echo "=========================================="
echo "✅ 端口修复完成！"
echo "=========================================="
echo ""
echo "📋 修改摘要:"
echo "   - admin-frontend 端口: 3006 → 3008"
echo "   - ai-monitor-frontend 端口: 3006 (保持不变)"
echo "   - sites-admin-frontend 端口: 3007 (保持不变)"
echo ""
echo "💡 下一步:"
echo "   1. 如果服务正在运行，需要重新部署:"
echo "      bash scripts/deploy_admin_frontend.sh"
echo ""
echo "   2. 验证端口占用:"
echo "      sudo lsof -i :3008"
echo ""
echo "   3. 测试服务:"
echo "      curl http://127.0.0.1:3008"
echo ""
echo "   4. 备份位置: $BACKUP_DIR"
echo ""

