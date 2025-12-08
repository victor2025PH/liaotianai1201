#!/usr/bin/env python3
"""测试Telegram注册API（需要认证token）"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_server_list():
    """测试服务器列表API"""
    print("=" * 60)
    print("测试: 获取服务器列表")
    print("=" * 60)
    
    url = f"{BASE_URL}/group-ai/servers"
    
    try:
        response = requests.get(url, timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] 服务器列表获取成功")
            print(f"服务器数量: {len(data)}")
            for server in data[:3]:  # 只显示前3个
                print(f"  - {server.get('node_id')}: {server.get('host')}")
            return True
        elif response.status_code == 401:
            print("[AUTH] 需要认证token")
            return False
        else:
            print(f"[ERROR] 错误: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[FAIL] 请求失败: {e}")
        return False

def test_registration_start():
    """测试开始注册API"""
    print("\n" + "=" * 60)
    print("测试: 开始注册（需要认证）")
    print("=" * 60)
    
    url = f"{BASE_URL}/telegram-registration/start"
    data = {
        "phone": "+1234567890",
        "country_code": "+1",
        "node_id": "worker-01"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("[OK] 注册启动成功（模拟）")
            print(f"Registration ID: {result.get('registration_id')}")
            return True
        elif response.status_code == 401:
            print("[AUTH] 需要认证token（正常）")
            print("提示: 在Swagger UI中设置token后可以测试")
            return True  # 401是预期的
        elif response.status_code == 400:
            error = response.json()
            print(f"[VALIDATION] 验证错误: {error.get('detail')}")
            return True  # 验证错误说明端点存在
        else:
            print(f"[ERROR] 错误: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[FAIL] 请求失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("Telegram注册API测试")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}\n")
    
    results = []
    
    # 测试服务器列表（可能不需要认证）
    results.append(test_server_list())
    
    # 测试注册API（需要认证）
    results.append(test_registration_start())
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    total = len(results)
    passed = sum(results)
    
    print(f"总测试项: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    
    if passed == total:
        print("\n[OK] 所有测试通过！")
        print("\n下一步:")
        print("1. 访问 http://localhost:3000")
        print("2. 登录系统获取token")
        print("3. 进入'账户中心' → 'Telegram注册'")
        print("4. 进行完整功能测试")
        return 0
    else:
        print("\n[WARN] 部分测试失败")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n测试已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

