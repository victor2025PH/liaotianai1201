#!/bin/bash
# ============================================================
# 验证 AI Provider API 部署状态
# ============================================================

echo "=========================================="
echo "验证 AI Provider API 部署状态"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 1. 检查后端服务状态
echo "[1/5] 检查后端服务状态..."
BACKEND_SERVICE=""
if systemctl cat luckyred-api.service >/dev/null 2>&1; then
  BACKEND_SERVICE="luckyred-api"
elif systemctl cat telegram-backend.service >/dev/null 2>&1; then
  BACKEND_SERVICE="telegram-backend"
fi

if [ -z "$BACKEND_SERVICE" ]; then
  echo "  ❌ 后端服务未找到"
  exit 1
fi

STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "unknown")
echo "  服务: $BACKEND_SERVICE"
echo "  状态: $STATUS"

if [ "$STATUS" != "active" ]; then
  echo "  ❌ 后端服务未运行"
  exit 1
fi

echo ""

# 2. 检查后端代码文件
echo "[2/5] 检查后端代码文件..."
AI_PROVIDER_FILE="$PROJECT_DIR/admin-backend/app/api/group_ai/ai_provider.py"
INIT_FILE="$PROJECT_DIR/admin-backend/app/api/group_ai/__init__.py"

if [ -f "$AI_PROVIDER_FILE" ]; then
  echo "  ✅ ai_provider.py 文件存在"
  
  # 检查关键端点
  if grep -q "@router.get(\"/providers\"" "$AI_PROVIDER_FILE"; then
    echo "  ✅ /providers 端点定义存在"
  else
    echo "  ❌ /providers 端点定义不存在"
  fi
else
  echo "  ❌ ai_provider.py 文件不存在"
fi

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

# 3. 检查后端进程是否加载了新代码
echo "[3/5] 检查后端进程..."
BACKEND_PID=$(systemctl show -p MainPID --value "$BACKEND_SERVICE" 2>/dev/null || echo "")
if [ -n "$BACKEND_PID" ] && [ "$BACKEND_PID" != "0" ]; then
  echo "  后端进程 PID: $BACKEND_PID"
  
  # 检查进程启动时间
  START_TIME=$(ps -o lstart= -p "$BACKEND_PID" 2>/dev/null || echo "")
  if [ -n "$START_TIME" ]; then
    echo "  进程启动时间: $START_TIME"
  fi
  
  # 检查进程加载的文件
  if [ -f "/proc/$BACKEND_PID/cmdline" ]; then
    CMDLINE=$(cat "/proc/$BACKEND_PID/cmdline" 2>/dev/null | tr '\0' ' ' || echo "")
    echo "  进程命令: $CMDLINE"
  fi
else
  echo "  ⚠️  无法获取后端进程信息"
fi

echo ""

# 4. 测试 API 端点
echo "[4/5] 测试 API 端点..."
echo "  测试: GET /api/v1/group-ai/ai-provider/providers"

RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:8000/api/v1/group-ai/ai-provider/providers 2>/dev/null || echo "ERROR")
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2 || echo "000")
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

echo "  HTTP 状态码: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
  echo "  ✅ 端点响应成功"
  echo "  响应内容（前100字符）:"
  echo "$BODY" | head -c 100 | sed 's/^/    /'
elif [ "$HTTP_CODE" = "404" ]; then
  echo "  ❌ 端点返回 404 (未找到)"
  echo ""
  echo "  可能原因："
  echo "    1. 后端服务未重启，未加载新代码"
  echo "    2. 路由未正确注册"
  echo "    3. 代码未正确部署到服务器"
  echo ""
  echo "  建议操作："
  echo "    1. 检查后端日志: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager | grep -i 'ai-provider\|error\|traceback'"
  echo "    2. 重启后端服务: sudo systemctl restart $BACKEND_SERVICE"
  echo "    3. 等待10秒后再次测试"
elif [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
  echo "  ⚠️  端点返回 $HTTP_CODE (需要认证)"
  echo "  这是正常的，端点存在但需要登录"
else
  echo "  ❌ 端点响应失败"
  echo "  响应: $BODY"
fi

echo ""

# 5. 检查后端日志中的错误
echo "[5/5] 检查后端日志..."
echo "  最近50行日志中的错误和警告:"
sudo journalctl -u "$BACKEND_SERVICE" -n 50 --no-pager 2>/dev/null | grep -iE "error|warning|traceback|ai-provider|ai_provider" | tail -10 || echo "  未找到相关错误"

echo ""
echo "=========================================="
echo "验证完成"
echo "=========================================="
echo ""
echo "如果端点返回404，请执行："
echo "  1. 重启后端服务: sudo systemctl restart $BACKEND_SERVICE"
echo "  2. 等待10秒: sleep 10"
echo "  3. 再次运行此脚本验证"
echo ""

