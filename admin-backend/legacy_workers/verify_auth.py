#!/usr/bin/env python
"""验证认证和权限"""
import sys
from pathlib import Path
import requests

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from app.db import SessionLocal
from app.crud.user import get_user_by_email
from app.crud.permission import user_has_permission
from app.core.config import get_settings

settings = get_settings()
db = SessionLocal()

print("[1] 检查用户和权限...")
admin = get_user_by_email(db, email=settings.admin_default_email)
if admin:
    print(f"   用户: {admin.email}")
    print(f"   超级用户: {admin.is_superuser}")
    print(f"   激活: {admin.is_active}")
    print(f"   角色数量: {len(admin.roles)}")
    for role in admin.roles:
        print(f"     角色: {role.name}, 权限数: {len(role.permissions)}")
    
    print("\n[2] 测试权限检查...")
    test_perms = ["script:view", "account:view", "server:view"]
    for perm in test_perms:
        has_perm = user_has_permission(db, user=admin, permission_code=perm)
        status = "[OK]" if has_perm else "[FAIL]"
        print(f"   {status} {perm}: {has_perm}")
else:
    print("   [FAIL] 用户不存在")

db.close()

print("\n[3] 测试API登录...")
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
    
    print("\n[4] 测试API调用...")
    headers = {"Authorization": f"Bearer {token}"}
    apis = [
        ("当前用户", "http://localhost:8000/api/v1/users/me"),
        ("剧本列表", "http://localhost:8000/api/v1/group-ai/scripts"),
        ("账号列表", "http://localhost:8000/api/v1/group-ai/accounts"),
    ]
    
    for name, url in apis:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            print(f"   [OK] {name}: 成功")
        else:
            print(f"   [FAIL] {name}: {resp.status_code}")
            if resp.status_code == 401:
                print(f"      响应: {resp.text[:200]}")
else:
    print(f"   [FAIL] 登录失败: {login_resp.status_code}")

print("\n[完成]")

