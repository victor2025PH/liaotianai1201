#!/usr/bin/env python3
"""
功能测试脚本
测试性能监控、健康检查、告警管理等功能
"""
import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 测试用的认证token（需要先登录获取）
AUTH_TOKEN = None


def login() -> str:
    """登录获取token"""
    try:
        # 使用默认管理员账号
        response = requests.post(
            f"{API_BASE}/auth/login",
            data={
                "username": "admin@example.com",
                "password": "changeme123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"登录异常: {e}")
        return None


def test_health_check() -> Dict[str, Any]:
    """测试健康检查端点"""
    print("\n=== 测试健康检查端点 ===")
    results = {}
    
    # 测试基础健康检查
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        results["basic_health"] = {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        }
        print(f"✓ 基础健康检查: {response.status_code}")
    except Exception as e:
        results["basic_health"] = {"error": str(e)}
        print(f"✗ 基础健康检查失败: {e}")
    
    # 测试详细健康检查
    try:
        response = requests.get(f"{BASE_URL}/health?detailed=true", timeout=10)
        results["detailed_health"] = {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text[:200]
        }
        print(f"✓ 详细健康检查: {response.status_code}")
    except Exception as e:
        results["detailed_health"] = {"error": str(e)}
        print(f"✗ 详细健康检查失败: {e}")
    
    # 测试K8s健康检查
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=5)
        results["k8s_health"] = {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        }
        print(f"✓ K8s健康检查: {response.status_code}")
    except Exception as e:
        results["k8s_health"] = {"error": str(e)}
        print(f"✗ K8s健康检查失败: {e}")
    
    return results


def test_performance_api(token: str) -> Dict[str, Any]:
    """测试性能监控API"""
    print("\n=== 测试性能监控API ===")
    results = {}
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        start_time = time.time()
        response = requests.get(f"{API_BASE}/system/performance", headers=headers, timeout=10)
        elapsed = (time.time() - start_time) * 1000
        
        results["performance_stats"] = {
            "status_code": response.status_code,
            "response_time_ms": elapsed,
            "response": response.json() if response.status_code == 200 else response.text[:200]
        }
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 性能统计API: {response.status_code}")
            print(f"  - 请求总数: {data.get('request_count', 'N/A')}")
            print(f"  - 平均响应时间: {data.get('average_response_time_ms', 'N/A')}ms")
            print(f"  - 慢请求数: {data.get('slow_requests_count', 'N/A')}")
        else:
            print(f"✗ 性能统计API失败: {response.status_code}")
    except Exception as e:
        results["performance_stats"] = {"error": str(e)}
        print(f"✗ 性能统计API异常: {e}")
    
    return results


def test_alert_management(token: str) -> Dict[str, Any]:
    """测试告警管理API"""
    print("\n=== 测试告警管理API ===")
    results = {}
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试告警统计
    try:
        response = requests.get(
            f"{API_BASE}/group-ai/alert-management/statistics",
            headers=headers,
            timeout=10
        )
        results["alert_statistics"] = {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text[:200]
        }
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 告警统计API: {response.status_code}")
            print(f"  - 总告警数: {data.get('total_alerts', 'N/A')}")
            print(f"  - 活跃告警数: {data.get('total_active', 'N/A')}")
        else:
            print(f"✗ 告警统计API失败: {response.status_code}")
    except Exception as e:
        results["alert_statistics"] = {"error": str(e)}
        print(f"✗ 告警统计API异常: {e}")
    
    # 测试添加告警
    try:
        test_alert = {
            "alert_key": f"test_alert_{int(time.time())}",
            "severity": "medium",
            "message": "测试告警",
            "source": "test_script"
        }
        # 注意：这里需要根据实际的告警添加API调整
        # 如果告警是通过其他服务添加的，这里可能无法直接测试
        print("  ℹ 告警添加需要通过其他服务触发")
    except Exception as e:
        print(f"  ⚠ 告警添加测试跳过: {e}")
    
    return results


def test_api_response_times(token: str) -> Dict[str, Any]:
    """测试API响应时间"""
    print("\n=== 测试API响应时间 ===")
    results = {}
    
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        ("/health", False),
        ("/api/v1/group-ai/dashboard", True),
        ("/api/v1/group-ai/scripts", True),
        ("/api/v1/group-ai/accounts", True),
    ]
    
    for endpoint, needs_auth in endpoints:
        try:
            start_time = time.time()
            if needs_auth:
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
            else:
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            elapsed = (time.time() - start_time) * 1000
            
            results[endpoint] = {
                "status_code": response.status_code,
                "response_time_ms": elapsed,
                "success": response.status_code < 400
            }
            
            status_icon = "✓" if response.status_code < 400 else "✗"
            print(f"{status_icon} {endpoint}: {elapsed:.2f}ms ({response.status_code})")
        except Exception as e:
            results[endpoint] = {"error": str(e)}
            print(f"✗ {endpoint}: 异常 - {e}")
    
    return results


def main():
    """主测试函数"""
    print("=" * 60)
    print("功能测试脚本")
    print("=" * 60)
    
    # 登录获取token
    print("\n正在登录...")
    token = login()
    if not token:
        print("❌ 无法获取认证token，部分测试将跳过")
        token = "dummy_token"
    
    all_results = {}
    
    # 测试健康检查
    all_results["health_check"] = test_health_check()
    
    # 测试性能监控
    if token:
        all_results["performance"] = test_performance_api(token)
        all_results["alert_management"] = test_alert_management(token)
        all_results["api_response_times"] = test_api_response_times(token)
    
    # 输出总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    # 保存结果到文件
    with open("/tmp/test_results.json", "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n测试结果已保存到 /tmp/test_results.json")
    
    # 统计成功率
    total_tests = 0
    passed_tests = 0
    
    for category, tests in all_results.items():
        for test_name, result in tests.items():
            total_tests += 1
            if "error" not in result and result.get("status_code", 0) < 400:
                passed_tests += 1
    
    print(f"\n总计: {passed_tests}/{total_tests} 测试通过")
    
    return 0 if passed_tests == total_tests else 1


if __name__ == "__main__":
    sys.exit(main())

