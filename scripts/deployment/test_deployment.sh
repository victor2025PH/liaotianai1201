#!/bin/bash
# 部署后测试脚本
# 使用方法: ./test_deployment.sh <server_ip> [username]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SERVER_IP="${1:-165.154.255.48}"
USERNAME="${2:-ubuntu}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}部署后测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "服务器: ${CYAN}${SERVER_IP}${NC}"
echo ""

# 测试计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

test_pass() {
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
    echo -e "${GREEN}✓${NC} $1"
}

test_fail() {
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
    echo -e "${RED}✗${NC} $1"
}

# 1. 测试服务可访问性
echo -e "${CYAN}[1/6] 测试服务可访问性...${NC}"
if curl -s -f --max-time 10 "http://${SERVER_IP}:8000/health" > /dev/null; then
    test_pass "服务可访问"
else
    test_fail "服务不可访问"
    echo "  提示: 检查防火墙和端口配置"
fi

# 2. 测试健康检查端点
echo -e "${CYAN}[2/6] 测试健康检查端点...${NC}"
HEALTH_RESPONSE=$(curl -s "http://${SERVER_IP}:8000/health" 2>/dev/null || echo "{}")
if echo "$HEALTH_RESPONSE" | grep -q "healthy\|status"; then
    test_pass "健康检查端点正常"
else
    test_fail "健康检查端点异常"
fi

# 3. 测试 API 文档
echo -e "${CYAN}[3/6] 测试 API 文档...${NC}"
if curl -s -f --max-time 10 "http://${SERVER_IP}:8000/docs" > /dev/null; then
    test_pass "API 文档可访问"
else
    test_fail "API 文档不可访问"
fi

# 4. 测试 OpenAPI Schema
echo -e "${CYAN}[4/6] 测试 OpenAPI Schema...${NC}"
if curl -s -f --max-time 10 "http://${SERVER_IP}:8000/openapi.json" > /dev/null; then
    SCHEMA=$(curl -s "http://${SERVER_IP}:8000/openapi.json")
    if echo "$SCHEMA" | grep -q "paths"; then
        PATH_COUNT=$(echo "$SCHEMA" | grep -o '"paths"' | wc -l)
        test_pass "OpenAPI Schema 正常"
    else
        test_fail "OpenAPI Schema 格式异常"
    fi
else
    test_fail "OpenAPI Schema 不可访问"
fi

# 5. 测试系统优化 API（如果已部署）
echo -e "${CYAN}[5/6] 测试系统优化 API...${NC}"
# 注意：这些端点需要认证，这里只测试端点是否存在
if curl -s -f --max-time 10 "http://${SERVER_IP}:8000/openapi.json" | grep -q "optimization"; then
    test_pass "系统优化 API 端点存在"
else
    test_fail "系统优化 API 端点不存在"
fi

# 6. 测试性能监控
echo -e "${CYAN}[6/6] 测试性能监控...${NC}"
if curl -s -f --max-time 10 "http://${SERVER_IP}:8000/metrics" > /dev/null; then
    METRICS=$(curl -s "http://${SERVER_IP}:8000/metrics")
    if echo "$METRICS" | grep -q "http_requests\|prometheus"; then
        test_pass "Prometheus 指标正常"
    else
        test_fail "Prometheus 指标格式异常"
    fi
else
    test_fail "Prometheus 指标端点不可访问"
fi

# 输出摘要
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}测试完成${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "总测试数: ${CYAN}${TOTAL_TESTS}${NC}"
echo -e "通过: ${GREEN}${PASSED_TESTS}${NC}"
echo -e "失败: ${RED}${FAILED_TESTS}${NC}"

if [ "$TOTAL_TESTS" -gt 0 ]; then
    PASS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")
    echo -e "通过率: ${CYAN}${PASS_RATE}%${NC}"
fi

echo ""
echo -e "服务地址: ${CYAN}http://${SERVER_IP}:8000${NC}"
echo -e "API 文档: ${CYAN}http://${SERVER_IP}:8000/docs${NC}"

# 返回退出码
if [ "$FAILED_TESTS" -eq 0 ]; then
    exit 0
else
    exit 1
fi

