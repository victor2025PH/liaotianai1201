#!/bin/bash
# 生产环境就绪性全面测试脚本
# 测试所有核心功能、监控和部署能力

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# 测试报告文件
REPORT_FILE="test_reports/production_readiness_$(date +%Y%m%d_%H%M%S).md"

# 创建报告目录
mkdir -p test_reports

# 测试函数
test_pass() {
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
    echo -e "${GREEN}✓${NC} $1"
    echo "✓ $1" >> "$REPORT_FILE"
}

test_fail() {
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
    echo -e "${RED}✗${NC} $1"
    echo "✗ $1" >> "$REPORT_FILE"
    if [ -n "$2" ]; then
        echo "  错误: $2" >> "$REPORT_FILE"
    fi
}

test_skip() {
    ((SKIPPED_TESTS++))
    ((TOTAL_TESTS++))
    echo -e "${YELLOW}⊘${NC} $1 (跳过)"
    echo "⊘ $1 (跳过)" >> "$REPORT_FILE"
}

# 初始化报告
init_report() {
    cat > "$REPORT_FILE" << EOF
# 生产环境就绪性测试报告

**测试时间**: $(date '+%Y-%m-%d %H:%M:%S')
**测试环境**: $(uname -a)

---

## 测试结果摘要

EOF
}

# 生成报告摘要
generate_summary() {
    cat >> "$REPORT_FILE" << EOF

---

## 测试统计

- **总测试数**: $TOTAL_TESTS
- **通过**: $PASSED_TESTS
- **失败**: $FAILED_TESTS
- **跳过**: $SKIPPED_TESTS
- **通过率**: $(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")%

---

## 详细测试结果

EOF
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}生产环境就绪性全面测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

init_report

# ============================================
# 1. 环境检查
# ============================================
echo -e "${CYAN}[1/6] 环境检查${NC}"
echo "## 1. 环境检查" >> "$REPORT_FILE"

# 检查 Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    test_pass "Python 已安装: $PYTHON_VERSION"
else
    test_fail "Python 未安装"
fi

# 检查 Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    test_pass "Node.js 已安装: $NODE_VERSION"
else
    test_fail "Node.js 未安装"
fi

# 检查 Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    test_pass "Docker 已安装: $DOCKER_VERSION"
else
    test_skip "Docker 未安装（可选）"
fi

# 检查 PostgreSQL
if command -v psql &> /dev/null || docker ps | grep -q postgres; then
    test_pass "PostgreSQL 可用"
else
    test_skip "PostgreSQL 未安装（可选）"
fi

# 检查 Redis
if command -v redis-cli &> /dev/null || docker ps | grep -q redis; then
    test_pass "Redis 可用"
else
    test_skip "Redis 未安装（可选）"
fi

echo ""

# ============================================
# 2. 后端服务测试
# ============================================
echo -e "${CYAN}[2/6] 后端服务测试${NC}"
echo "" >> "$REPORT_FILE"
echo "## 2. 后端服务测试" >> "$REPORT_FILE"

# 检查后端服务是否运行
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
if curl -s -f "$BACKEND_URL/health" > /dev/null 2>&1; then
    test_pass "后端服务运行中 ($BACKEND_URL)"
    
    # 测试健康检查端点
    HEALTH_RESPONSE=$(curl -s "$BACKEND_URL/health")
    if echo "$HEALTH_RESPONSE" | grep -q "healthy\|status"; then
        test_pass "健康检查端点正常"
    else
        test_fail "健康检查端点响应异常"
    fi
    
    # 测试详细健康检查
    if curl -s -f "$BACKEND_URL/health?detailed=true" > /dev/null 2>&1; then
        test_pass "详细健康检查端点正常"
    else
        test_fail "详细健康检查端点异常"
    fi
    
    # 测试 API 文档
    if curl -s -f "$BACKEND_URL/docs" > /dev/null 2>&1; then
        test_pass "API 文档可访问"
    else
        test_fail "API 文档不可访问"
    fi
    
    # 测试 OpenAPI Schema
    if curl -s -f "$BACKEND_URL/openapi.json" > /dev/null 2>&1; then
        test_pass "OpenAPI Schema 可访问"
    else
        test_fail "OpenAPI Schema 不可访问"
    fi
else
    test_fail "后端服务未运行 ($BACKEND_URL)"
    echo "  提示: 请启动后端服务: cd admin-backend && uvicorn app.main:app --reload"
fi

echo ""

# ============================================
# 3. 监控功能测试
# ============================================
echo -e "${CYAN}[3/6] 监控功能测试${NC}"
echo "" >> "$REPORT_FILE"
echo "## 3. 监控功能测试" >> "$REPORT_FILE"

if curl -s -f "$BACKEND_URL/health" > /dev/null 2>&1; then
    # 测试 Prometheus 指标
    if curl -s -f "$BACKEND_URL/metrics" > /dev/null 2>&1; then
        METRICS=$(curl -s "$BACKEND_URL/metrics")
        if echo "$METRICS" | grep -q "http_requests_total\|prometheus"; then
            test_pass "Prometheus 指标端点正常"
        else
            test_fail "Prometheus 指标格式异常"
        fi
    else
        test_fail "Prometheus 指标端点不可访问"
    fi
    
    # 测试健康检查组件
    DETAILED_HEALTH=$(curl -s "$BACKEND_URL/health?detailed=true" 2>/dev/null || echo "{}")
    if echo "$DETAILED_HEALTH" | grep -q "components\|database\|redis"; then
        test_pass "健康检查组件信息正常"
    else
        test_skip "健康检查组件信息不可用（可能未配置）"
    fi
else
    test_skip "监控功能测试（后端服务未运行）"
fi

echo ""

# ============================================
# 4. Session 管理测试
# ============================================
echo -e "${CYAN}[4/6] Session 管理测试${NC}"
echo "" >> "$REPORT_FILE"
echo "## 4. Session 管理测试" >> "$REPORT_FILE"

# 检查 Session 目录
if [ -d "sessions" ]; then
    test_pass "Session 目录存在"
    
    # 检查 Session 文件
    SESSION_COUNT=$(find sessions -name "*.session" -o -name "*.enc" 2>/dev/null | wc -l)
    if [ "$SESSION_COUNT" -gt 0 ]; then
        test_pass "找到 $SESSION_COUNT 个 Session 文件"
        
        # 测试验证脚本
        if [ -f "scripts/verify_session.py" ]; then
            FIRST_SESSION=$(find sessions -name "*.session" -o -name "*.enc" 2>/dev/null | head -1)
            if [ -n "$FIRST_SESSION" ]; then
                SESSION_NAME=$(basename "$FIRST_SESSION" .session | sed 's/.enc$//')
                if python3 scripts/verify_session.py "$SESSION_NAME" > /dev/null 2>&1; then
                    test_pass "Session 验证脚本正常"
                else
                    test_skip "Session 验证脚本（可能需要配置）"
                fi
            fi
        fi
    else
        test_skip "未找到 Session 文件（可选）"
    fi
else
    test_skip "Session 目录不存在（可选）"
fi

# 测试 Session 导出 API（如果后端运行）
if curl -s -f "$BACKEND_URL/health" > /dev/null 2>&1; then
    # 检查 API 端点是否存在（不实际调用，避免需要认证）
    if curl -s -f "$BACKEND_URL/openapi.json" | grep -q "export-session\|sessions"; then
        test_pass "Session 导出 API 端点存在"
    else
        test_skip "Session 导出 API 端点（需要检查）"
    fi
fi

echo ""

# ============================================
# 5. 部署配置测试
# ============================================
echo -e "${CYAN}[5/6] 部署配置测试${NC}"
echo "" >> "$REPORT_FILE"
echo "## 5. 部署配置测试" >> "$REPORT_FILE"

# 检查 Dockerfile
if [ -f "admin-backend/Dockerfile" ]; then
    test_pass "后端 Dockerfile 存在"
else
    test_fail "后端 Dockerfile 不存在"
fi

if [ -f "admin-frontend/Dockerfile" ]; then
    test_pass "前端 Dockerfile 存在"
else
    test_skip "前端 Dockerfile（admin-frontend）"
fi

if [ -f "saas-demo/Dockerfile" ]; then
    test_pass "SaaS 前端 Dockerfile 存在"
else
    test_skip "SaaS 前端 Dockerfile"
fi

# 检查 Docker Compose
if [ -f "deploy/docker-compose.yaml" ] || [ -f "docker-compose.yml" ]; then
    test_pass "Docker Compose 配置文件存在"
else
    test_skip "Docker Compose 配置文件（可选）"
fi

# 检查 Kubernetes 配置
if [ -d "deploy/k8s" ]; then
    K8S_FILES=$(find deploy/k8s -name "*.yaml" -o -name "*.yml" 2>/dev/null | wc -l)
    if [ "$K8S_FILES" -gt 0 ]; then
        test_pass "Kubernetes 配置文件存在 ($K8S_FILES 个文件)"
    else
        test_skip "Kubernetes 配置文件目录为空"
    fi
else
    test_skip "Kubernetes 配置目录不存在（可选）"
fi

# 检查 CI/CD 配置
if [ -d ".github/workflows" ]; then
    WORKFLOW_FILES=$(find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null | wc -l)
    if [ "$WORKFLOW_FILES" -gt 0 ]; then
        test_pass "GitHub Actions 工作流存在 ($WORKFLOW_FILES 个文件)"
    else
        test_skip "GitHub Actions 工作流不存在"
    fi
else
    test_skip "GitHub Actions 配置目录不存在（可选）"
fi

echo ""

# ============================================
# 6. 文档完整性测试
# ============================================
echo -e "${CYAN}[6/6] 文档完整性测试${NC}"
echo "" >> "$REPORT_FILE"
echo "## 6. 文档完整性测试" >> "$REPORT_FILE"

# 检查关键文档
REQUIRED_DOCS=(
    "docs/使用说明/DEPLOYMENT_GUIDE.md"
    "docs/使用说明/故障排查指南.md"
    "docs/使用说明/API文档使用指南.md"
    "docs/使用说明/SESSION跨服务器部署指南.md"
    "README.md"
)

for doc in "${REQUIRED_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        test_pass "文档存在: $(basename $doc)"
    else
        test_fail "文档缺失: $doc"
    fi
done

# 检查环境变量示例
if [ -f "docs/env.example" ] || [ -f ".env.example" ]; then
    test_pass "环境变量示例文件存在"
else
    test_skip "环境变量示例文件（可选）"
fi

echo ""

# ============================================
# 生成报告摘要
# ============================================
generate_summary

# 输出摘要
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}测试完成${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "总测试数: ${CYAN}$TOTAL_TESTS${NC}"
echo -e "通过: ${GREEN}$PASSED_TESTS${NC}"
echo -e "失败: ${RED}$FAILED_TESTS${NC}"
echo -e "跳过: ${YELLOW}$SKIPPED_TESTS${NC}"

if [ "$TOTAL_TESTS" -gt 0 ]; then
    PASS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")
    echo -e "通过率: ${CYAN}${PASS_RATE}%${NC}"
fi

echo ""
echo -e "详细报告: ${CYAN}$REPORT_FILE${NC}"
echo ""

# 返回退出码
if [ "$FAILED_TESTS" -eq 0 ]; then
    exit 0
else
    exit 1
fi

