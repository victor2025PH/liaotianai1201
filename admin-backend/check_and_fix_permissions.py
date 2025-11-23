#!/usr/bin/env python
"""检查并修复管理员用户权限"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from app.db import SessionLocal
from app.crud.user import get_user_by_email
from app.crud.role import get_role_by_name
from app.crud.permission import get_permission_by_code
from app.models.role import Role
from app.models.permission import Permission
from app.core.config import get_settings
from app.core.permissions import PermissionCode

settings = get_settings()
db = SessionLocal()

try:
    admin = get_user_by_email(db, email=settings.admin_default_email)
    if not admin:
        print("[ERROR] 管理员用户不存在")
        sys.exit(1)
    
    print(f"[INFO] 管理员用户: {admin.email}")
    print(f"[INFO] 激活状态: {admin.is_active}")
    print(f"[INFO] 超级用户: {admin.is_superuser}")
    print(f"[INFO] 角色数量: {len(admin.roles)}")
    
    # 检查是否有admin角色
    admin_role = None
    for role in admin.roles:
        print(f"  角色: {role.name}, 权限数量: {len(role.permissions)}")
        if role.name == "admin":
            admin_role = role
    
    # 如果没有admin角色，创建并分配
    if not admin_role:
        print("[INFO] 创建admin角色...")
        admin_role = get_role_by_name(db, name="admin")
        if not admin_role:
            admin_role = Role(name="admin", description="系统管理员")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
        admin.roles.append(admin_role)
        db.commit()
        print("[OK] admin角色已创建并分配")
    
    # 确保admin角色有所有权限
    print("[INFO] 检查并添加所有权限...")
    all_permissions = [perm.value for perm in PermissionCode]
    added_count = 0
    
    for perm_code in all_permissions:
        permission = get_permission_by_code(db, code=perm_code)
        if not permission:
            permission = Permission(code=perm_code, description=f"权限: {perm_code}")
            db.add(permission)
            db.commit()
            db.refresh(permission)
            print(f"  创建权限: {perm_code}")
        
        if permission not in admin_role.permissions:
            admin_role.permissions.append(permission)
            added_count += 1
            print(f"  添加权限: {perm_code}")
    
    if added_count > 0:
        db.commit()
        print(f"[OK] 已添加 {added_count} 个权限")
    else:
        print("[OK] 所有权限已存在")
    
    # 最终验证
    db.refresh(admin_role)
    print(f"[INFO] 最终权限数量: {len(admin_role.permissions)}")
    
    print("\n[SUCCESS] 权限检查和修复完成！")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

