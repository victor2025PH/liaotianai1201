#!/usr/bin/env python3
# ============================================================
# Activate All Accounts (Python Script)
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Batch activate all accounts in the database using Python
#
# One-click execution: python3 scripts/server/activate_all_accounts.py
# ============================================================

import sys
import os
from pathlib import Path

# 添加项目路径
PROJECT_DIR = Path("/home/ubuntu/telegram-ai-system")
BACKEND_DIR = PROJECT_DIR / "admin-backend"
sys.path.insert(0, str(BACKEND_DIR))

try:
    from sqlalchemy import create_engine, update
    from sqlalchemy.orm import sessionmaker
    from app.models.group_ai import GroupAIAccount
    from app.core.database import Base, get_db
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保在正确的环境中运行此脚本")
    sys.exit(1)

def activate_all_accounts():
    """批量激活所有账号"""
    print("============================================================")
    print("🔧 批量激活所有账号")
    print("============================================================")
    print("")
    
    # 获取数据库路径
    db_path = BACKEND_DIR / "data" / "app.db"
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        sys.exit(1)
    
    # 创建数据库连接
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 统计账号数量
        total_accounts = db.query(GroupAIAccount).count()
        active_accounts = db.query(GroupAIAccount).filter(GroupAIAccount.active == True).count()
        inactive_accounts = db.query(GroupAIAccount).filter(GroupAIAccount.active == False).count()
        
        print("[1/3] 检查数据库...")
        print("----------------------------------------")
        print(f"总账号数: {total_accounts}")
        print(f"已激活: {active_accounts}")
        print(f"未激活: {inactive_accounts}")
        print("")
        
        if inactive_accounts == 0:
            print("✅ 所有账号都已激活，无需操作")
            return
        
        # 显示未激活的账号列表
        print("[2/3] 未激活的账号列表...")
        print("----------------------------------------")
        inactive_list = db.query(GroupAIAccount).filter(GroupAIAccount.active == False).all()
        for acc in inactive_list:
            print(f"  - {acc.account_id} (电话: {acc.phone_number or 'N/A'}, 用户名: {acc.username or 'N/A'}, 服务器: {acc.server_id or 'N/A'})")
        print("")
        
        # 确认操作
        print("[3/3] 激活所有账号...")
        print("----------------------------------------")
        print(f"⚠️  即将激活 {inactive_accounts} 个账号")
        confirm = input("确认继续？(y/N): ").strip().lower()
        if confirm != 'y':
            print("操作已取消")
            return
        
        # 激活所有账号
        updated = db.query(GroupAIAccount).filter(GroupAIAccount.active == False).update(
            {"active": True},
            synchronize_session=False
        )
        db.commit()
        
        # 验证结果
        new_active_count = db.query(GroupAIAccount).filter(GroupAIAccount.active == True).count()
        
        print("")
        print("✅ 激活完成！")
        print(f"   - 已激活账号数: {updated}")
        print(f"   - 当前活跃账号总数: {new_active_count}")
        print("")
        print("============================================================")
        print("✅ 批量激活完成")
        print("============================================================")
        print("")
        print("现在可以尝试使用"一键启动所有账号"功能了")
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    activate_all_accounts()

