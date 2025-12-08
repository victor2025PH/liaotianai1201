#!/usr/bin/env python
"""测试认证流程和权限验证"""
import sys
from pathlib import Path
import requests
from jose import jwt

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from app.db import SessionLocal
from app.crud.user import get_user_by_email
from app.crud.permission import user_has_permission
from app.core.config import get_settings

settings = get_settings()

# 1. 测试登录
print("[1] 测试登录...")
form_data = "username=admin@example.com&password=changeme123"
login_resp = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data=form_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
if login_resp.status_code == 200:
    token = login_resp.json()["access_token"]
    print(f"   [OK] 登录成功")
    print(f"   Token: {token[:30]}...")
else:
    print(f"   [FAIL] 登录失败: {login_resp.status_code}")
    print(f"   {login_resp.text}")
    sys.exit(1)

# 2. 解码token
print("\n[2] 解码token...")
payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
print(f"   Subject (email): {payload.get('sub')}")

# 3. 从数据库加载用户
print("\n[3] 从数据库加载用户...")
db = SessionLocal()
try:
    user = get_user_by_email(db, email=payload.get("sub"))
    if user:
        print(f"   [OK] 用户存在: {user.email}")
        print(f"   激活: {user.is_active}")
        print(f"   超级用户: {user.is_superuser}")
        print(f"   角色数量: {len(user.roles)}")
        for role in user.roles:
            print(f"     角色: {role.name}, 权限数量: {len(role.permissions)}")
        
        # 4. 测试权限检查
        print("\n[4] 测试权限检查...")
        test_perms = ["script:view", "account:view", "server:view"]
        for perm in test_perms:
            has_perm = user_has_permission(db, user=user, permission_code=perm)
            status = "[OK]" if has_perm else "[FAIL]"
            print(f"   {status} {perm}: {has_perm}")
    else:
        print(f"   [FAIL] 用户不存在")
finally:
    db.close()

# 5. 测试API调用
print("\n[5] 测试API调用...")
headers = {"Authorization": f"Bearer {token}"}
apis = [
    ("剧本列表", "http://localhost:8000/api/v1/group-ai/scripts"),
    ("账号列表", "http://localhost:8000/api/v1/group-ai/accounts"),
    ("服务器列表", "http://localhost:8000/api/v1/group-ai/servers"),
]

for name, url in apis:
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            print(f"   [OK] {name}: 成功")
        else:
            print(f"   [FAIL] {name}: {resp.status_code}")
            print(f"      {resp.text[:200]}")
    except Exception as e:
        print(f"   [FAIL] {name}: {e}")

print("\n[完成] 测试结束")

