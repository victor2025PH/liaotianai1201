#!/bin/bash
# 深度调试 AI Provider API 路由问题

set -e

echo "=========================================="
echo "深度调试 AI Provider API 路由"
echo "=========================================="

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
ADMIN_BACKEND="$PROJECT_ROOT/admin-backend"
VENV_PATH="$ADMIN_BACKEND/.venv"

cd "$ADMIN_BACKEND"
source "$VENV_PATH/bin/activate"

echo ""
echo "[1] 检查 Python 导入..."
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/home/ubuntu/telegram-ai-system/admin-backend')

try:
    print("导入 ai_provider 模块...")
    from app.api.group_ai import ai_provider
    print("✅ ai_provider 模块导入成功")
    print(f"   Router: {ai_provider.router}")
    print(f"   Routes: {[r.path for r in ai_provider.router.routes]}")
except Exception as e:
    print(f"❌ ai_provider 模块导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n导入数据库模型...")
    from app.models.group_ai import AIProviderConfig, AIProviderSettings
    print("✅ 数据库模型导入成功")
except Exception as e:
    print(f"❌ 数据库模型导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n检查路由注册...")
    from app.api.group_ai import router as group_ai_router
    print(f"✅ group_ai router: {group_ai_router}")
    
    # 查找 ai-provider 路由
    ai_provider_routes = [r for r in group_ai_router.routes if 'ai-provider' in str(r.path)]
    if ai_provider_routes:
        print(f"✅ 找到 {len(ai_provider_routes)} 个 ai-provider 路由:")
        for r in ai_provider_routes:
            print(f"   - {r.path} ({r.methods if hasattr(r, 'methods') else 'N/A'})")
    else:
        print("⚠️  未找到 ai-provider 路由")
        
except Exception as e:
    print(f"❌ 路由检查失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n检查主应用路由...")
    from app.api import router as api_router
    print(f"✅ API router: {api_router}")
    
    # 查找 group-ai 路由
    group_ai_routes = [r for r in api_router.routes if 'group-ai' in str(r.path)]
    print(f"✅ 找到 {len(group_ai_routes)} 个 group-ai 路由")
    
except Exception as e:
    print(f"❌ 主应用路由检查失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

echo ""
echo "[2] 检查后端服务状态..."
if sudo systemctl is-active --quiet luckyred-api; then
    echo "✅ 后端服务正在运行"
else
    echo "❌ 后端服务未运行"
    echo "查看日志:"
    sudo journalctl -u luckyred-api -n 30
    exit 1
fi

echo ""
echo "[3] 检查后端服务日志（最近50行）..."
sudo journalctl -u luckyred-api -n 50 --no-pager | grep -i "error\|exception\|traceback\|ai.provider\|ai-provider" || echo "未找到相关错误"

echo ""
echo "[4] 测试本地 API 端点..."
sleep 2

ENDPOINTS=(
    "/api/v1/group-ai/ai-provider/providers"
    "/api/v1/group-ai/ai-provider/status"
)

for endpoint in "${ENDPOINTS[@]}"; do
    echo -n "测试 $endpoint ... "
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000$endpoint" 2>&1 || echo "000")
    if [ "$response" = "200" ] || [ "$response" = "401" ] || [ "$response" = "403" ]; then
        echo "✅ HTTP $response"
    else
        echo "❌ HTTP $response"
        echo "   详细响应:"
        curl -s "http://localhost:8000$endpoint" | head -20 || echo "   无法连接"
    fi
done

echo ""
echo "[5] 检查所有注册的路由..."
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/home/ubuntu/telegram-ai-system/admin-backend')

try:
    from app.main import app
    print("✅ FastAPI 应用加载成功")
    
    # 获取所有路由
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append((route.path, route.methods))
    
    # 查找 ai-provider 相关路由
    ai_provider_routes = [r for r in routes if 'ai-provider' in r[0] or 'ai_provider' in r[0]]
    
    if ai_provider_routes:
        print(f"\n✅ 找到 {len(ai_provider_routes)} 个 AI Provider 路由:")
        for path, methods in ai_provider_routes:
            print(f"   {', '.join(methods)} {path}")
    else:
        print("\n❌ 未找到 AI Provider 路由！")
        print("\n所有 group-ai 路由:")
        group_ai_routes = [r for r in routes if 'group-ai' in r[0]]
        for path, methods in group_ai_routes[:20]:  # 只显示前20个
            print(f"   {', '.join(methods)} {path}")
        
except Exception as e:
    print(f"❌ 检查路由失败: {e}")
    import traceback
    traceback.print_exc()
PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "调试完成"
echo "=========================================="

