#!/bin/bash
# ============================================================
# 连接超时修复脚本
# ============================================================
# 
# 功能：
# 1. 重启所有服务（Nginx, 前端, 后端）
# 2. 检查并修复防火墙规则
# 3. 验证服务状态
# 4. 测试连接
#
# 使用方法：sudo bash scripts/server/fix_connection_timeout.sh
# ============================================================

set -e

echo "============================================================"
echo "连接超时修复脚本"
echo "============================================================"
echo "开始时间: $(date)"
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then
    echo "❌ 此脚本需要 root 权限，请使用 sudo 运行"
    echo "   使用方法: sudo bash scripts/server/fix_connection_timeout.sh"
    exit 1
fi

# ============================================================
# [1/5] 重启后端服务
# ============================================================
echo "[1/5] 重启后端服务"
echo "------------------------------------------------------------"
systemctl restart luckyred-api || {
    echo "❌ 重启后端服务失败"
    systemctl status luckyred-api --no-pager | head -10
    exit 1
}
sleep 3
if systemctl is-active --quiet luckyred-api; then
    echo "✅ 后端服务已重启并运行中"
else
    echo "❌ 后端服务启动失败"
    systemctl status luckyred-api --no-pager | head -10
    exit 1
fi
echo ""

# ============================================================
# [2/5] 重启前端服务
# ============================================================
echo "[2/5] 重启前端服务"
echo "------------------------------------------------------------"
systemctl restart liaotian-frontend || {
    echo "❌ 重启前端服务失败"
    systemctl status liaotian-frontend --no-pager | head -10
    exit 1
}
sleep 3
if systemctl is-active --quiet liaotian-frontend; then
    echo "✅ 前端服务已重启并运行中"
else
    echo "❌ 前端服务启动失败"
    systemctl status liaotian-frontend --no-pager | head -10
    exit 1
fi
echo ""

# ============================================================
# [3/5] 重启 Nginx
# ============================================================
echo "[3/5] 重启 Nginx"
echo "------------------------------------------------------------"
# 检查 Nginx 配置
if nginx -t 2>&1 | grep -q "syntax is ok"; then
    echo "✅ Nginx 配置语法正确"
    systemctl restart nginx || {
        echo "❌ 重启 Nginx 失败"
        systemctl status nginx --no-pager | head -10
        exit 1
    }
    sleep 2
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已重启并运行中"
    else
        echo "❌ Nginx 启动失败"
        systemctl status nginx --no-pager | head -10
        exit 1
    fi
else
    echo "❌ Nginx 配置语法错误"
    nginx -t
    exit 1
fi
echo ""

# ============================================================
# [4/5] 检查并修复防火墙
# ============================================================
echo "[4/5] 检查并修复防火墙"
echo "------------------------------------------------------------"

# 检查 UFW
if command -v ufw > /dev/null 2>&1; then
    UFW_STATUS=$(ufw status | head -1)
    if echo "$UFW_STATUS" | grep -q "Status: active"; then
        echo "□ UFW 已启用，检查端口规则..."
        
        # 确保 HTTP 和 HTTPS 端口开放
        if ! ufw status | grep -q "80/tcp"; then
            echo "  开放端口 80 (HTTP)..."
            ufw allow 80/tcp || echo "⚠️  开放端口 80 失败"
        fi
        
        if ! ufw status | grep -q "443/tcp"; then
            echo "  开放端口 443 (HTTPS)..."
            ufw allow 443/tcp || echo "⚠️  开放端口 443 失败"
        fi
        
        echo "✅ 防火墙规则已检查"
    else
        echo "□ UFW 未启用，跳过防火墙配置"
    fi
else
    echo "□ UFW 未安装，跳过防火墙配置"
fi
echo ""

# ============================================================
# [5/5] 验证服务状态和连接
# ============================================================
echo "[5/5] 验证服务状态和连接"
echo "------------------------------------------------------------"

# 等待服务完全启动
echo "等待服务启动 (10秒)..."
sleep 10

# 检查端口监听
echo "□ 检查端口监听:"
PORTS_OK=true

if ss -tlnp 2>/dev/null | grep -q ":80 "; then
    echo "✅ 端口 80 正在监听"
else
    echo "❌ 端口 80 未监听"
    PORTS_OK=false
fi

if ss -tlnp 2>/dev/null | grep -q ":443 "; then
    echo "✅ 端口 443 正在监听"
else
    echo "❌ 端口 443 未监听"
    PORTS_OK=false
fi

if ss -tlnp 2>/dev/null | grep -q ":3000 "; then
    echo "✅ 端口 3000 正在监听"
else
    echo "❌ 端口 3000 未监听"
    PORTS_OK=false
fi

if ss -tlnp 2>/dev/null | grep -q ":8000 "; then
    echo "✅ 端口 8000 正在监听"
else
    echo "❌ 端口 8000 未监听"
    PORTS_OK=false
fi
echo ""

# 测试本地连接
echo "□ 测试本地连接:"
CONNECTION_OK=true

# 测试前端
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:3000/ 2>/dev/null || echo "000")
if [ "$FRONTEND_CODE" = "200" ] || [ "$FRONTEND_CODE" = "302" ] || [ "$FRONTEND_CODE" = "301" ]; then
    echo "✅ 前端本地连接正常 (HTTP $FRONTEND_CODE)"
else
    echo "❌ 前端本地连接失败 (HTTP $FRONTEND_CODE)"
    CONNECTION_OK=false
fi

# 测试后端
BACKEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:8000/api/v1/health 2>/dev/null || echo "000")
if [ "$BACKEND_CODE" = "200" ]; then
    echo "✅ 后端本地连接正常 (HTTP $BACKEND_CODE)"
else
    echo "❌ 后端本地连接失败 (HTTP $BACKEND_CODE)"
    CONNECTION_OK=false
fi

# 测试 Nginx
NGINX_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1/ 2>/dev/null || echo "000")
if [ "$NGINX_CODE" = "200" ] || [ "$NGINX_CODE" = "302" ] || [ "$NGINX_CODE" = "301" ]; then
    echo "✅ Nginx 本地连接正常 (HTTP $NGINX_CODE)"
else
    echo "❌ Nginx 本地连接失败 (HTTP $NGINX_CODE)"
    CONNECTION_OK=false
fi
echo ""

# ============================================================
# 修复总结
# ============================================================
echo "============================================================"
echo "修复总结"
echo "============================================================"

if [ "$PORTS_OK" = true ] && [ "$CONNECTION_OK" = true ]; then
    echo "✅ 所有服务已重启，端口正常监听，本地连接正常"
    echo ""
    echo "如果外部仍然无法访问，可能的原因："
    echo "1. 服务器防火墙（云服务商安全组）阻止了外部连接"
    echo "2. 服务器网络配置问题"
    echo "3. DNS 解析问题"
    echo ""
    echo "建议检查："
    echo "1. 云服务商安全组规则（确保 80 和 443 端口开放）"
    echo "2. 服务器 IP 地址是否正确"
    echo "3. 域名 DNS 解析是否正确"
else
    echo "⚠️  部分服务可能存在问题"
    echo ""
    echo "请查看上述错误信息，并检查："
    echo "1. 服务日志: sudo journalctl -u [service-name] -n 50 --no-pager"
    echo "2. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
fi

echo ""
echo "============================================================"
echo "修复完成"
echo "结束时间: $(date)"
echo "============================================================"

