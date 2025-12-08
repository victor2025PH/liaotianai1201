#!/usr/bin/env python3
"""测试Telegram注册API（带认证）"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def get_auth_token():
    """获取认证token"""
    print("=" * 60)
    print("获取认证Token")
    print("=" * 60)
    
    # 注意：这里需要实际的登录凭据
    # 在实际测试中，应该通过登录接口获取token
    print("[INFO] 需要通过登录接口获取token")
    print("提示: 使用以下方式获取token:")
    print("1. 访问 http://localhost:8000/docs")
    print("2. 使用 /api/v1/auth/login 接口")
    print("3. 复制返回的 access_token")
    print("4. 在Swagger UI中点击'Authorize'输入token")
    
    return None

def test_server_list_with_auth(token=None):
    """测试服务器列表API（带认证）"""
    print("\n" + "=" * 60)
    print("测试: 获取服务器列表（带认证）")
    print("=" * 60)
    
    url = f"{BASE_URL}/group-ai/servers"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
        print(f"使用Token: {token[:20]}...")
    else:
        print("[INFO] 未提供token，将测试无认证访问")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] 服务器列表获取成功")
            print(f"服务器数量: {len(data)}")
            for server in data:
                print(f"  - {server.get('node_id')}: {server.get('host')} ({server.get('status')})")
            return True, data
        elif response.status_code == 401:
            print("[AUTH] 需要认证token")
            print("提示: 请提供有效的JWT token")
            return False, None
        else:
            print(f"[ERROR] 错误: {response.text[:200]}")
            return False, None
    except Exception as e:
        print(f"[FAIL] 请求失败: {e}")
        return False, None

def test_registration_start_with_auth(token, server_node_id="worker-01"):
    """测试开始注册API（带认证）"""
    print("\n" + "=" * 60)
    print("测试: 开始注册（带认证）")
    print("=" * 60)
    
    url = f"{BASE_URL}/telegram-registration/start"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "phone": "+1234567890",  # 使用测试手机号
        "country_code": "+1",
        "node_id": server_node_id
    }
    
    print(f"请求数据: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("[OK] 注册启动成功")
            print(f"Registration ID: {result.get('registration_id')}")
            print(f"Status: {result.get('status')}")
            print(f"Risk Score: {result.get('risk_score')}")
            if result.get('phone_code_hash'):
                print(f"Phone Code Hash: {result.get('phone_code_hash')[:20]}...")
            return True, result
        elif response.status_code == 400:
            error = response.json()
            print(f"[VALIDATION] 验证错误: {error.get('detail')}")
            return False, error
        elif response.status_code == 401:
            print("[AUTH] 认证失败，token无效或过期")
            return False, None
        else:
            print(f"[ERROR] 错误: {response.text[:200]}")
            return False, None
    except Exception as e:
        print(f"[FAIL] 请求失败: {e}")
        return False, None

def main():
    """主测试函数"""
    print("=" * 60)
    print("Telegram注册API测试（带认证）")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}\n")
    
    # 获取token（需要用户提供）
    token = get_auth_token()
    
    if not token:
        print("\n" + "=" * 60)
        print("测试说明")
        print("=" * 60)
        print("要测试需要认证的API，请：")
        print("1. 访问 http://localhost:8000/docs")
        print("2. 使用 /api/v1/auth/login 接口登录")
        print("3. 复制返回的 access_token")
        print("4. 在脚本中设置 TOKEN 变量，或使用Swagger UI测试")
        print("\n或者，直接访问前端页面进行测试：")
        print("   http://localhost:3000/accounts")
        return 0
    
    # 测试服务器列表
    success, servers = test_server_list_with_auth(token)
    
    if success and servers:
        # 使用第一个服务器进行注册测试
        server_node_id = servers[0].get('node_id') if servers else "worker-01"
        test_registration_start_with_auth(token, server_node_id)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

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

