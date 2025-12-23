"""
强制创建站点表（绕过迁移问题）
直接使用 SQL 创建表
"""
import sqlite3
import sys
import os

def create_tables_with_sql():
    """使用 SQL 直接创建表"""
    db_file = os.path.join(os.path.dirname(__file__), '..', 'admin.db')
    db_file = os.path.abspath(db_file)
    
    if not os.path.exists(db_file):
        print(f"❌ 数据库文件不存在: {db_file}")
        return False
    
    print(f"📁 数据库文件: {db_file}")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # 检查表是否已存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sites'")
        if cursor.fetchone():
            print("✅ 表 'sites' 已存在")
        else:
            print("📝 创建表 'sites'...")
            cursor.execute("""
                CREATE TABLE sites (
                    id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    url VARCHAR(255) NOT NULL,
                    site_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20),
                    config JSON,
                    created_at DATETIME,
                    updated_at DATETIME,
                    PRIMARY KEY (id)
                )
            """)
            cursor.execute("CREATE INDEX ix_sites_id ON sites (id)")
            cursor.execute("CREATE INDEX ix_sites_site_type ON sites (site_type)")
            print("✅ 表 'sites' 创建成功")
        
        # 创建 site_visits 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='site_visits'")
        if cursor.fetchone():
            print("✅ 表 'site_visits' 已存在")
        else:
            print("📝 创建表 'site_visits'...")
            cursor.execute("""
                CREATE TABLE site_visits (
                    id INTEGER NOT NULL,
                    site_id INTEGER NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    referer VARCHAR(255),
                    page_path VARCHAR(255),
                    session_id VARCHAR(100),
                    visit_duration INTEGER,
                    created_at DATETIME,
                    PRIMARY KEY (id),
                    FOREIGN KEY(site_id) REFERENCES sites (id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX ix_site_visits_id ON site_visits (id)")
            cursor.execute("CREATE INDEX ix_site_visits_site_id ON site_visits (site_id)")
            cursor.execute("CREATE INDEX ix_site_visits_session_id ON site_visits (session_id)")
            cursor.execute("CREATE INDEX ix_site_visits_site_id_created_at ON site_visits (site_id, created_at)")
            print("✅ 表 'site_visits' 创建成功")
        
        # 创建 ai_conversations 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_conversations'")
        if cursor.fetchone():
            print("✅ 表 'ai_conversations' 已存在")
        else:
            print("📝 创建表 'ai_conversations'...")
            cursor.execute("""
                CREATE TABLE ai_conversations (
                    id INTEGER NOT NULL,
                    site_id INTEGER NOT NULL,
                    session_id VARCHAR(100),
                    user_message TEXT,
                    ai_response TEXT,
                    ai_provider VARCHAR(20),
                    response_time INTEGER,
                    tokens_used INTEGER,
                    created_at DATETIME,
                    PRIMARY KEY (id),
                    FOREIGN KEY(site_id) REFERENCES sites (id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX ix_ai_conversations_id ON ai_conversations (id)")
            cursor.execute("CREATE INDEX ix_ai_conversations_site_id ON ai_conversations (site_id)")
            cursor.execute("CREATE INDEX ix_ai_conversations_session_id ON ai_conversations (session_id)")
            cursor.execute("CREATE INDEX ix_ai_conversations_site_id_created_at ON ai_conversations (site_id, created_at)")
            print("✅ 表 'ai_conversations' 创建成功")
        
        # 创建 contact_forms 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contact_forms'")
        if cursor.fetchone():
            print("✅ 表 'contact_forms' 已存在")
        else:
            print("📝 创建表 'contact_forms'...")
            cursor.execute("""
                CREATE TABLE contact_forms (
                    id INTEGER NOT NULL,
                    site_id INTEGER NOT NULL,
                    contact_type VARCHAR(20),
                    contact_value VARCHAR(255),
                    message TEXT,
                    status VARCHAR(20),
                    notes TEXT,
                    created_at DATETIME,
                    updated_at DATETIME,
                    PRIMARY KEY (id),
                    FOREIGN KEY(site_id) REFERENCES sites (id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX ix_contact_forms_id ON contact_forms (id)")
            cursor.execute("CREATE INDEX ix_contact_forms_site_id ON contact_forms (site_id)")
            cursor.execute("CREATE INDEX ix_contact_forms_status ON contact_forms (status)")
            cursor.execute("CREATE INDEX ix_contact_forms_site_id_created_at ON contact_forms (site_id, created_at)")
            print("✅ 表 'contact_forms' 创建成功")
        
        # 创建 site_analytics 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='site_analytics'")
        if cursor.fetchone():
            print("✅ 表 'site_analytics' 已存在")
        else:
            print("📝 创建表 'site_analytics'...")
            cursor.execute("""
                CREATE TABLE site_analytics (
                    id INTEGER NOT NULL,
                    site_id INTEGER NOT NULL,
                    date DATETIME NOT NULL,
                    pv INTEGER,
                    uv INTEGER,
                    conversations INTEGER,
                    contacts INTEGER,
                    avg_session_duration INTEGER,
                    bounce_rate INTEGER,
                    created_at DATETIME,
                    updated_at DATETIME,
                    PRIMARY KEY (id),
                    FOREIGN KEY(site_id) REFERENCES sites (id) ON DELETE CASCADE,
                    UNIQUE(site_id, date)
                )
            """)
            cursor.execute("CREATE INDEX ix_site_analytics_id ON site_analytics (id)")
            cursor.execute("CREATE INDEX ix_site_analytics_site_id ON site_analytics (site_id)")
            cursor.execute("CREATE INDEX ix_site_analytics_date ON site_analytics (date)")
            print("✅ 表 'site_analytics' 创建成功")
        
        conn.commit()
        print("\n✅ 所有表创建完成！")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 创建表失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if create_tables_with_sql():
        print("\n💡 下一步：运行 python scripts/init_sites.py 初始化站点数据")
        sys.exit(0)
    else:
        sys.exit(1)

