#!/usr/bin/env python3
"""
数据库查询性能检查脚本
分析慢查询、检查索引使用情况
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "admin-backend"))

from sqlalchemy import text, inspect
from app.db import SessionLocal, engine
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_indexes():
    """检查数据库索引"""
    print("\n=== 检查数据库索引 ===")
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    index_info = {}
    
    for table_name in tables:
        if 'group_ai' in table_name or table_name in ['users', 'notifications', 'audit_logs']:
            indexes = inspector.get_indexes(table_name)
            index_info[table_name] = indexes
            
            print(f"\n表: {table_name}")
            if indexes:
                for idx in indexes:
                    print(f"  ✓ {idx['name']}: {idx['column_names']}")
            else:
                print(f"  ⚠ 无索引")
    
    return index_info


def analyze_slow_queries():
    """分析慢查询（模拟常见查询）"""
    print("\n=== 分析常见查询性能 ===")
    
    db = SessionLocal()
    results = {}
    
    try:
        # 测试1: 查询账号列表（带过滤）
        start = time.time()
        result = db.execute(text("""
            SELECT COUNT(*) FROM group_ai_accounts 
            WHERE active = true
        """))
        elapsed = (time.time() - start) * 1000
        results["account_count"] = {"time_ms": elapsed, "rows": result.scalar()}
        print(f"✓ 账号计数查询: {elapsed:.2f}ms")
        
        # 测试2: 查询脚本列表（带排序）
        start = time.time()
        result = db.execute(text("""
            SELECT id, name, status, created_at 
            FROM group_ai_scripts 
            WHERE status = 'published'
            ORDER BY created_at DESC 
            LIMIT 10
        """))
        elapsed = (time.time() - start) * 1000
        rows = result.fetchall()
        results["script_list"] = {"time_ms": elapsed, "rows": len(rows)}
        print(f"✓ 脚本列表查询: {elapsed:.2f}ms ({len(rows)} 行)")
        
        # 测试3: 查询对话历史（带时间范围）
        # 根据数据库类型使用不同的SQL语法
        from sqlalchemy import inspect as sql_inspect
        inspector = sql_inspect(engine)
        is_postgresql = 'postgresql' in str(engine.url)
        
        start = time.time()
        if is_postgresql:
            result = db.execute(text("""
                SELECT COUNT(*) FROM group_ai_dialogue_history 
                WHERE timestamp > NOW() - INTERVAL '24 hours'
            """))
        else:
            # SQLite语法
            result = db.execute(text("""
                SELECT COUNT(*) FROM group_ai_dialogue_history 
                WHERE timestamp > datetime('now', '-24 hours')
            """))
        elapsed = (time.time() - start) * 1000
        results["dialogue_recent"] = {"time_ms": elapsed, "rows": result.scalar()}
        print(f"✓ 最近对话查询: {elapsed:.2f}ms")
        
        # 测试4: 关联查询（账号+脚本）
        start = time.time()
        result = db.execute(text("""
            SELECT a.id, a.phone_number, s.name as script_name
            FROM group_ai_accounts a
            LEFT JOIN group_ai_scripts s ON a.script_id = s.id
            WHERE a.active = true
            LIMIT 20
        """))
        elapsed = (time.time() - start) * 1000
        rows = result.fetchall()
        results["account_script_join"] = {"time_ms": elapsed, "rows": len(rows)}
        print(f"✓ 账号-脚本关联查询: {elapsed:.2f}ms ({len(rows)} 行)")
        
    except Exception as e:
        logger.error(f"查询分析失败: {e}", exc_info=True)
        print(f"✗ 查询分析失败: {e}")
    finally:
        db.close()
    
    return results


def check_table_sizes():
    """检查表大小"""
    print("\n=== 检查表大小 ===")
    
    db = SessionLocal()
    
    try:
        # PostgreSQL
        if 'postgresql' in str(engine.url):
            result = db.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10
            """))
            
            print("\n表大小（前10）:")
            for row in result:
                print(f"  {row.tablename}: {row.size}")
        else:
            # SQLite
            result = db.execute(text("""
                SELECT name, 
                       (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as row_count
                FROM sqlite_master m
                WHERE type='table'
                ORDER BY name
            """))
            
            print("\n表列表:")
            for row in result:
                print(f"  {row.name}")
                
    except Exception as e:
        logger.error(f"检查表大小失败: {e}")
        print(f"✗ 检查表大小失败: {e}")
    finally:
        db.close()


def main():
    """主函数"""
    print("=" * 60)
    print("数据库性能检查")
    print("=" * 60)
    
    try:
        # 检查索引
        index_info = check_indexes()
        
        # 分析查询性能
        query_results = analyze_slow_queries()
        
        # 检查表大小
        check_table_sizes()
        
        # 总结
        print("\n" + "=" * 60)
        print("性能检查总结")
        print("=" * 60)
        
        slow_queries = [name for name, data in query_results.items() if data.get("time_ms", 0) > 100]
        if slow_queries:
            print(f"\n⚠ 发现慢查询 (>100ms): {', '.join(slow_queries)}")
        else:
            print("\n✓ 所有查询性能良好")
        
        return 0
        
    except Exception as e:
        logger.error(f"检查失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

