#!/bin/bash
# AI API 验证脚本
# 用于快速诊断和验证 AI 对话功能的 API 配置

set -e

echo "=========================================="
echo "AI API 配置验证脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 检查后端服务状态
echo "1. 检查后端服务状态..."
if pm2 list | grep -q "backend.*online"; then
    echo -e "${GREEN}✅ 后端服务正在运行${NC}"
    pm2 list | grep backend
else
    echo -e "${RED}❌ 后端服务未运行${NC}"
    echo "请执行: pm2 start backend 或 pm2 restart backend"
    exit 1
fi
echo ""

# 2. 检查环境变量
echo "2. 检查环境变量配置..."
# 使用正确的项目路径
PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_ROOT/admin-backend"

if [ -d "$BACKEND_DIR" ]; then
    cd "$BACKEND_DIR" || exit 1
else
    # 尝试从脚本位置推断
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    if [ -d "$SCRIPT_DIR/../admin-backend" ]; then
        cd "$SCRIPT_DIR/../admin-backend" || exit 1
    else
        echo "❌ 无法找到 admin-backend 目录"
        exit 1
    fi
fi

if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env 文件存在${NC}"
    
    if grep -q "OPENAI_API_KEY" .env && ! grep -q "^OPENAI_API_KEY=$" .env; then
        echo -e "${GREEN}✅ OPENAI_API_KEY 已配置${NC}"
    else
        echo -e "${YELLOW}⚠️  OPENAI_API_KEY 未配置或为空${NC}"
    fi
    
    if grep -q "GEMINI_API_KEY" .env && ! grep -q "^GEMINI_API_KEY=$" .env; then
        echo -e "${GREEN}✅ GEMINI_API_KEY 已配置${NC}"
    else
        echo -e "${YELLOW}⚠️  GEMINI_API_KEY 未配置或为空${NC}"
    fi
else
    echo -e "${RED}❌ .env 文件不存在${NC}"
fi
echo ""

# 3. 测试本地 API
echo "3. 测试本地 API 端点..."
LOCAL_API="http://127.0.0.1:8000/api/v1/frontend-config/ai-keys"

if command -v curl &> /dev/null; then
    RESPONSE=$(curl -s -w "\n%{http_code}" "$LOCAL_API" || echo -e "\n000")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ 本地 API 响应正常 (HTTP $HTTP_CODE)${NC}"
        echo "响应内容:"
        echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    else
        echo -e "${RED}❌ 本地 API 响应异常 (HTTP $HTTP_CODE)${NC}"
        echo "响应内容: $BODY"
    fi
else
    echo -e "${YELLOW}⚠️  curl 未安装，跳过本地 API 测试${NC}"
fi
echo ""

# 4. 测试远程 API
echo "4. 测试远程 API 端点..."
REMOTE_API="https://aiadmin.usdt2026.cc/api/v1/frontend-config/ai-keys"

if command -v curl &> /dev/null; then
    RESPONSE=$(curl -s -w "\n%{http_code}" "$REMOTE_API" || echo -e "\n000")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ 远程 API 响应正常 (HTTP $HTTP_CODE)${NC}"
        echo "响应内容:"
        echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    else
        echo -e "${RED}❌ 远程 API 响应异常 (HTTP $HTTP_CODE)${NC}"
        echo "响应内容: $BODY"
        echo ""
        echo "可能的原因:"
        echo "  - Nginx 配置错误"
        echo "  - SSL 证书问题"
        echo "  - 防火墙阻止"
    fi
else
    echo -e "${YELLOW}⚠️  curl 未安装，跳过远程 API 测试${NC}"
fi
echo ""

# 5. 检查路由注册
echo "5. 检查路由注册..."
if [ -f "app/api/frontend_config.py" ]; then
    if grep -q "prefix=\"/frontend-config\"" app/api/frontend_config.py; then
        echo -e "${GREEN}✅ 路由前缀配置正确${NC}"
    else
        echo -e "${RED}❌ 路由前缀配置错误${NC}"
        echo "应该为: prefix=\"/frontend-config\""
    fi
    
    if grep -q "router.include_router(frontend_config.router)" app/api/__init__.py 2>/dev/null; then
        echo -e "${GREEN}✅ 路由已正确注册${NC}"
    else
        echo -e "${RED}❌ 路由未注册${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  无法找到 frontend_config.py${NC}"
fi
echo ""

# 6. 检查后端日志
echo "6. 检查后端最近日志..."
if pm2 logs backend --lines 10 --nostream 2>/dev/null | grep -i "error\|exception\|traceback" | tail -5; then
    echo -e "${YELLOW}⚠️  发现错误日志，请检查${NC}"
else
    echo -e "${GREEN}✅ 未发现明显错误${NC}"
fi
echo ""

# 总结
echo "=========================================="
echo "验证完成"
echo "=========================================="
echo ""
echo "如果发现问题，请参考: docs/AI_CHAT_FIX_PLAN.md"
echo ""

