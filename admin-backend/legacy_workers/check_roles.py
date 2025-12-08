#!/usr/bin/env python
"""檢查角色的詳細信息和使用情況"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from app.db import SessionLocal
from app.models.role import Role
from app.models.user import User

def main():
    db = SessionLocal()
    try:
        roles = db.query(Role).order_by(Role.id).all()
        
        print("=" * 60)
        print("角色列表和使用情況")
        print("=" * 60)
        
        for role in roles:
            print(f"\n[角色 ID: {role.id}]")
            print(f"  名稱: {role.name}")
            print(f"  描述: {role.description or '(無)'}")
            
            # 檢查用戶使用情況
            users_with_role = db.query(User).join(User.roles).filter(Role.id == role.id).all()
            if users_with_role:
                print(f"  使用此角色的用戶 ({len(users_with_role)} 個):")
                for user in users_with_role:
                    print(f"    - {user.email} (ID: {user.id}, 超級管理員: {user.is_superuser})")
            else:
                print(f"  使用此角色的用戶: 無")
            
            # 檢查權限分配
            permissions = role.permissions
            if permissions:
                print(f"  分配的權限 ({len(permissions)} 個):")
                for perm in permissions:
                    print(f"    - {perm.code}: {perm.description}")
            else:
                print(f"  分配的權限: 無")
            
            # 判斷是否可以安全刪除
            can_delete = True
            reasons = []
            
            if role.name == "admin":
                can_delete = False
                reasons.append("這是系統預設的管理員角色，由啟動腳本自動創建")
            
            if users_with_role:
                can_delete = False
                reasons.append(f"有 {len(users_with_role)} 個用戶正在使用此角色")
            
            if can_delete:
                print(f"  [OK] 可以安全刪除")
            else:
                print(f"  [WARNING] 不建議刪除:")
                for reason in reasons:
                    print(f"     - {reason}")
        
        print("\n" + "=" * 60)
        print("總結:")
        print("- 'admin' 角色是系統預設角色，會被自動分配給默認管理員用戶")
        print("- 其他角色如果沒有用戶使用，可以安全刪除")
        print("- 如果角色有用戶在使用，刪除前請先移除用戶的角色分配")
        print("=" * 60)
        
    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()

