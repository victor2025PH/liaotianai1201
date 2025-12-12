#!/bin/bash
# ============================================================
# 检查 AI Provider API 路由是否正确注册
# ============================================================

echo "=========================================="
echo "检查 AI Provider API 路由"
echo "=========================================="
echo ""

# 1. 检查后端服务状态
echo "[1/4] 检查后端服务状态..."
if systemctl cat luckyred-api.service >/dev/null 2>&1; then
  BACKEND_SERVICE="luckyred-api"
elif systemctl cat telegram-backend.service >/dev/null 2>&1; then
  BACKEND_SERVICE="telegram-backend"
else
  echo "  ❌ 后端服务未找到"
  exit 1
fi

STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "unknown")
echo "  服务: $BACKEND_SERVICE"
echo "  状态: $STATUS"

if [ "$STATUS" != "active" ]; then
  echo "  ⚠️  后端服务未运行"
  exit 1
fi

echo ""

# 2. 测试 API 端点
echo "[2/4] 测试 AI Provider API 端点..."
echo "  测试: GET /api/v1/group-ai/ai-provider/providers"

RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:8000/api/v1/group-ai/ai-provider/providers 2>/dev/null || echo "ERROR")
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

if [ "$HTTP_CODE" = "200" ]; then
  echo "  ✅ 端点响应成功 (HTTP $HTTP_CODE)"
  echo "  响应内容:"
  echo "$BODY" | head -5 | sed 's/^/    /'
elif [ "$HTTP_CODE" = "404" ]; then
  echo "  ❌ 端点返回 404 (未找到)"
  echo "  可能原因："
  echo "    1. 路由未正确注册"
  echo "    2. 后端代码未更新"
  echo "    3. 服务未重启"
elif [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
  echo "  ⚠️  端点返回 $HTTP_CODE (需要认证)"
  echo "  这是正常的，端点存在但需要登录"
else
  echo "  ❌ 端点响应失败 (HTTP $HTTP_CODE)"
  echo "  响应: $BODY"
fi

echo ""

# 3. 检查后端代码文件
echo "[3/4] 检查后端代码文件..."
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
AI_PROVIDER_FILE="$PROJECT_DIR/admin-backend/app/api/group_ai/ai_provider.py"

if [ -f "$AI_PROVIDER_FILE" ]; then
  echo "  ✅ ai_provider.py 文件存在"
  
  # 检查文件是否包含关键端点
  if grep -q "@router.get(\"/providers\"" "$AI_PROVIDER_FILE"; then
    echo "  ✅ /providers 端点定义存在"
  else
    echo "  ❌ /providers 端点定义不存在"
  fi
  
  if grep -q "@router.post(\"/update-key\"" "$AI_PROVIDER_FILE"; then
    echo "  ✅ /update-key 端点定义存在"
  else
    echo "  ❌ /update-key 端点定义不存在"
  fi
  
  if grep -q "@router.post(\"/test\"" "$AI_PROVIDER_FILE"; then
    echo "  ✅ /test 端点定义存在"
  else
    echo "  ❌ /test 端点定义不存在"
  fi
else
  echo "  ❌ ai_provider.py 文件不存在"
fi

echo ""

# 4. 检查路由注册
echo "[4/4] 检查路由注册..."
INIT_FILE="$PROJECT_DIR/admin-backend/app/api/group_ai/__init__.py"

if [ -f "$INIT_FILE" ]; then
  echo "  ✅ __init__.py 文件存在"
  
  if grep -q "ai_provider" "$INIT_FILE"; then
    echo "  ✅ ai_provider 模块已导入"
    
    if grep -q "ai_provider.router" "$INIT_FILE"; then
      echo "  ✅ ai_provider.router 已注册"
    else
      echo "  ❌ ai_provider.router 未注册"
    fi
  else
    echo "  ❌ ai_provider 模块未导入"
  fi
else
  echo "  ❌ __init__.py 文件不存在"
fi

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="
echo ""
echo "如果端点返回404，请执行："
echo "  1. 检查后端服务日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
echo "  2. 重启后端服务: sudo systemctl restart $BACKEND_SERVICE"
echo "  3. 等待10秒后再次测试"
echo ""

