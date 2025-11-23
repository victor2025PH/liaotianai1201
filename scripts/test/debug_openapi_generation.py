#!/usr/bin/env python3
"""
调试OpenAPI生成过程
详细检查为什么groups路由没有出现在OpenAPI文档中
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "admin-backend"))

def check_route_registration():
    """检查路由注册过程"""
    print("=" * 60)
    print("检查路由注册过程")
    print("=" * 60)
    
    # 1. 检查groups模块
    print("\n[1] 检查groups模块...")
    try:
        from app.api.group_ai import groups
        print(f"   ✅ Groups模块导入成功")
        print(f"   Router routes: {len(groups.router.routes)}")
        for route in groups.router.routes:
            if hasattr(route, 'path'):
                print(f"      - {route.path}")
    except Exception as e:
        print(f"   ❌ Groups模块导入失败: {e}")
        return
    
    # 2. 检查group_ai.__init__
    print("\n[2] 检查group_ai.__init__...")
    try:
        from app.api.group_ai import __init__ as group_ai_init
        print(f"   ✅ Group-AI模块导入成功")
        print(f"   Router routes: {len(group_ai_init.router.routes)}")
        
        groups_routes = [r for r in group_ai_init.router.routes if hasattr(r, 'path') and 'groups' in str(r.path)]
        print(f"   Groups路由数: {len(groups_routes)}")
        if groups_routes:
            for r in groups_routes:
                print(f"      ✅ {r.path}")
        else:
            print("      ❌ 未找到groups路由")
    except Exception as e:
        print(f"   ❌ Group-AI模块导入失败: {e}")
        return
    
    # 3. 检查api.__init__
    print("\n[3] 检查api.__init__...")
    try:
        from app.api import __init__ as api_init
        print(f"   ✅ API模块导入成功")
        print(f"   Router routes: {len(api_init.router.routes)}")
        
        groups_routes = [r for r in api_init.router.routes if hasattr(r, 'path') and 'groups' in str(r.path)]
        print(f"   Groups路由数: {len(groups_routes)}")
    except Exception as e:
        print(f"   ❌ API模块导入失败: {e}")
        return
    
    # 4. 检查主应用
    print("\n[4] 检查主应用...")
    try:
        from app.main import app
        print(f"   ✅ 主应用导入成功")
        print(f"   总路由数: {len(app.routes)}")
        
        groups_routes = [r for r in app.routes if hasattr(r, 'path') and 'groups' in str(r.path)]
        print(f"   Groups路由数: {len(groups_routes)}")
        if groups_routes:
            for r in groups_routes:
                print(f"      ✅ {r.path}")
                print(f"         类型: {type(r).__name__}")
                print(f"         包含在schema: {getattr(r, 'include_in_schema', True)}")
        else:
            print("      ❌ 未找到groups路由")
    except Exception as e:
        print(f"   ❌ 主应用导入失败: {e}")
        return
    
    # 5. 检查OpenAPI schema
    print("\n[5] 检查OpenAPI schema...")
    try:
        openapi_schema = app.openapi()
        paths = openapi_schema.get('paths', {})
        print(f"   OpenAPI路径数: {len(paths)}")
        
        groups_paths = [p for p in paths.keys() if 'groups' in p]
        print(f"   Groups路径数: {len(groups_paths)}")
        if groups_paths:
            for p in groups_paths:
                print(f"      ✅ {p}")
        else:
            print("      ❌ 未找到groups路径")
            
            # 检查所有group-ai路径
            group_ai_paths = [p for p in paths.keys() if 'group-ai' in p]
            print(f"\n   Group-AI路径数: {len(group_ai_paths)}")
            if group_ai_paths:
                print("   前10个Group-AI路径:")
                for p in group_ai_paths[:10]:
                    print(f"      - {p}")
    except Exception as e:
        print(f"   ❌ OpenAPI schema生成失败: {e}")
        import traceback
        traceback.print_exc()
        return

def check_route_details():
    """检查路由的详细信息"""
    print("\n" + "=" * 60)
    print("检查路由详细信息")
    print("=" * 60)
    
    try:
        from app.main import app
        
        # 查找groups路由
        groups_routes = [r for r in app.routes if hasattr(r, 'path') and 'groups' in str(r.path)]
        
        if groups_routes:
            print(f"\n找到 {len(groups_routes)} 个groups路由:")
            for i, route in enumerate(groups_routes, 1):
                print(f"\n路由 {i}:")
                print(f"  路径: {route.path}")
                print(f"  类型: {type(route).__name__}")
                print(f"  包含在schema: {getattr(route, 'include_in_schema', '未知')}")
                print(f"  方法: {getattr(route, 'methods', '未知')}")
                print(f"  标签: {getattr(route, 'tags', '未知')}")
                
                # 检查路由的依赖
                if hasattr(route, 'dependant'):
                    print(f"  依赖: {route.dependant}")
                
                # 检查端点
                if hasattr(route, 'endpoint'):
                    endpoint = route.endpoint
                    print(f"  端点函数: {getattr(endpoint, '__name__', '未知')}")
                    print(f"  端点模块: {getattr(endpoint, '__module__', '未知')}")
        else:
            print("\n❌ 未找到groups路由")
            
            # 检查所有路由类型
            print("\n所有路由类型统计:")
            route_types = {}
            for route in app.routes:
                route_type = type(route).__name__
                route_types[route_type] = route_types.get(route_type, 0) + 1
            for rt, count in sorted(route_types.items()):
                print(f"  {rt}: {count}")
                
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n开始调试OpenAPI生成过程...\n")
    
    check_route_registration()
    check_route_details()
    
    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)

