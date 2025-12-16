#!/bin/bash
# ============================================================
# 连接超时诊断和修复脚本
# ============================================================
# 
# 功能：
# 1. 检查服务状态（Nginx, 前端, 后端）
# 2. 检查端口监听
# 3. 检查防火墙
# 4. 检查 Nginx 配置
# 5. 尝试修复常见问题
#
# 使用方法：sudo bash scripts/server/diagnose_connection_timeout.sh
# ============================================================

set -e

echo "============================================================"
echo "连接超时诊断和修复脚本"
echo "============================================================"
echo "开始时间: $(date)"
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  建议以 root 权限运行此脚本（使用 sudo）"
    echo "继续执行..."
    echo ""
fi

# ============================================================
# [1/6] 检查服务状态
# ============================================================
echo "[1/6] 检查服务状态"
echo "------------------------------------------------------------"

# 检查 Nginx
echo "□ Nginx 服务状态:"
if systemctl is-active --quiet nginx 2>/dev/null || sudo systemctl is-active --quiet nginx 2>/dev/null; then
    echo "✅ Nginx 运行中"
    systemctl status nginx --no-pager | head -5 || sudo systemctl status nginx --no-pager | head -5
else
    echo "❌ Nginx 未运行"
    systemctl status nginx --no-pager | head -10 || sudo systemctl status nginx --no-pager | head -10
fi
echo ""

# 检查前端服务
echo "□ 前端服务状态:"
if systemctl is-active --quiet liaotian-frontend 2>/dev/null || sudo systemctl is-active --quiet liaotian-frontend 2>/dev/null; then
    echo "✅ 前端服务运行中"
    systemctl status liaotian-frontend --no-pager | head -5 || sudo systemctl status liaotian-frontend --no-pager | head -5
else
    echo "❌ 前端服务未运行"
    systemctl status liaotian-frontend --no-pager | head -10 || sudo systemctl status liaotian-frontend --no-pager | head -10
fi
echo ""

# 检查后端服务
echo "□ 后端服务状态:"
if systemctl is-active --quiet luckyred-api 2>/dev/null || sudo systemctl is-active --quiet luckyred-api 2>/dev/null; then
    echo "✅ 后端服务运行中"
    systemctl status luckyred-api --no-pager | head -5 || sudo systemctl status luckyred-api --no-pager | head -5
else
    echo "❌ 后端服务未运行"
    systemctl status luckyred-api --no-pager | head -10 || sudo systemctl status luckyred-api --no-pager | head -10
fi
echo ""

# ============================================================
# [2/6] 检查端口监听
# ============================================================
echo "[2/6] 检查端口监听"
echo "------------------------------------------------------------"

# 检查端口 80 (HTTP)
echo "□ 端口 80 (HTTP):"
if ss -tlnp 2>/dev/null | grep -q ":80 " || sudo ss -tlnp 2>/dev/null | grep -q ":80 "; then
    echo "✅ 端口 80 正在监听"
    ss -tlnp 2>/dev/null | grep ":80 " || sudo ss -tlnp 2>/dev/null | grep ":80 "
else
    echo "❌ 端口 80 未监听"
fi
echo ""

# 检查端口 443 (HTTPS)
echo "□ 端口 443 (HTTPS):"
if ss -tlnp 2>/dev/null | grep -q ":443 " || sudo ss -tlnp 2>/dev/null | grep -q ":443 "; then
    echo "✅ 端口 443 正在监听"
    ss -tlnp 2>/dev/null | grep ":443 " || sudo ss -tlnp 2>/dev/null | grep ":443 "
else
    echo "❌ 端口 443 未监听"
fi
echo ""

# 检查端口 3000 (前端)
echo "□ 端口 3000 (前端):"
if ss -tlnp 2>/dev/null | grep -q ":3000 " || sudo ss -tlnp 2>/dev/null | grep -q ":3000 "; then
    echo "✅ 端口 3000 正在监听"
    ss -tlnp 2>/dev/null | grep ":3000 " || sudo ss -tlnp 2>/dev/null | grep ":3000 "
else
    echo "❌ 端口 3000 未监听"
fi
echo ""

# 检查端口 8000 (后端)
echo "□ 端口 8000 (后端):"
if ss -tlnp 2>/dev/null | grep -q ":8000 " || sudo ss -tlnp 2>/dev/null | grep -q ":8000 "; then
    echo "✅ 端口 8000 正在监听"
    ss -tlnp 2>/dev/null | grep ":8000 " || sudo ss -tlnp 2>/dev/null | grep ":8000 "
else
    echo "❌ 端口 8000 未监听"
fi
echo ""

# ============================================================
# [3/6] 检查防火墙
# ============================================================
echo "[3/6] 检查防火墙"
echo "------------------------------------------------------------"

# 检查 UFW
if command -v ufw > /dev/null 2>&1; then
    echo "□ UFW 状态:"
    ufw status | head -10 || sudo ufw status | head -10
    echo ""
fi

# 检查 iptables
if command -v iptables > /dev/null 2>&1; then
    echo "□ iptables 规则（端口 80, 443）:"
    iptables -L -n 2>/dev/null | grep -E "80|443" || sudo iptables -L -n 2>/dev/null | grep -E "80|443" || echo "未找到相关规则"
    echo ""
fi

# ============================================================
# [4/6] 检查 Nginx 配置
# ============================================================
echo "[4/6] 检查 Nginx 配置"
echo "------------------------------------------------------------"

NGINX_CONF="/etc/nginx/sites-available/default"

if [ -f "$NGINX_CONF" ]; then
    echo "□ Nginx 配置语法检查:"
    nginx -t 2>&1 || sudo nginx -t 2>&1
    echo ""
    
    echo "□ Nginx 配置摘要:"
    echo "  - 监听端口:"
    grep -E "listen\s+[0-9]+" "$NGINX_CONF" | head -5 || echo "未找到监听配置"
    echo "  - server_name:"
    grep -E "server_name" "$NGINX_CONF" | head -3 || echo "未找到 server_name"
    echo "  - SSL 配置:"
    grep -E "ssl_certificate|ssl_certificate_key" "$NGINX_CONF" | head -2 || echo "未找到 SSL 配置"
else
    echo "⚠️  Nginx 配置文件不存在: $NGINX_CONF"
fi
echo ""

# ============================================================
# [5/6] 测试本地连接
# ============================================================
echo "[5/6] 测试本地连接"
echo "------------------------------------------------------------"

# 测试前端
echo "□ 测试前端 (http://127.0.0.1:3000):"
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:3000/ 2>/dev/null || echo "000")
if [ "$FRONTEND_CODE" = "200" ] || [ "$FRONTEND_CODE" = "302" ] || [ "$FRONTEND_CODE" = "301" ]; then
    echo "✅ 前端响应正常 (HTTP $FRONTEND_CODE)"
else
    echo "❌ 前端响应异常 (HTTP $FRONTEND_CODE)"
fi
echo ""

# 测试后端
echo "□ 测试后端 (http://127.0.0.1:8000):"
BACKEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:8000/api/v1/health 2>/dev/null || echo "000")
if [ "$BACKEND_CODE" = "200" ]; then
    echo "✅ 后端响应正常 (HTTP $BACKEND_CODE)"
else
    echo "❌ 后端响应异常 (HTTP $BACKEND_CODE)"
fi
echo ""

# 测试 Nginx (本地)
echo "□ 测试 Nginx (http://127.0.0.1):"
NGINX_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1/ 2>/dev/null || echo "000")
if [ "$NGINX_CODE" = "200" ] || [ "$NGINX_CODE" = "302" ] || [ "$NGINX_CODE" = "301" ]; then
    echo "✅ Nginx 响应正常 (HTTP $NGINX_CODE)"
else
    echo "❌ Nginx 响应异常 (HTTP $NGINX_CODE)"
fi
echo ""

# ============================================================
# [6/6] 查看最近错误日志
# ============================================================
echo "[6/6] 查看最近错误日志"
echo "------------------------------------------------------------"

echo "□ Nginx 错误日志（最后 20 行）:"
tail -20 /var/log/nginx/error.log 2>/dev/null || sudo tail -20 /var/log/nginx/error.log 2>/dev/null || echo "无法读取 Nginx 错误日志"
echo ""

echo "□ 后端服务日志（最后 20 行，包含 error）:"
journalctl -u luckyred-api -n 50 --no-pager 2>/dev/null | grep -i "error\|exception\|traceback" | tail -10 || sudo journalctl -u luckyred-api -n 50 --no-pager 2>/dev/null | grep -i "error\|exception\|traceback" | tail -10 || echo "未找到错误日志"
echo ""

echo "□ 前端服务日志（最后 20 行，包含 error）:"
journalctl -u liaotian-frontend -n 50 --no-pager 2>/dev/null | grep -i "error\|exception\|traceback" | tail -10 || sudo journalctl -u liaotian-frontend -n 50 --no-pager 2>/dev/null | grep -i "error\|exception\|traceback" | tail -10 || echo "未找到错误日志"
echo ""

# ============================================================
# 诊断总结和建议
# ============================================================
echo "============================================================"
echo "诊断总结"
echo "============================================================"

# 检查关键问题
ISSUES_FOUND=0

if ! systemctl is-active --quiet nginx 2>/dev/null && ! sudo systemctl is-active --quiet nginx 2>/dev/null; then
    echo "❌ Nginx 服务未运行"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

if ! systemctl is-active --quiet liaotian-frontend 2>/dev/null && ! sudo systemctl is-active --quiet liaotian-frontend 2>/dev/null; then
    echo "❌ 前端服务未运行"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

if ! systemctl is-active --quiet luckyred-api 2>/dev/null && ! sudo systemctl is-active --quiet luckyred-api 2>/dev/null; then
    echo "❌ 后端服务未运行"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

if [ "$ISSUES_FOUND" -eq 0 ]; then
    echo "✅ 所有服务都在运行"
    echo ""
    echo "如果仍然无法访问，可能的原因："
    echo "1. 防火墙阻止了外部连接"
    echo "2. 服务器网络配置问题"
    echo "3. DNS 解析问题"
    echo "4. SSL 证书问题"
    echo ""
    echo "建议操作："
    echo "1. 检查防火墙规则: sudo ufw status"
    echo "2. 检查服务器 IP 和域名解析"
    echo "3. 检查 SSL 证书: sudo certbot certificates"
else
    echo ""
    echo "发现 $ISSUES_FOUND 个问题"
    echo ""
    echo "建议执行修复脚本:"
    echo "  sudo bash scripts/server/fix_500_fatal.sh"
    echo ""
    echo "或手动重启服务:"
    echo "  sudo systemctl restart nginx"
    echo "  sudo systemctl restart liaotian-frontend"
    echo "  sudo systemctl restart luckyred-api"
fi

echo ""
echo "============================================================"
echo "诊断完成"
echo "结束时间: $(date)"
echo "============================================================"

