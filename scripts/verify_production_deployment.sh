#!/bin/bash
# 生产环境部署验证脚本
# 用于全面验证 AI 聊天系统的生产环境部署状态

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_ROOT/admin-backend"
FRONTEND_DIRS=(
    "$PROJECT_ROOT/aizkw20251219"
    "$PROJECT_ROOT/hbwy20251220"
    "$PROJECT_ROOT/tgmini20251220"
)

echo "=========================================="
echo "生产环境部署验证"
echo "=========================================="
echo ""

# 1. 检查项目目录
echo -e "${BLUE}[1/10] 检查项目目录...${NC}"
if [ ! -d "$PROJECT_ROOT" ]; then
    echo -e "${RED}❌ 项目根目录不存在: $PROJECT_ROOT${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 项目根目录存在${NC}"

if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ 后端目录不存在: $BACKEND_DIR${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 后端目录存在${NC}"
echo ""

# 2. 检查后端服务状态
echo -e "${BLUE}[2/10] 检查后端服务状态...${NC}"
if ! pm2 list | grep -q "backend.*online"; then
    echo -e "${RED}❌ 后端服务未运行${NC}"
    pm2 list | grep backend || echo "未找到 backend 进程"
    exit 1
fi
echo -e "${GREEN}✅ 后端服务正在运行${NC}"
pm2 list | grep backend
echo ""

# 3. 检查后端端口
echo -e "${BLUE}[3/10] 检查后端端口 (8000)...${NC}"
if ! netstat -tlnp 2>/dev/null | grep -q ":8000" && ! ss -tlnp 2>/dev/null | grep -q ":8000"; then
    echo -e "${YELLOW}⚠️  端口 8000 未监听（可能使用其他方式检查）${NC}"
else
    echo -e "${GREEN}✅ 端口 8000 正在监听${NC}"
fi
echo ""

# 4. 检查环境变量配置
echo -e "${BLUE}[4/10] 检查环境变量配置...${NC}"
cd "$BACKEND_DIR" || exit 1

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env 文件不存在${NC}"
    exit 1
fi
echo -e "${GREEN}✅ .env 文件存在${NC}"

# 检查 API Keys
if grep -q "OPENAI_API_KEY" .env && ! grep -q "^OPENAI_API_KEY=$" .env && ! grep -q "^OPENAI_API_KEY=\"\"" .env; then
    OPENAI_KEY=$(grep "^OPENAI_API_KEY=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'" | head -c 10)
    if [ -n "$OPENAI_KEY" ]; then
        echo -e "${GREEN}✅ OPENAI_API_KEY 已配置 (${OPENAI_KEY}...)${NC}"
    else
        echo -e "${YELLOW}⚠️  OPENAI_API_KEY 为空${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY 未配置或为空${NC}"
fi

if grep -q "GEMINI_API_KEY" .env && ! grep -q "^GEMINI_API_KEY=$" .env && ! grep -q "^GEMINI_API_KEY=\"\"" .env; then
    GEMINI_KEY=$(grep "^GEMINI_API_KEY=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'" | head -c 10)
    if [ -n "$GEMINI_KEY" ]; then
        echo -e "${GREEN}✅ GEMINI_API_KEY 已配置 (${GEMINI_KEY}...)${NC}"
    else
        echo -e "${YELLOW}⚠️  GEMINI_API_KEY 为空${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  GEMINI_API_KEY 未配置或为空${NC}"
fi
echo ""

# 5. 测试本地 API
echo -e "${BLUE}[5/10] 测试本地 API 端点...${NC}"
LOCAL_API="http://127.0.0.1:8000/api/v1/frontend-config/ai-keys"

if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$LOCAL_API" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ 本地 API 响应正常 (HTTP $HTTP_CODE)${NC}"
        RESPONSE=$(curl -s "$LOCAL_API" 2>/dev/null)
        echo "响应内容:"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    else
        echo -e "${RED}❌ 本地 API 响应异常 (HTTP $HTTP_CODE)${NC}"
        echo "尝试获取详细错误:"
        curl -s "$LOCAL_API" || echo "无法连接"
    fi
else
    echo -e "${YELLOW}⚠️  curl 未安装，跳过 API 测试${NC}"
fi
echo ""

# 6. 测试远程 API
echo -e "${BLUE}[6/10] 测试远程 API 端点...${NC}"
REMOTE_API="https://aiadmin.usdt2026.cc/api/v1/frontend-config/ai-keys"

if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -k -o /dev/null -w "%{http_code}" "$REMOTE_API" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ 远程 API 响应正常 (HTTP $HTTP_CODE)${NC}"
        RESPONSE=$(curl -s -k "$REMOTE_API" 2>/dev/null)
        echo "响应内容:"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    else
        echo -e "${YELLOW}⚠️  远程 API 响应异常 (HTTP $HTTP_CODE)${NC}"
        echo "可能的原因: Nginx 配置、SSL 证书、防火墙"
    fi
else
    echo -e "${YELLOW}⚠️  curl 未安装，跳过远程 API 测试${NC}"
fi
echo ""

# 7. 检查路由注册
echo -e "${BLUE}[7/10] 检查后端路由注册...${NC}"
if [ -f "$BACKEND_DIR/app/api/frontend_config.py" ]; then
    if grep -q "prefix=\"/frontend-config\"" "$BACKEND_DIR/app/api/frontend_config.py"; then
        echo -e "${GREEN}✅ 路由前缀配置正确${NC}"
    else
        echo -e "${RED}❌ 路由前缀配置错误${NC}"
    fi
    
    if grep -q "router.include_router(frontend_config.router)" "$BACKEND_DIR/app/api/__init__.py" 2>/dev/null; then
        echo -e "${GREEN}✅ 路由已正确注册${NC}"
    else
        echo -e "${RED}❌ 路由未注册${NC}"
    fi
else
    echo -e "${RED}❌ frontend_config.py 文件不存在${NC}"
fi
echo ""

# 8. 检查前端服务
echo -e "${BLUE}[8/10] 检查前端服务状态...${NC}"
FRONTEND_SERVICES=("aizkw-frontend" "hongbao-frontend" "tgmini-frontend")
ALL_FRONTEND_OK=true

for service in "${FRONTEND_SERVICES[@]}"; do
    if pm2 list | grep -q "$service.*online"; then
        echo -e "${GREEN}✅ $service 正在运行${NC}"
    else
        echo -e "${YELLOW}⚠️  $service 未运行或状态异常${NC}"
        ALL_FRONTEND_OK=false
    fi
done

if [ "$ALL_FRONTEND_OK" = true ]; then
    echo -e "${GREEN}✅ 所有前端服务正常运行${NC}"
else
    echo -e "${YELLOW}⚠️  部分前端服务异常${NC}"
fi
echo ""

# 9. 检查后端日志
echo -e "${BLUE}[9/10] 检查后端最近日志...${NC}"
ERROR_COUNT=$(pm2 logs backend --lines 50 --nostream 2>/dev/null | grep -i "error\|exception\|traceback\|not found" | wc -l || echo "0")

if [ "$ERROR_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  发现 $ERROR_COUNT 个错误/警告${NC}"
    echo "最近的错误:"
    pm2 logs backend --lines 20 --nostream 2>/dev/null | grep -i "error\|exception\|traceback\|not found" | tail -5 || echo "无法获取日志"
else
    echo -e "${GREEN}✅ 未发现明显错误${NC}"
fi
echo ""

# 10. 检查 Python 环境
echo -e "${BLUE}[10/10] 检查 Python 环境...${NC}"
if [ -f "$BACKEND_DIR/venv/bin/python" ] || [ -f "$BACKEND_DIR/.venv/bin/python" ]; then
    echo -e "${GREEN}✅ Python 虚拟环境存在${NC}"
    
    # 检查关键依赖
    if [ -f "$BACKEND_DIR/venv/bin/python" ]; then
        PYTHON_BIN="$BACKEND_DIR/venv/bin/python"
    else
        PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
    fi
    
    # 检查 fastapi
    if $PYTHON_BIN -c "import fastapi" 2>/dev/null; then
        echo -e "${GREEN}✅ FastAPI 已安装${NC}"
    else
        echo -e "${RED}❌ FastAPI 未安装${NC}"
    fi
    
    # 检查 pydantic
    if $PYTHON_BIN -c "import pydantic_settings" 2>/dev/null; then
        echo -e "${GREEN}✅ Pydantic Settings 已安装${NC}"
    else
        echo -e "${RED}❌ Pydantic Settings 未安装${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Python 虚拟环境未找到${NC}"
fi
echo ""

# 总结
echo "=========================================="
echo "验证完成"
echo "=========================================="
echo ""
echo "如果发现问题，请参考: docs/AI_CHAT_FIX_PLAN.md"
echo ""

