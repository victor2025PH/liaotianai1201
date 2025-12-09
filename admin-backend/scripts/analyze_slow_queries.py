#!/usr/bin/env python3
"""
数据库慢查询分析脚本
分析数据库查询性能，识别慢查询和优化机会
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.db import SessionLocal, engine
import time
import logging
from typing import Dict, List, Any
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_sqlite(engine_obj) -> bool:
    """检查是否为SQLite数据库"""
    return engine_obj.name == 'sqlite'


def analyze_query_performance(db, query: str, params: Dict = None) -> Dict[str, Any]:
    """分析单个查询的性能"""
    start_time = time.time()
    try:
        result = db.execute(text(query), params or {})
        rows = result.fetchall()
        elapsed_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        return {
            "query": query,
            "execution_time_ms": elapsed_time,
            "row_count": len(rows),
            "success": True
        }
    except Exception as e:
        elapsed_time = (time.time() - start_time) * 1000
        return {
            "query": query,
            "execution_time_ms": elapsed_time,
            "error": str(e),
            "success": False
        }


def check_indexes(db, is_sqlite_db: bool) -> Dict[str, List[Dict]]:
    """检查数据库索引"""
    logger.info("检查数据库索引...")
    indexes = {}
    
    if is_sqlite_db:
        # SQLite索引检查
        tables = db.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).scalars().all()
        
        for table_name in tables:
            if table_name.startswith('sqlite_'):
                continue
                
            table_indexes = []
            index_list = db.execute(text(f"PRAGMA index_list('{table_name}');")).fetchall()
            
            for index_row in index_list:
                index_name = index_row[1]
                index_info = db.execute(text(f"PRAGMA index_info('{index_name}');")).fetchall()
                columns = [col[2] for col in index_info]
                
                table_indexes.append({
                    "name": index_name,
                    "columns": columns,
                    "unique": index_row[2] == 1
                })
            
            indexes[table_name] = table_indexes
            logger.info(f"表 {table_name}: {len(table_indexes)} 个索引")
    else:
        # PostgreSQL索引检查
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        for table_name in tables:
            table_indexes = []
            for index in inspector.get_indexes(table_name):
                table_indexes.append({
                    "name": index['name'],
                    "columns": index['column_names'],
                    "unique": index['unique']
                })
            
            indexes[table_name] = table_indexes
            logger.info(f"表 {table_name}: {len(table_indexes)} 个索引")
    
    return indexes


def analyze_common_queries(db, is_sqlite_db: bool) -> List[Dict[str, Any]]:
    """分析常见查询的性能"""
    logger.info("分析常见查询性能...")
    results = []
    
    # 查询1: 账号列表（带过滤）
    query1 = """
        SELECT * FROM group_ai_accounts 
        WHERE active = 1 
        ORDER BY created_at DESC 
        LIMIT 20
    """
    result1 = analyze_query_performance(db, query1)
    result1["description"] = "账号列表查询（活跃账号，按创建时间排序）"
    results.append(result1)
    
    # 查询2: 脚本列表（带状态过滤）
    query2 = """
        SELECT * FROM group_ai_scripts 
        WHERE status = 'published' 
        ORDER BY created_at DESC 
        LIMIT 20
    """
    result2 = analyze_query_performance(db, query2)
    result2["description"] = "脚本列表查询（已发布，按创建时间排序）"
    results.append(result2)
    
    # 查询3: 对话历史（时间范围查询）
    if is_sqlite_db:
        query3 = """
            SELECT * FROM group_ai_dialogue_history 
            WHERE timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC 
            LIMIT 100
        """
    else:
        query3 = """
            SELECT * FROM group_ai_dialogue_history 
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            ORDER BY timestamp DESC 
            LIMIT 100
        """
    result3 = analyze_query_performance(db, query3)
    result3["description"] = "对话历史查询（最近24小时）"
    results.append(result3)
    
    # 查询4: 账号统计（聚合查询）
    query4 = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN active = 1 THEN 1 ELSE 0 END) as active_count,
            SUM(CASE WHEN active = 0 THEN 1 ELSE 0 END) as inactive_count
        FROM group_ai_accounts
    """
    result4 = analyze_query_performance(db, query4)
    result4["description"] = "账号统计查询（聚合）"
    results.append(result4)
    
    # 查询5: 自动化任务（带过滤和排序）
    query5 = """
        SELECT * FROM group_ai_automation_tasks 
        WHERE enabled = 1 
        ORDER BY next_run_at ASC 
        LIMIT 10
    """
    result5 = analyze_query_performance(db, query5)
    result5["description"] = "自动化任务查询（启用的任务，按下次运行时间排序）"
    results.append(result5)
    
    return results


def check_table_sizes(db, is_sqlite_db: bool) -> Dict[str, int]:
    """检查表大小（行数）"""
    logger.info("检查表大小...")
    sizes = {}
    
    if is_sqlite_db:
        tables = db.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).scalars().all()
    else:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
    
    for table_name in tables:
        if table_name.startswith('sqlite_'):
            continue
        
        try:
            count = db.execute(text(f"SELECT COUNT(*) FROM {table_name};")).scalar()
            sizes[table_name] = count
            logger.info(f"表 {table_name}: {count} 行")
        except Exception as e:
            logger.warning(f"获取表 {table_name} 行数失败: {e}")
            sizes[table_name] = -1
    
    return sizes


def identify_missing_indexes(db, is_sqlite_db: bool) -> List[Dict[str, str]]:
    """识别缺失的索引"""
    logger.info("识别缺失的索引...")
    missing_indexes = []
    
    # 检查常见查询模式需要的索引
    checks = [
        {
            "table": "group_ai_accounts",
            "columns": ["script_id", "active"],
            "index_name": "idx_account_script_active",
            "reason": "常用过滤组合：按脚本ID和激活状态过滤"
        },
        {
            "table": "group_ai_accounts",
            "columns": ["server_id", "active"],
            "index_name": "idx_account_server_active",
            "reason": "常用过滤组合：按服务器ID和激活状态过滤"
        },
        {
            "table": "group_ai_scripts",
            "columns": ["status", "created_at"],
            "index_name": "idx_script_status_created",
            "reason": "常用过滤和排序组合：按状态过滤并按创建时间排序"
        },
        {
            "table": "group_ai_dialogue_history",
            "columns": ["account_id", "group_id", "timestamp"],
            "index_name": "idx_dialogue_account_group_time",
            "reason": "常用查询模式：按账号、群组和时间范围查询"
        },
        {
            "table": "group_ai_automation_tasks",
            "columns": ["enabled", "next_run_at"],
            "index_name": "idx_task_enabled_next_run",
            "reason": "常用查询模式：查找启用的任务并按下次运行时间排序"
        }
    ]
    
    # 获取现有索引
    indexes = check_indexes(db, is_sqlite_db)
    
    for check in checks:
        table_name = check["table"]
        if table_name not in indexes:
            missing_indexes.append(check)
            continue
        
        # 检查是否存在匹配的索引
        found = False
        for index in indexes[table_name]:
            if set(index["columns"]) == set(check["columns"]):
                found = True
                break
        
        if not found:
            missing_indexes.append(check)
    
    return missing_indexes


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("数据库慢查询分析")
    logger.info("=" * 60)
    
    settings = get_settings()
    is_sqlite_db = is_sqlite(engine)
    
    logger.info(f"数据库类型: {engine.name}")
    logger.info(f"数据库URL: {settings.database_url.split('@')[-1] if '@' in settings.database_url else '本地文件'}")
    
    with SessionLocal() as db:
        # 1. 检查索引
        indexes = check_indexes(db, is_sqlite_db)
        
        # 2. 检查表大小
        table_sizes = check_table_sizes(db, is_sqlite_db)
        
        # 3. 分析常见查询性能
        query_results = analyze_common_queries(db, is_sqlite_db)
        
        # 4. 识别缺失的索引
        missing_indexes = identify_missing_indexes(db, is_sqlite_db)
    
    # 输出结果
    logger.info("\n" + "=" * 60)
    logger.info("分析结果")
    logger.info("=" * 60)
    
    # 查询性能分析
    logger.info("\n查询性能分析:")
    slow_queries = []
    for result in query_results:
        status = "✓" if result["success"] else "✗"
        time_ms = result["execution_time_ms"]
        logger.info(f"{status} {result['description']}: {time_ms:.2f}ms")
        
        if result["success"] and time_ms > 100:  # 超过100ms视为慢查询
            slow_queries.append(result)
    
    if slow_queries:
        logger.warning(f"\n发现 {len(slow_queries)} 个慢查询（>100ms）:")
        for query in slow_queries:
            logger.warning(f"  - {query['description']}: {query['execution_time_ms']:.2f}ms")
    
    # 缺失索引
    if missing_indexes:
        logger.warning(f"\n发现 {len(missing_indexes)} 个缺失的索引:")
        for idx in missing_indexes:
            logger.warning(f"  - {idx['table']}.{idx['index_name']}: {', '.join(idx['columns'])}")
            logger.warning(f"    原因: {idx['reason']}")
    else:
        logger.info("\n✓ 所有推荐的索引都已存在")
    
    # 保存结果到文件
    report = {
        "database_type": engine.name,
        "indexes": indexes,
        "table_sizes": table_sizes,
        "query_performance": query_results,
        "slow_queries": slow_queries,
        "missing_indexes": missing_indexes
    }
    
    report_path = project_root / "database_analysis_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"\n详细报告已保存到: {report_path}")
    
    return report


if __name__ == "__main__":
    main()

