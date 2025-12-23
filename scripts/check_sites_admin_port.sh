#!/bin/bash
# 检查站点管理后台端口和进程

set -e

echo "🔍 检查站点管理后台状态..."

# 1. 检查 PM2 进程
echo ""
echo "📊 PM2 进程状态:"
pm2 list | grep sites-admin-frontend || echo "⚠️  sites-admin-frontend 进程不存在"

# 2. 检查端口
echo ""
echo "🔌 检查端口 3007:"
if command -v lsof &> /dev/null; then
    if lsof -i :3007 2>/dev/null | grep -q LISTEN; then
        echo "✅ 端口 3007 正在监听"
        lsof -i :3007 | grep LISTEN
    else
        echo "❌ 端口 3007 未监听"
    fi
elif command -v netstat &> /dev/null; then
    if netstat -tlnp 2>/dev/null | grep -q ":3007 "; then
        echo "✅ 端口 3007 正在监听"
        netstat -tlnp | grep ":3007 "
    else
        echo "❌ 端口 3007 未监听"
    fi
else
    echo "⚠️  无法检查端口（需要 lsof 或 netstat）"
fi

# 3. HTTP 测试
echo ""
echo "🌐 HTTP 测试:"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://127.0.0.1:3007 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "404" ]; then
    echo "✅ HTTP 响应正常 (状态码: $HTTP_STATUS)"
elif [ "$HTTP_STATUS" = "000" ]; then
    echo "❌ 无法连接到服务 (连接超时或拒绝)"
else
    echo "⚠️  HTTP 响应异常 (状态码: $HTTP_STATUS)"
fi

# 4. 检查日志
echo ""
echo "📋 检查 PM2 日志:"
if pm2 list | grep -q sites-admin-frontend; then
    echo "最近 20 行错误日志:"
    pm2 logs sites-admin-frontend --lines 20 --nostream --err 2>/dev/null || echo "无法读取错误日志"
    echo ""
    echo "最近 20 行输出日志:"
    pm2 logs sites-admin-frontend --lines 20 --nostream --out 2>/dev/null || echo "无法读取输出日志"
else
    echo "⚠️  进程不存在，无法查看日志"
fi

# 5. 检查进程详情
echo ""
echo "📊 进程详情:"
if pm2 list | grep -q sites-admin-frontend; then
    pm2 describe sites-admin-frontend 2>/dev/null | head -30 || echo "无法获取进程详情"
fi

echo ""
echo "💡 如果服务未运行，可以尝试："
echo "   1. 重启服务: pm2 restart sites-admin-frontend"
echo "   2. 查看详细日志: pm2 logs sites-admin-frontend"
echo "   3. 重新部署: bash scripts/deploy_sites_admin.sh"

