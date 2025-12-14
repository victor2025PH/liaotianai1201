#!/usr/bin/env python3
"""
修复 Worker 节点 Session 文件读取问题
解决 "no such column: server_address" 和 "no such column: version" 错误
"""

import sqlite3
import os
from pathlib import Path
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_session_file(session_path: str) -> bool:
    """
    修复 Session 文件，添加缺失的列
    
    Args:
        session_path: Session 文件路径
        
    Returns:
        是否修复成功
    """
    try:
        if not os.path.exists(session_path):
            logger.error(f"Session 文件不存在: {session_path}")
            return False
        
        # 备份原文件
        backup_path = f"{session_path}.backup"
        if not os.path.exists(backup_path):
            import shutil
            shutil.copy2(session_path, backup_path)
            logger.info(f"已备份: {backup_path}")
        
        # 连接数据库
        conn = sqlite3.connect(session_path)
        cursor = conn.cursor()
        
        # 检查 sessions 表结构
        cursor.execute("PRAGMA table_info(sessions)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        # 添加缺失的列
        if 'server_address' not in columns:
            try:
                cursor.execute("ALTER TABLE sessions ADD COLUMN server_address TEXT")
                logger.info(f"已添加 server_address 列到 {session_path}")
            except sqlite3.OperationalError as e:
                logger.warning(f"添加 server_address 列失败（可能已存在）: {e}")
        
        if 'port' not in columns:
            try:
                cursor.execute("ALTER TABLE sessions ADD COLUMN port INTEGER")
                logger.info(f"已添加 port 列到 {session_path}")
            except sqlite3.OperationalError as e:
                logger.warning(f"添加 port 列失败（可能已存在）: {e}")
        
        # 检查 version 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='version'")
        if not cursor.fetchone():
            try:
                cursor.execute("CREATE TABLE IF NOT EXISTS version (version INTEGER)")
                cursor.execute("INSERT INTO version (version) VALUES (1)")
                logger.info(f"已创建 version 表到 {session_path}")
            except sqlite3.OperationalError as e:
                logger.warning(f"创建 version 表失败: {e}")
        else:
            # 检查 version 表是否有数据
            cursor.execute("SELECT COUNT(*) FROM version")
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute("INSERT INTO version (version) VALUES (1)")
                logger.info(f"已添加 version 数据到 {session_path}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Session 文件修复成功: {session_path}")
        return True
        
    except Exception as e:
        logger.error(f"修复 Session 文件失败 {session_path}: {e}", exc_info=True)
        return False


def extract_user_id_from_session(session_path: str):
    """
    从 Session 文件提取 user_id
    
    Args:
        session_path: Session 文件路径
        
    Returns:
        user_id 或 None
    """
    try:
        conn = sqlite3.connect(session_path)
        cursor = conn.cursor()
        
        # 尝试从 sessions 表获取 user_id
        try:
            cursor.execute("SELECT dc_id, server_address, port, auth_key FROM sessions LIMIT 1")
            row = cursor.fetchone()
            if row:
                # 如果有数据，尝试从 peers 表获取 user_id
                cursor.execute("SELECT id FROM peers WHERE id > 0 LIMIT 1")
                peer_row = cursor.fetchone()
                if peer_row:
                    user_id = str(peer_row[0])
                    conn.close()
                    return user_id
        except sqlite3.OperationalError as e:
            logger.warning(f"从 sessions 表读取失败: {e}")
        
        # 尝试从文件名提取（如果文件名是账号ID）
        filename = Path(session_path).stem
        if filename.isdigit():
            conn.close()
            return filename
        
        conn.close()
        return None
        
    except Exception as e:
        logger.error(f"提取 user_id 失败 {session_path}: {e}")
        return None


def fix_all_sessions(sessions_dir: str):
    """
    修复目录中的所有 Session 文件
    
    Args:
        sessions_dir: Session 文件目录
    """
    sessions_path = Path(sessions_dir)
    if not sessions_path.exists():
        logger.error(f"Session 目录不存在: {sessions_dir}")
        return
    
    session_files = list(sessions_path.glob("*.session"))
    logger.info(f"找到 {len(session_files)} 个 Session 文件")
    
    fixed_count = 0
    for session_file in session_files:
        if fix_session_file(str(session_file)):
            fixed_count += 1
            
            # 尝试提取 user_id
            user_id = extract_user_id_from_session(str(session_file))
            if user_id:
                logger.info(f"  ✅ {session_file.name}: user_id = {user_id}")
            else:
                logger.warning(f"  ⚠️  {session_file.name}: 无法提取 user_id")
    
    logger.info(f"修复完成: {fixed_count}/{len(session_files)} 个文件")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        sessions_dir = sys.argv[1]
    else:
        # 默认使用当前目录下的 sessions 文件夹
        sessions_dir = "./sessions"
    
    fix_all_sessions(sessions_dir)

