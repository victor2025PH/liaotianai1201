#!/bin/bash
# ============================================================
# 检查 API 500 错误
# ============================================================

set -e

echo "=========================================="
echo "检查 API 500 错误"
echo "=========================================="

BACKEND_SERVICE="luckyred-api"

# Step 1: 检查服务状态
echo ""
echo "[1/4] 检查后端服务状态..."
echo "----------------------------------------"
if systemctl is-active "$BACKEND_SERVICE" >/dev/null 2>&1; then
  echo "✅ 后端服务正在运行"
else
  echo "❌ 后端服务未运行"
  exit 1
fi

# Step 2: 检查最近的错误日志
echo ""
echo "[2/4] 检查最近的错误日志..."
echo "----------------------------------------"
echo "最后 50 行日志（包含错误）:"
sudo journalctl -u "$BACKEND_SERVICE" -n 50 --no-pager | grep -i "error\|exception\|traceback\|fail" | tail -20 || echo "  没有找到错误日志"

# Step 3: 测试 API 端点
echo ""
echo "[3/4] 测试 API 端点..."
echo "----------------------------------------"

# 测试健康检查
echo "测试 /health..."
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:8000/health 2>/dev/null || echo "ERROR")
HEALTH_CODE=$(echo "$HEALTH_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2 || echo "000")
if [ "$HEALTH_CODE" = "200" ]; then
  echo "✅ /health 正常 (HTTP $HEALTH_CODE)"
else
  echo "❌ /health 失败 (HTTP $HEALTH_CODE)"
  echo "  响应: $HEALTH_RESPONSE"
fi

# 测试 AI Provider API（不需要认证的端点）
echo ""
echo "测试 /api/v1/group-ai/ai-provider/providers..."
PROVIDERS_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:8000/api/v1/group-ai/ai-provider/providers 2>/dev/null || echo "ERROR")
PROVIDERS_CODE=$(echo "$PROVIDERS_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2 || echo "000")
PROVIDERS_BODY=$(echo "$PROVIDERS_RESPONSE" | grep -v "HTTP_CODE" || echo "")

if [ "$PROVIDERS_CODE" = "200" ] || [ "$PROVIDERS_CODE" = "401" ] || [ "$PROVIDERS_CODE" = "403" ]; then
  echo "✅ API 端点可访问 (HTTP $PROVIDERS_CODE)"
  if [ "$PROVIDERS_CODE" != "200" ]; then
    echo "  需要认证，这是正常的"
  fi
else
  echo "❌ API 端点失败 (HTTP $PROVIDERS_CODE)"
  echo "  响应: $PROVIDERS_BODY"
fi

# Step 4: 检查数据库连接
echo ""
echo "[4/4] 检查数据库连接..."
echo "----------------------------------------"
cd /home/ubuntu/telegram-ai-system/admin-backend 2>/dev/null || {
  echo "⚠️  无法进入后端目录"
  exit 1
}

if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
  
  # 检查数据库文件
  if [ -f "admin.db" ]; then
    echo "✅ 数据库文件存在"
    DB_SIZE=$(du -h admin.db | awk '{print $1}')
    echo "  数据库大小: $DB_SIZE"
  else
    echo "⚠️  数据库文件不存在"
  fi
  
  # 尝试导入模型（检查是否有语法错误）
  echo "检查 Python 模块导入..."
  if python3 -c "from app.models.group_ai import AIProviderConfig, AIProviderSettings, AIProviderKey" 2>&1; then
    echo "✅ 模型导入成功"
  else
    echo "❌ 模型导入失败"
    python3 -c "from app.models.group_ai import AIProviderConfig, AIProviderSettings, AIProviderKey" 2>&1 | head -10
  fi
else
  echo "⚠️  虚拟环境不存在"
fi

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="
echo ""
echo "如果 API 仍然返回 500，请查看详细日志:"
echo "  sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager | tail -50"
echo ""
echo "或者实时查看日志:"
echo "  sudo journalctl -u $BACKEND_SERVICE -f"

