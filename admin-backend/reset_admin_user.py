#!/usr/bin/env python
"""重置或创建默认管理员用户"""
import sys
from pathlib import Path

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from app.db import SessionLocal, engine, Base
from app.crud.user import get_user_by_email, create_user
from app.crud.user import create_role, assign_role_to_user
from app.core.config import get_settings
from app.core.security import get_password_hash, verify_password

def main():
    settings = get_settings()
    
    # 确保所有表已创建
    print("正在创建数据库表...")
    try:
        # 导入所有模型以确保它们被注册
        from app.models import user, role, permission
        from app.models import group_ai
        Base.metadata.create_all(bind=engine)
        print("[OK] 数据库表已创建")
    except Exception as e:
        print(f"[WARNING] 创建数据库表时出现警告: {e}")
    
    db = SessionLocal()
    
    try:
        print(f"正在检查/创建管理员用户: {settings.admin_default_email}")
        
        # 检查用户是否存在
        admin = get_user_by_email(db, email=settings.admin_default_email)
        
        if admin:
            print(f"用户已存在: {admin.email}")
            print(f"  - 是否激活: {admin.is_active}")
            print(f"  - 是否超级用户: {admin.is_superuser}")
            
            # 验证密码
            if verify_password(settings.admin_default_password, admin.hashed_password):
                print(f"  - 密码验证: [OK] 正确")
            else:
                print(f"  - 密码验证: [ERROR] 不正确，正在更新密码...")
                admin.hashed_password = get_password_hash(settings.admin_default_password)
                admin.is_active = True
                admin.is_superuser = True
                db.commit()
                db.refresh(admin)
                print(f"  - 密码已更新")
        else:
            print(f"用户不存在，正在创建...")
            admin = create_user(
                db,
                email=settings.admin_default_email,
                password=settings.admin_default_password,
                full_name="超级管理员",
                is_superuser=True,
            )
            print(f"  - 用户已创建: {admin.email}")
        
        # 确保管理员角色存在并分配
        admin_role = create_role(db, name="admin", description="系统管理员")
        assign_role_to_user(db, user=admin, role=admin_role)
        print(f"  - 角色已分配: {admin_role.name}")
        
        # 最终验证
        admin = get_user_by_email(db, email=settings.admin_default_email)
        if verify_password(settings.admin_default_password, admin.hashed_password):
            print("\n[SUCCESS] 管理员账户准备就绪！")
            print(f"  邮箱: {settings.admin_default_email}")
            print(f"  密码: {settings.admin_default_password}")
        else:
            print("\n[ERROR] 密码验证失败，请检查配置")
            
    except Exception as e:
        print(f"\n[ERROR] 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()

