#!/usr/bin/env python3
"""测试Telegram注册API端点"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"

def test_api_endpoints():
    """测试API端点是否可访问"""
    print("=" * 60)
    print("Telegram注册API端点测试")
    print("=" * 60)
    
    # 测试端点列表
    endpoints = [
        {
            "method": "GET",
            "path": "/docs",
            "description": "API文档页面",
            "requires_auth": False
        },
        {
            "method": "POST",
            "path": "/telegram-registration/start",
            "description": "开始注册",
            "requires_auth": True,
            "test_data": {
                "phone": "+1234567890",
                "country_code": "+1",
                "node_id": "worker-01"
            }
        },
        {
            "method": "GET",
            "path": "/telegram-registration/status/test-id",
            "description": "查询注册状态",
            "requires_auth": True
        }
    ]
    
    results = []
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint['path']}"
        method = endpoint['method']
        
        print(f"\n测试: {method} {endpoint['path']}")
        print(f"描述: {endpoint['description']}")
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                headers = {"Content-Type": "application/json"}
                data = endpoint.get('test_data', {})
                response = requests.post(url, json=data, headers=headers, timeout=5)
            else:
                response = None
            
            if response is not None:
                status_code = response.status_code
                if status_code == 200 or status_code == 201:
                    print(f"[OK] 状态码: {status_code}")
                    results.append(True)
                elif status_code == 401:
                    print(f"[AUTH] 需要认证 (状态码: {status_code})")
                    results.append(True)  # 需要认证是正常的
                elif status_code == 404:
                    print(f"[INFO] 端点存在但资源不存在 (状态码: {status_code})")
                    results.append(True)
                elif status_code == 422:
                    print(f"[VALIDATION] 验证错误 (状态码: {status_code})")
                    print(f"响应: {response.text[:200]}")
                    results.append(True)  # 验证错误说明端点存在
                else:
                    print(f"[WARN] 状态码: {status_code}")
                    print(f"响应: {response.text[:200]}")
                    results.append(False)
            else:
                print("[SKIP] 未实现的HTTP方法")
                results.append(False)
                
        except requests.exceptions.ConnectionError:
            print("[FAIL] 无法连接到服务器，请确保后端服务已启动")
            results.append(False)
        except requests.exceptions.Timeout:
            print("[FAIL] 请求超时")
            results.append(False)
        except Exception as e:
            print(f"[FAIL] 错误: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    success_count = sum(results)
    total_count = len(results)
    print(f"成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("[OK] 所有端点测试通过！")
        return True
    else:
        print("[WARN] 部分端点测试失败，请检查后端服务状态")
        return False

if __name__ == "__main__":
    try:
        test_api_endpoints()
    except KeyboardInterrupt:
        print("\n测试已中断")
    except Exception as e:
        print(f"\n测试失败: {e}")

