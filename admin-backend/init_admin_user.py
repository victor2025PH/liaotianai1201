"""
初始化默认管理员用户
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.db import SessionLocal, Base, engine
from app.models.user import User
from app.models.role import Role
from app.core.security import get_password_hash
from app.core.config import get_settings

def init_admin_user():
    """初始化默认管理员用户"""
    # 创建所有表
    print("[INFO] 创建数据库表...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        settings = get_settings()
        
        # 检查管理员用户是否存在
        admin = db.query(User).filter(User.email == settings.admin_default_email).first()
        if admin:
            print(f"[OK] 管理员用户已存在: {admin.email}")
            return
        
        # 创建管理员角色
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(name="admin", description="系统管理员")
            db.add(admin_role)
            db.commit()
            print("[OK] 管理员角色已创建")
        
        # 创建管理员用户
        admin = User(
            email=settings.admin_default_email,
            hashed_password=get_password_hash(settings.admin_default_password),
            full_name="超级管理员",
            is_active=True,
            is_superuser=True
        )
        admin.roles.append(admin_role)
        db.add(admin)
        db.commit()
        
        print(f"[OK] 默认管理员用户已创建")
        print(f"   邮箱: {settings.admin_default_email}")
        print(f"   密码: {settings.admin_default_password}")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] 创建管理员用户失败: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_admin_user()

