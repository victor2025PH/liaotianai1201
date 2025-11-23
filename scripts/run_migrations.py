"""
資料庫遷移與備份腳本。

使用方式：
    python -m scripts.run_migrations
"""
import os
import sqlite3
import shutil
import datetime

import config
from migrations import MIGRATIONS


MIGRATION_TABLE = "schema_migrations"


def ensure_backup():
    """
    在執行遷移前備份資料庫。
    """
    db_path = config.DB_PATH
    if not os.path.exists(db_path):
        print(f"[migrate] 資料庫 {db_path} 不存在，跳過備份。")
        return None

    backup_dir = os.path.join(config.BACKUP_DIR, "db_bak")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = os.path.join(
        backup_dir, f"before-migrate-{timestamp}-chat_history.db"
    )
    shutil.copy2(db_path, backup_path)
    print(f"[migrate] 已備份資料庫至 {backup_path}")
    return backup_path


def ensure_migration_table(conn: sqlite3.Connection):
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
            version TEXT PRIMARY KEY,
            description TEXT,
            applied_at TEXT
        );
        """
    )
    conn.commit()


def get_applied_versions(conn: sqlite3.Connection):
    cursor = conn.execute(f"SELECT version FROM {MIGRATION_TABLE}")
    return {row[0] for row in cursor.fetchall()}


def apply_migration(conn: sqlite3.Connection, migration: dict):
    print(f"[migrate] 執行遷移 {migration['version']}: {migration['description']}")
    for stmt in migration.get("statements", []):
        conn.execute(stmt)
    conn.execute(
        f"INSERT INTO {MIGRATION_TABLE} (version, description, applied_at) VALUES (?, ?, datetime('now', 'localtime'))",
        (migration["version"], migration.get("description", "")),
    )
    conn.commit()


def run():
    ensure_backup()

    conn = sqlite3.connect(config.DB_PATH)
    ensure_migration_table(conn)
    applied = get_applied_versions(conn)

    pending = [m for m in MIGRATIONS if m["version"] not in applied]
    if not pending:
        print("[migrate] 無需遷移，資料庫已是最新狀態。")
        conn.close()
        return

    for migration in pending:
        apply_migration(conn, migration)

    conn.close()
    print(f"[migrate] 遷移完成，共執行 {len(pending)} 項。")


if __name__ == "__main__":
    run()

