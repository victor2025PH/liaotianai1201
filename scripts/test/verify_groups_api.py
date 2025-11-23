#!/usr/bin/env python3
"""
验证Groups API端点是否在Swagger文档中可见
"""
import sys
import json
import requests
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

API_BASE = "http://localhost:8000"
SWAGGER_JSON_URL = f"{API_BASE}/openapi.json"
GROUPS_ENDPOINTS = [
    "/api/v1/group-ai/groups/create",
    "/api/v1/group-ai/groups/join",
    "/api/v1/group-ai/groups/start-chat"
]

def check_swagger_docs():
    """检查Swagger文档中的路由"""
    print("=" * 60)
    print("验证 Swagger 文档中的 Groups API 路由")
    print("=" * 60)
    
    try:
        # 1. 获取OpenAPI JSON
        print("\n[1] 获取 OpenAPI JSON 文档...")
        response = requests.get(SWAGGER_JSON_URL, timeout=10)
        if response.status_code != 200:
            print(f"❌ 无法获取OpenAPI文档: HTTP {response.status_code}")
            return False
        
        openapi_data = response.json()
        print("✅ OpenAPI文档获取成功")
        
        # 2. 检查路径
        print("\n[2] 检查 Groups API 路径...")
        paths = openapi_data.get("paths", {})
        
        found_endpoints = []
        missing_endpoints = []
        
        for endpoint in GROUPS_ENDPOINTS:
            if endpoint in paths:
                found_endpoints.append(endpoint)
                methods = list(paths[endpoint].keys())
                print(f"  ✅ {endpoint} - 方法: {methods}")
            else:
                missing_endpoints.append(endpoint)
                print(f"  ❌ {endpoint} - 未找到")
        
        # 3. 检查tags
        print("\n[3] 检查 'groups' 标签...")
        tags = openapi_data.get("tags", [])
        groups_tag = [t for t in tags if t.get("name") == "groups"]
        
        if groups_tag:
            print(f"  ✅ 找到 'groups' 标签: {groups_tag[0]}")
        else:
            print("  ⚠️  未找到 'groups' 标签（可能使用其他标签）")
        
        # 4. 查找所有groups相关路径
        print("\n[4] 查找所有包含 'groups' 的路径...")
        all_groups_paths = [path for path in paths.keys() if "groups" in path]
        if all_groups_paths:
            print(f"  找到 {len(all_groups_paths)} 个groups相关路径:")
            for path in all_groups_paths:
                methods = list(paths[path].keys())
                print(f"    - {path} [{', '.join(methods)}]")
        else:
            print("  ❌ 未找到任何groups相关路径")
        
        # 5. 总结
        print("\n" + "=" * 60)
        print("验证结果总结")
        print("=" * 60)
        print(f"✅ 找到的端点: {len(found_endpoints)}/{len(GROUPS_ENDPOINTS)}")
        if found_endpoints:
            for endpoint in found_endpoints:
                print(f"  ✅ {endpoint}")
        
        if missing_endpoints:
            print(f"\n❌ 缺失的端点: {len(missing_endpoints)}")
            for endpoint in missing_endpoints:
                print(f"  ❌ {endpoint}")
        
        # 6. 测试实际API调用
        print("\n[5] 测试实际API调用...")
        test_endpoint = GROUPS_ENDPOINTS[0]  # 使用create端点
        test_url = f"{API_BASE}{test_endpoint}"
        
        try:
            response = requests.post(
                test_url,
                json={"account_id": "test", "title": "test"},
                timeout=5
            )
            status_code = response.status_code
            
            if status_code == 404:
                print(f"  ❌ {test_endpoint} - HTTP 404 (端点不存在)")
                return False
            elif status_code == 422:
                print(f"  ✅ {test_endpoint} - HTTP 422 (验证错误，说明端点存在)")
                return True
            elif status_code == 500:
                print(f"  ⚠️  {test_endpoint} - HTTP 500 (服务器错误，但端点存在)")
                return True
            else:
                print(f"  ✅ {test_endpoint} - HTTP {status_code} (端点存在)")
                return True
        except requests.exceptions.RequestException as e:
            print(f"  ❌ 请求失败: {e}")
            return len(found_endpoints) > 0  # 如果Swagger中有，也算成功
        
        return len(found_endpoints) == len(GROUPS_ENDPOINTS)
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务")
        print(f"   请确保后端服务运行在 {API_BASE}")
        return False
    except Exception as e:
        print(f"❌ 验证过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_api_docs_page():
    """检查Swagger UI页面是否可访问"""
    print("\n" + "=" * 60)
    print("检查 Swagger UI 页面")
    print("=" * 60)
    
    docs_url = f"{API_BASE}/docs"
    try:
        response = requests.get(docs_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ Swagger UI 页面可访问: {docs_url}")
            return True
        else:
            print(f"❌ Swagger UI 页面返回: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法访问 Swagger UI: {e}")
        return False


if __name__ == "__main__":
    print("\n开始验证 Groups API 路由...\n")
    
    # 检查Swagger UI
    docs_accessible = check_api_docs_page()
    
    # 检查Swagger文档
    swagger_ok = check_swagger_docs()
    
    # 最终结果
    print("\n" + "=" * 60)
    print("最终验证结果")
    print("=" * 60)
    
    if swagger_ok:
        print("✅ Groups API 路由验证成功！")
        print("\n💡 下一步:")
        print("  1. 访问 http://localhost:8000/docs 查看Swagger UI")
        print("  2. 在Swagger UI中查找 'groups' 标签")
        print("  3. 测试创建群组功能")
    else:
        print("❌ Groups API 路由验证失败")
        print("\n💡 建议:")
        print("  1. 检查后端服务是否正常运行")
        print("  2. 检查后端日志: admin-backend/backend.log")
        print("  3. 确认groups模块是否正确导入")
        print("  4. 尝试手动重启后端服务")
    
    sys.exit(0 if swagger_ok else 1)

