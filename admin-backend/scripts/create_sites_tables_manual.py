"""
手动创建站点表（如果迁移有问题）
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect
from app.db import Base
from app.models.sites import Site, SiteVisit, AIConversation, ContactForm, SiteAnalytics
from app.core.config import settings

def create_tables_manually():
    """手动创建站点表"""
    # 创建数据库引擎
    db_url = settings.database_url
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    
    inspector = inspect(engine)
    
    print("🔍 检查表是否存在...")
    
    tables_to_create = {
        'sites': Site,
        'site_visits': SiteVisit,
        'ai_conversations': AIConversation,
        'contact_forms': ContactForm,
        'site_analytics': SiteAnalytics,
    }
    
    created_tables = []
    existing_tables = []
    
    for table_name, model in tables_to_create.items():
        if inspector.has_table(table_name):
            print(f"  ✅ 表 '{table_name}' 已存在")
            existing_tables.append(table_name)
        else:
            print(f"  ❌ 表 '{table_name}' 不存在，将创建...")
            try:
                # 只创建这个表
                model.__table__.create(engine, checkfirst=True)
                print(f"  ✅ 表 '{table_name}' 创建成功")
                created_tables.append(table_name)
            except Exception as e:
                print(f"  ❌ 表 '{table_name}' 创建失败: {e}")
    
    print(f"\n📊 总结:")
    print(f"  - 已存在: {len(existing_tables)} 个表")
    print(f"  - 新创建: {len(created_tables)} 个表")
    
    if created_tables:
        print(f"\n✅ 成功创建以下表: {', '.join(created_tables)}")
    elif existing_tables:
        print(f"\n✅ 所有表都已存在")
    else:
        print(f"\n❌ 没有创建任何表")
        return False
    
    return True

if __name__ == "__main__":
    try:
        if create_tables_manually():
            print("\n✅ 表创建完成！")
            print("💡 现在可以运行: python scripts/init_sites.py")
        else:
            print("\n❌ 表创建失败")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

