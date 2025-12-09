#!/usr/bin/env python3
"""
数据库查询优化脚本
执行数据库优化操作，包括添加索引、分析查询计划等
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text, inspect, Index
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.db import SessionLocal, engine, Base
from app.models import group_ai, user, role, permission, notification, audit_log
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_sqlite(engine_obj) -> bool:
    """检查是否为SQLite数据库"""
    return engine_obj.name == 'sqlite'


def add_missing_indexes(db, is_sqlite_db: bool):
    """添加缺失的索引"""
    logger.info("检查并添加缺失的索引...")
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    indexes_to_add = []
    
    # 检查 group_ai_accounts 表的索引
    if 'group_ai_accounts' in tables:
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('group_ai_accounts')]
        
        if 'idx_account_script_active' not in existing_indexes:
            indexes_to_add.append({
                "table": "group_ai_accounts",
                "name": "idx_account_script_active",
                "columns": ["script_id", "active"],
                "sqlite_sql": "CREATE INDEX IF NOT EXISTS idx_account_script_active ON group_ai_accounts(script_id, active);",
                "postgresql_sql": "CREATE INDEX IF NOT EXISTS idx_account_script_active ON group_ai_accounts(script_id, active);"
            })
        
        if 'idx_account_server_active' not in existing_indexes:
            indexes_to_add.append({
                "table": "group_ai_accounts",
                "name": "idx_account_server_active",
                "columns": ["server_id", "active"],
                "sqlite_sql": "CREATE INDEX IF NOT EXISTS idx_account_server_active ON group_ai_accounts(server_id, active);",
                "postgresql_sql": "CREATE INDEX IF NOT EXISTS idx_account_server_active ON group_ai_accounts(server_id, active);"
            })
    
    # 检查 group_ai_scripts 表的索引
    if 'group_ai_scripts' in tables:
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('group_ai_scripts')]
        
        if 'idx_script_status_created' not in existing_indexes:
            indexes_to_add.append({
                "table": "group_ai_scripts",
                "name": "idx_script_status_created",
                "columns": ["status", "created_at"],
                "sqlite_sql": "CREATE INDEX IF NOT EXISTS idx_script_status_created ON group_ai_scripts(status, created_at);",
                "postgresql_sql": "CREATE INDEX IF NOT EXISTS idx_script_status_created ON group_ai_scripts(status, created_at);"
            })
    
    # 检查 group_ai_dialogue_history 表的索引
    if 'group_ai_dialogue_history' in tables:
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('group_ai_dialogue_history')]
        
        if 'idx_dialogue_account_group_time' not in existing_indexes:
            indexes_to_add.append({
                "table": "group_ai_dialogue_history",
                "name": "idx_dialogue_account_group_time",
                "columns": ["account_id", "group_id", "timestamp"],
                "sqlite_sql": "CREATE INDEX IF NOT EXISTS idx_dialogue_account_group_time ON group_ai_dialogue_history(account_id, group_id, timestamp);",
                "postgresql_sql": "CREATE INDEX IF NOT EXISTS idx_dialogue_account_group_time ON group_ai_dialogue_history(account_id, group_id, timestamp);"
            })
        
        if 'idx_dialogue_timestamp' not in existing_indexes:
            indexes_to_add.append({
                "table": "group_ai_dialogue_history",
                "name": "idx_dialogue_timestamp",
                "columns": ["timestamp"],
                "sqlite_sql": "CREATE INDEX IF NOT EXISTS idx_dialogue_timestamp ON group_ai_dialogue_history(timestamp);",
                "postgresql_sql": "CREATE INDEX IF NOT EXISTS idx_dialogue_timestamp ON group_ai_dialogue_history(timestamp);"
            })
    
    # 检查 group_ai_automation_tasks 表的索引
    if 'group_ai_automation_tasks' in tables:
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('group_ai_automation_tasks')]
        
        if 'idx_task_enabled_next_run' not in existing_indexes:
            indexes_to_add.append({
                "table": "group_ai_automation_tasks",
                "name": "idx_task_enabled_next_run",
                "columns": ["enabled", "next_run_at"],
                "sqlite_sql": "CREATE INDEX IF NOT EXISTS idx_task_enabled_next_run ON group_ai_automation_tasks(enabled, next_run_at);",
                "postgresql_sql": "CREATE INDEX IF NOT EXISTS idx_task_enabled_next_run ON group_ai_automation_tasks(enabled, next_run_at);"
            })
    
    # 执行添加索引
    if indexes_to_add:
        logger.info(f"发现 {len(indexes_to_add)} 个缺失的索引，开始添加...")
        for idx_info in indexes_to_add:
            try:
                if is_sqlite_db:
                    sql = idx_info["sqlite_sql"]
                else:
                    sql = idx_info["postgresql_sql"]
                
                db.execute(text(sql))
                db.commit()
                logger.info(f"✓ 已添加索引: {idx_info['name']} on {idx_info['table']}")
            except Exception as e:
                logger.error(f"✗ 添加索引 {idx_info['name']} 失败: {e}")
                db.rollback()
    else:
        logger.info("✓ 所有推荐的索引都已存在")


def analyze_query_plans(db, is_sqlite_db: bool):
    """分析查询计划"""
    logger.info("分析查询计划...")
    
    queries = [
        {
            "name": "账号列表查询",
            "sql": "SELECT * FROM group_ai_accounts WHERE active = 1 ORDER BY created_at DESC LIMIT 20"
        },
        {
            "name": "脚本列表查询",
            "sql": "SELECT * FROM group_ai_scripts WHERE status = 'published' ORDER BY created_at DESC LIMIT 20"
        }
    ]
    
    for query in queries:
        logger.info(f"\n查询: {query['name']}")
        try:
            if is_sqlite_db:
                # SQLite EXPLAIN QUERY PLAN
                plan = db.execute(text(f"EXPLAIN QUERY PLAN {query['sql']}")).fetchall()
                logger.info("查询计划:")
                for row in plan:
                    logger.info(f"  {row}")
            else:
                # PostgreSQL EXPLAIN
                plan = db.execute(text(f"EXPLAIN ANALYZE {query['sql']}")).fetchall()
                logger.info("查询计划:")
                for row in plan:
                    logger.info(f"  {row[0]}")
        except Exception as e:
            logger.warning(f"分析查询计划失败: {e}")


def optimize_vacuum(db, is_sqlite_db: bool):
    """执行数据库优化（VACUUM/ANALYZE）"""
    logger.info("执行数据库优化...")
    
    try:
        if is_sqlite_db:
            # SQLite VACUUM
            db.execute(text("VACUUM;"))
            db.execute(text("ANALYZE;"))
            db.commit()
            logger.info("✓ SQLite VACUUM 和 ANALYZE 完成")
        else:
            # PostgreSQL VACUUM ANALYZE
            db.execute(text("VACUUM ANALYZE;"))
            db.commit()
            logger.info("✓ PostgreSQL VACUUM ANALYZE 完成")
    except Exception as e:
        logger.error(f"✗ 数据库优化失败: {e}")
        db.rollback()


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("数据库查询优化")
    logger.info("=" * 60)
    
    settings = get_settings()
    is_sqlite_db = is_sqlite(engine)
    
    logger.info(f"数据库类型: {engine.name}")
    
    with SessionLocal() as db:
        # 1. 添加缺失的索引
        add_missing_indexes(db, is_sqlite_db)
        
        # 2. 分析查询计划
        analyze_query_plans(db, is_sqlite_db)
        
        # 3. 执行数据库优化
        optimize_vacuum(db, is_sqlite_db)
    
    logger.info("\n" + "=" * 60)
    logger.info("优化完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

