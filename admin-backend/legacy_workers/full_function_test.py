#!/usr/bin/env python
"""完整功能测试"""
import sys
from pathlib import Path
import requests

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

print("=" * 60)
print("完整功能测试")
print("=" * 60)

# 1. 登录
print("\n[1] 登录测试...")
form_data = "username=admin@example.com&password=changeme123"
login_resp = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data=form_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
if login_resp.status_code != 200:
    print(f"   [FAIL] 登录失败: {login_resp.status_code}")
    sys.exit(1)

token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"   [OK] 登录成功")

# 2. 测试所有API
print("\n[2] API功能测试...")
apis = [
    ("当前用户信息", "GET", "http://localhost:8000/api/v1/users/me", None),
    ("剧本列表", "GET", "http://localhost:8000/api/v1/group-ai/scripts", None),
    ("账号列表", "GET", "http://localhost:8000/api/v1/group-ai/accounts", None),
    ("服务器列表", "GET", "http://localhost:8000/api/v1/group-ai/servers", None),
    ("用户列表", "GET", "http://localhost:8000/api/v1/users", None),
]

success_count = 0
fail_count = 0

for name, method, url, data in apis:
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=5)
        else:
            resp = requests.post(url, headers=headers, json=data, timeout=5)
        
        if resp.status_code == 200:
            result = resp.json()
            if "email" in result:
                value = f"用户: {result['email']}"
            elif "total" in result:
                value = f"总数: {result['total']}"
            elif isinstance(result, list):
                value = f"数量: {len(result)}"
            else:
                value = "成功"
            print(f"   [OK] {name}: {value}")
            success_count += 1
        else:
            print(f"   [FAIL] {name}: HTTP {resp.status_code}")
            if resp.status_code == 401:
                print(f"      响应: {resp.text[:100]}")
            fail_count += 1
    except Exception as e:
        print(f"   [FAIL] {name}: {e}")
        fail_count += 1

# 3. 总结
print("\n" + "=" * 60)
print("测试结果汇总")
print("=" * 60)
print(f"成功: {success_count}")
print(f"失败: {fail_count}")
print(f"总计: {success_count + fail_count}")

if success_count == len(apis):
    print("\n[SUCCESS] 所有API测试通过！系统已完全修复！")
    print("\n下一步：")
    print("  1. 在浏览器中访问 http://localhost:3000/login")
    print("  2. 使用 admin@example.com / changeme123 登录")
    print("  3. 测试前端各个功能模块")
else:
    print(f"\n[WARNING] {success_count}/{len(apis)} 个API测试通过")

print("=" * 60)

