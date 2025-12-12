#!/bin/bash
# 验证 AI Provider 路由是否正确注册

set -e

echo "=========================================="
echo "验证 AI Provider 路由"
echo "=========================================="

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
ADMIN_BACKEND="$PROJECT_ROOT/admin-backend"
VENV_PATH="$ADMIN_BACKEND/.venv"

cd "$ADMIN_BACKEND"
source "$VENV_PATH/bin/activate"

echo ""
echo "[1] 检查模块导入..."
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/home/ubuntu/telegram-ai-system/admin-backend')

try:
    print("导入 ai_provider 模块...")
    from app.api.group_ai import ai_provider
    print("✅ ai_provider 模块导入成功")
    print(f"   Router prefix: {ai_provider.router.prefix}")
    print(f"   Routes count: {len(ai_provider.router.routes)}")
    
    # 列出所有路由
    print("\n   路由列表:")
    for route in ai_provider.router.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(route.methods) if route.methods else 'N/A'
            print(f"      {methods} {route.path}")
except Exception as e:
    print(f"❌ ai_provider 模块导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

echo ""
echo "[2] 检查路由注册..."
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/home/ubuntu/telegram-ai-system/admin-backend')

try:
    print("检查 group_ai router...")
    from app.api.group_ai import router as group_ai_router
    print(f"✅ group_ai router: {group_ai_router}")
    
    # 查找 ai-provider 路由
    ai_provider_routes = []
    for route in group_ai_router.routes:
        if hasattr(route, 'path') and ('ai-provider' in str(route.path) or 'ai_provider' in str(route.path)):
            ai_provider_routes.append(route)
        elif hasattr(route, 'routes'):  # 可能是子路由
            for sub_route in route.routes:
                if hasattr(sub_route, 'path') and ('ai-provider' in str(sub_route.path) or 'ai_provider' in str(sub_route.path)):
                    ai_provider_routes.append(sub_route)
    
    if ai_provider_routes:
        print(f"✅ 找到 {len(ai_provider_routes)} 个 AI Provider 路由:")
        for route in ai_provider_routes:
            methods = ', '.join(route.methods) if hasattr(route, 'methods') and route.methods else 'N/A'
            path = route.path if hasattr(route, 'path') else str(route)
            print(f"      {methods} {path}")
    else:
        print("❌ 未找到 AI Provider 路由！")
        print("\n所有 group_ai 路由:")
        for route in list(group_ai_router.routes)[:10]:
            if hasattr(route, 'path'):
                methods = ', '.join(route.methods) if hasattr(route, 'methods') and route.methods else 'N/A'
                print(f"      {methods} {route.path}")
        
except Exception as e:
    print(f"❌ 路由检查失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

echo ""
echo "[3] 检查主应用路由..."
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/home/ubuntu/telegram-ai-system/admin-backend')

try:
    print("加载 FastAPI 应用...")
    from app.main import app
    print("✅ FastAPI 应用加载成功")
    
    # 获取所有路由
    all_routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            all_routes.append((route.path, route.methods))
    
    # 查找 ai-provider 路由
    ai_provider_routes = [r for r in all_routes if 'ai-provider' in r[0] or 'ai_provider' in r[0]]
    
    if ai_provider_routes:
        print(f"✅ 在主应用中找到 {len(ai_provider_routes)} 个 AI Provider 路由:")
        for path, methods in ai_provider_routes:
            print(f"      {', '.join(methods)} {path}")
    else:
        print("❌ 在主应用中未找到 AI Provider 路由！")
        print("\n所有 group-ai 路由（前20个）:")
        group_ai_routes = [r for r in all_routes if 'group-ai' in r[0]]
        for path, methods in group_ai_routes[:20]:
            print(f"      {', '.join(methods)} {path}")
        
except Exception as e:
    print(f"❌ 主应用路由检查失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

echo ""
echo "[4] 测试 API 端点..."
sleep 2

ENDPOINTS=(
    "/api/v1/group-ai/ai-provider/providers"
    "/api/v1/group-ai/ai-provider/status"
    "/api/v1/group-ai/ai-provider/switch"
)

for endpoint in "${ENDPOINTS[@]}"; do
    echo -n "测试 $endpoint ... "
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000$endpoint" 2>&1 || echo "000")
    if [ "$response" = "200" ] || [ "$response" = "401" ] || [ "$response" = "403" ]; then
        echo "✅ HTTP $response"
    elif [ "$response" = "404" ]; then
        echo "❌ HTTP 404 (路由未找到)"
        echo "   详细响应:"
        curl -s "http://localhost:8000$endpoint" | head -5 || echo "   无法连接"
    else
        echo "⚠️  HTTP $response"
    fi
done

echo ""
echo "=========================================="
echo "验证完成"
echo "=========================================="
echo ""
echo "如果路由未找到，请："
echo "1. 检查代码是否正确: ls -la $ADMIN_BACKEND/app/api/group_ai/ai_provider.py"
echo "2. 重启后端服务: sudo systemctl restart luckyred-api"
echo "3. 查看服务日志: sudo journalctl -u luckyred-api -n 50"
echo ""

