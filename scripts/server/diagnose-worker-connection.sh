#!/bin/bash
# ============================================================
# Worker 节点连接诊断脚本
# ============================================================

set -e

echo "=========================================="
echo "🔍 Worker 节点连接诊断"
echo "=========================================="
echo ""

SERVER_URL="${SERVER_URL:-https://aikz.usdt2026.cc}"
HEARTBEAT_ENDPOINT="${SERVER_URL}/api/v1/workers/heartbeat"

echo "服务器配置:"
echo "  - 服务器 URL: $SERVER_URL"
echo "  - 心跳端点: $HEARTBEAT_ENDPOINT"
echo ""

# 1. 检查网络连接
echo "[1/6] 检查网络连接..."
echo "  - 测试 DNS 解析..."
if host aikz.usdt2026.cc >/dev/null 2>&1; then
    IP=$(host aikz.usdt2026.cc | grep "has address" | awk '{print $4}' | head -1)
    echo "    ✅ DNS 解析成功: $IP"
else
    echo "    ❌ DNS 解析失败"
    echo "    请检查网络连接或 DNS 配置"
fi

echo "  - 测试 HTTP 连接..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$SERVER_URL" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "    ✅ HTTP 连接成功 (状态码: $HTTP_CODE)"
else
    echo "    ❌ HTTP 连接失败 (状态码: $HTTP_CODE)"
    echo "    请检查网络连接或服务器是否运行"
fi

echo "  - 测试 HTTPS 连接..."
HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$SERVER_URL" 2>/dev/null || echo "000")
if [ "$HTTPS_CODE" = "200" ] || [ "$HTTPS_CODE" = "301" ] || [ "$HTTPS_CODE" = "302" ]; then
    echo "    ✅ HTTPS 连接成功 (状态码: $HTTPS_CODE)"
else
    echo "    ❌ HTTPS 连接失败 (状态码: $HTTPS_CODE)"
fi
echo ""

# 2. 检查 SSL 证书
echo "[2/6] 检查 SSL 证书..."
SSL_INFO=$(echo | openssl s_client -connect aikz.usdt2026.cc:443 -servername aikz.usdt2026.cc 2>/dev/null | openssl x509 -noout -dates -subject 2>/dev/null || echo "")
if [ -n "$SSL_INFO" ]; then
    echo "    ✅ SSL 证书有效"
    echo "$SSL_INFO" | grep -E "notBefore|notAfter|subject" | sed 's/^/      /'
else
    echo "    ❌ 无法获取 SSL 证书信息"
    echo "    请检查 SSL 证书是否有效或网络连接"
fi
echo ""

# 3. 检查防火墙
echo "[3/6] 检查防火墙设置..."
if command -v ufw >/dev/null 2>&1; then
    UFW_STATUS=$(sudo ufw status 2>/dev/null | head -1 || echo "")
    echo "    UFW 状态: $UFW_STATUS"
    if echo "$UFW_STATUS" | grep -q "inactive"; then
        echo "    ✅ UFW 防火墙未激活"
    else
        echo "    ⚠️  UFW 防火墙已激活，请确保允许出站连接"
    fi
elif command -v firewall-cmd >/dev/null 2>&1; then
    FIREWALLD_STATUS=$(sudo firewall-cmd --state 2>/dev/null || echo "not running")
    echo "    Firewalld 状态: $FIREWALLD_STATUS"
    if [ "$FIREWALLD_STATUS" = "not running" ]; then
        echo "    ✅ Firewalld 防火墙未运行"
    else
        echo "    ⚠️  Firewalld 防火墙已运行，请确保允许出站连接"
    fi
else
    echo "    ⚠️  未检测到常见防火墙工具，请手动检查防火墙设置"
fi
echo ""

# 4. 测试后端 API 端点
echo "[4/6] 测试后端 API 端点..."
echo "  - 测试健康检查端点..."
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "${SERVER_URL}/health" 2>/dev/null || echo "000")
if [ "$HEALTH_CODE" = "200" ]; then
    echo "    ✅ 健康检查端点可访问 (状态码: $HEALTH_CODE)"
else
    echo "    ❌ 健康检查端点不可访问 (状态码: $HEALTH_CODE)"
fi

echo "  - 测试心跳端点..."
HEARTBEAT_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 -X POST "$HEARTBEAT_ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{"node_id":"test","status":"online","account_count":0,"accounts":[]}' 2>/dev/null || echo "000")
if [ "$HEARTBEAT_CODE" = "200" ] || [ "$HEARTBEAT_CODE" = "401" ] || [ "$HEARTBEAT_CODE" = "403" ]; then
    echo "    ✅ 心跳端点可访问 (状态码: $HEARTBEAT_CODE)"
    if [ "$HEARTBEAT_CODE" = "401" ] || [ "$HEARTBEAT_CODE" = "403" ]; then
        echo "      注意: 需要认证，这是正常的"
    fi
else
    echo "    ❌ 心跳端点不可访问 (状态码: $HEARTBEAT_CODE)"
    echo "      请检查后端服务是否运行"
fi
echo ""

# 5. 检查 Worker 节点配置
echo "[5/6] 检查 Worker 节点配置..."
if [ -f "worker_config.py" ]; then
    echo "    ✅ 找到 worker_config.py"
    if grep -q "SERVER_URL\|server_url" worker_config.py 2>/dev/null; then
        CONFIG_URL=$(grep -E "SERVER_URL|server_url" worker_config.py | head -1 | sed 's/.*=//' | tr -d ' "\'"' || echo "")
        echo "    配置的服务器 URL: $CONFIG_URL"
        if [ "$CONFIG_URL" = "$SERVER_URL" ] || [ -z "$CONFIG_URL" ]; then
            echo "    ✅ 服务器 URL 配置正确"
        else
            echo "    ⚠️  服务器 URL 配置可能不匹配"
        fi
    fi
elif [ -f "config.py" ]; then
    echo "    ✅ 找到 config.py"
    if grep -q "SERVER_URL\|server_url" config.py 2>/dev/null; then
        CONFIG_URL=$(grep -E "SERVER_URL|server_url" config.py | head -1 | sed 's/.*=//' | tr -d ' "\'"' || echo "")
        echo "    配置的服务器 URL: $CONFIG_URL"
    fi
else
    echo "    ⚠️  未找到 Worker 配置文件"
    echo "    请确认 Worker 节点配置文件位置"
fi
echo ""

# 6. 检查 Worker 节点进程
echo "[6/6] 检查 Worker 节点进程..."
WORKER_PROCESSES=$(ps aux | grep -E "worker|python.*worker" | grep -v grep || echo "")
if [ -n "$WORKER_PROCESSES" ]; then
    echo "    ✅ 找到 Worker 进程:"
    echo "$WORKER_PROCESSES" | head -3 | sed 's/^/      /'
else
    echo "    ❌ 未找到 Worker 进程"
    echo "    请确认 Worker 节点是否正在运行"
fi
echo ""

# 总结
echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "建议："
echo "  1. 如果网络连接失败，检查网络配置和 DNS 设置"
echo "  2. 如果 SSL 证书无效，检查证书是否过期"
echo "  3. 如果防火墙阻止，允许出站 HTTPS 连接（端口 443）"
echo "  4. 如果 API 端点不可访问，检查后端服务状态"
echo "  5. 如果 Worker 进程未运行，启动 Worker 节点"
echo ""

