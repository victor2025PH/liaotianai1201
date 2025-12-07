#!/bin/bash
# Verify Nginx and Systemd deployment status
# 验证 Nginx 和 Systemd 部署状态

echo "========================================="
echo "部署状态验证"
echo "========================================="
echo ""

# 检查 Nginx
echo "=== 1. Nginx 状态 ==="
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 服务运行中"
else
    echo "❌ Nginx 服务未运行"
fi

if systemctl is-enabled --quiet nginx; then
    echo "✅ Nginx 开机自启动已启用"
else
    echo "⚠️  Nginx 开机自启动未启用"
fi

# 检查 Nginx 配置
echo ""
echo "=== 2. Nginx 配置 ==="
if [ -f "/etc/nginx/sites-available/liaotian" ]; then
    echo "✅ Nginx 配置文件存在"
    if [ -L "/etc/nginx/sites-enabled/liaotian" ]; then
        echo "✅ Nginx 配置已启用"
    else
        echo "⚠️  Nginx 配置未启用"
    fi
else
    echo "❌ Nginx 配置文件不存在"
fi

# 检查端口
echo ""
echo "=== 3. 端口状态 ==="
if ss -tlnp | grep :80 > /dev/null 2>&1; then
    echo "✅ 端口 80 监听中"
    ss -tlnp | grep :80
else
    echo "❌ 端口 80 未监听"
fi

if ss -tlnp | grep :3000 > /dev/null 2>&1; then
    echo "✅ 端口 3000 监听中"
else
    echo "❌ 端口 3000 未监听"
fi

if ss -tlnp | grep :8000 > /dev/null 2>&1; then
    echo "✅ 端口 8000 监听中"
else
    echo "❌ 端口 8000 未监听"
fi

# 检查 Systemd 服务
echo ""
echo "=== 4. Systemd 服务状态 ==="

# 后端服务
if systemctl is-active --quiet liaotian-backend; then
    echo "✅ 后端服务运行中"
else
    echo "❌ 后端服务未运行"
    echo "   查看日志: sudo journalctl -u liaotian-backend -n 20"
fi

if systemctl is-enabled --quiet liaotian-backend; then
    echo "✅ 后端服务开机自启动已启用"
else
    echo "⚠️  后端服务开机自启动未启用"
fi

# 前端服务
if systemctl is-active --quiet liaotian-frontend; then
    echo "✅ 前端服务运行中"
else
    echo "❌ 前端服务未运行"
    echo "   查看日志: sudo journalctl -u liaotian-frontend -n 20"
fi

if systemctl is-enabled --quiet liaotian-frontend; then
    echo "✅ 前端服务开机自启动已启用"
else
    echo "⚠️  前端服务开机自启动未启用"
fi

# HTTP 测试
echo ""
echo "=== 5. HTTP 响应测试 ==="

# 测试后端健康检查
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    echo "✅ 后端健康检查正常 (HTTP $BACKEND_HEALTH)"
    curl -s http://localhost:8000/health | head -1
else
    echo "❌ 后端健康检查失败 (HTTP $BACKEND_HEALTH)"
fi

# 测试前端
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_RESPONSE" = "200" ] || [ "$FRONTEND_RESPONSE" = "301" ] || [ "$FRONTEND_RESPONSE" = "302" ]; then
    echo "✅ 前端响应正常 (HTTP $FRONTEND_RESPONSE)"
else
    echo "❌ 前端响应异常 (HTTP $FRONTEND_RESPONSE)"
fi

# 测试 Nginx 代理
NGINX_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health 2>/dev/null || echo "000")
if [ "$NGINX_RESPONSE" = "200" ]; then
    echo "✅ Nginx 代理正常 (HTTP $NGINX_RESPONSE)"
    curl -s http://localhost/health | head -1
else
    echo "⚠️  Nginx 代理异常 (HTTP $NGINX_RESPONSE)"
fi

# 总结
echo ""
echo "========================================="
echo "验证完成"
echo "========================================="
echo ""
echo "访问地址："
echo "  本地: http://localhost/"
echo "  外部: http://165.154.233.55/"
echo ""
echo "如果服务未运行，查看日志："
echo "  sudo journalctl -u liaotian-backend -f"
echo "  sudo journalctl -u liaotian-frontend -f"
echo "  sudo tail -f /var/log/nginx/liaotian-error.log"
