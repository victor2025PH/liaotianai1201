#!/bin/bash
# ============================================================
# 修复数据库修复后的 502 错误
# ============================================================

set -e

echo "=========================================="
echo "修复 502 Bad Gateway 错误"
echo "=========================================="

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
BACKEND_SERVICE="luckyred-api"

# Step 1: 检查后端服务状态
echo ""
echo "[1/6] 检查后端服务状态..."
echo "----------------------------------------"
if systemctl is-active "$BACKEND_SERVICE" >/dev/null 2>&1; then
  echo "✅ 后端服务正在运行"
else
  echo "❌ 后端服务未运行"
fi

# Step 2: 检查端口 8000
echo ""
echo "[2/6] 检查端口 8000..."
echo "----------------------------------------"
PORT_8000_PID=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || echo "")
if [ -n "$PORT_8000_PID" ]; then
  echo "✅ 端口 8000 正在监听 (PID: $PORT_8000_PID)"
else
  echo "❌ 端口 8000 未监听"
fi

# Step 3: 查看后端服务日志
echo ""
echo "[3/6] 查看后端服务最近日志..."
echo "----------------------------------------"
sudo journalctl -u "$BACKEND_SERVICE" -n 50 --no-pager | tail -30 || echo "无法查看日志"

# Step 4: 检查数据库文件
echo ""
echo "[4/6] 检查数据库文件..."
echo "----------------------------------------"
DB_PATH="$BACKEND_DIR/admin.db"
if [ -f "$DB_PATH" ]; then
  echo "✅ 数据库文件存在: $DB_PATH"
  DB_SIZE=$(du -h "$DB_PATH" | awk '{print $1}')
  echo "  数据库大小: $DB_SIZE"
  
  # 检查数据库列
  cd "$BACKEND_DIR" || exit 1
  if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    python3 << 'PYTHON_SCRIPT'
import sqlite3
import sys

db_path = "admin.db"
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查 ai_provider_configs 表的列
    cursor.execute("PRAGMA table_info(ai_provider_configs)")
    configs_columns = [row[1] for row in cursor.fetchall()]
    print("ai_provider_configs 表的列:")
    for col in configs_columns:
        print(f"  ✅ {col}")
    
    required_configs_cols = ['id', 'provider_name', 'key_name', 'api_key', 'is_valid', 'is_active', 'last_tested', 'usage_stats']
    missing_configs_cols = [col for col in required_configs_cols if col not in configs_columns]
    if missing_configs_cols:
        print(f"  ❌ 缺少列: {missing_configs_cols}")
    else:
        print("  ✅ 所有必需的列都存在")
    
    # 检查 ai_provider_settings 表的列
    cursor.execute("PRAGMA table_info(ai_provider_settings)")
    settings_columns = [row[1] for row in cursor.fetchall()]
    print("\nai_provider_settings 表的列:")
    for col in settings_columns:
        print(f"  ✅ {col}")
    
    required_settings_cols = ['id', 'current_provider', 'auto_failover_enabled', 'failover_providers', 'active_keys']
    missing_settings_cols = [col for col in required_settings_cols if col not in settings_columns]
    if missing_settings_cols:
        print(f"  ❌ 缺少列: {missing_settings_cols}")
    else:
        print("  ✅ 所有必需的列都存在")
    
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"❌ 检查数据库失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT
  fi
else
  echo "❌ 数据库文件不存在: $DB_PATH"
fi

# Step 5: 清理端口并重启服务
echo ""
echo "[5/6] 清理端口并重启服务..."
echo "----------------------------------------"

# 停止服务
echo "停止后端服务..."
sudo systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
sleep 2

# 清理端口
if [ -n "$PORT_8000_PID" ]; then
  echo "清理端口 8000 (PID: $PORT_8000_PID)..."
  sudo kill -9 "$PORT_8000_PID" 2>/dev/null || true
  sleep 2
fi

# 清理所有 uvicorn 进程
echo "清理所有 uvicorn 进程..."
sudo pkill -9 -f "uvicorn.*8000" 2>/dev/null || true
sudo pkill -9 -f "uvicorn.*app.main" 2>/dev/null || true
sleep 2

# 重新加载 systemd
echo "重新加载 systemd..."
sudo systemctl daemon-reload

# 启动服务
echo "启动后端服务..."
sudo systemctl start "$BACKEND_SERVICE"
sleep 10

# Step 6: 验证服务
echo ""
echo "[6/6] 验证服务..."
echo "----------------------------------------"

# 检查服务状态
STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "unknown")
if [ "$STATUS" = "active" ]; then
  echo "✅ 后端服务已启动 (状态: $STATUS)"
else
  echo "❌ 后端服务启动失败 (状态: $STATUS)"
  echo "查看详细日志:"
  sudo journalctl -u "$BACKEND_SERVICE" -n 100 --no-pager | tail -50
  exit 1
fi

# 检查端口
sleep 3
PORT_8000_AFTER=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
if [ -n "$PORT_8000_AFTER" ]; then
  NEW_PID=$(echo "$PORT_8000_AFTER" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || echo "")
  echo "✅ 端口 8000 正在监听 (PID: $NEW_PID)"
else
  echo "❌ 端口 8000 未监听"
  echo "查看日志: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager"
  exit 1
fi

# 测试健康检查
echo "测试健康检查..."
if curl -s --max-time 5 http://localhost:8000/health >/dev/null 2>&1; then
  echo "✅ 健康检查通过"
else
  echo "❌ 健康检查失败"
  echo "查看日志: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager | tail -50"
  exit 1
fi

# 测试 AI Provider API
echo "测试 AI Provider API..."
API_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" --max-time 5 http://localhost:8000/api/v1/group-ai/ai-provider/providers 2>/dev/null || echo "ERROR")
API_CODE=$(echo "$API_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2 || echo "000")
if [ "$API_CODE" = "200" ] || [ "$API_CODE" = "401" ] || [ "$API_CODE" = "403" ]; then
  echo "✅ AI Provider API 可访问 (HTTP $API_CODE)"
else
  echo "⚠️  AI Provider API 返回 (HTTP $API_CODE)"
  echo "响应: $(echo "$API_RESPONSE" | grep -v "HTTP_CODE" | head -5)"
fi

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="
echo ""
echo "如果仍有 502 错误，请检查："
echo "  1. Nginx 配置: sudo nginx -t"
echo "  2. Nginx 日志: sudo tail -50 /var/log/nginx/error.log"
echo "  3. 后端日志: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager"
echo ""

