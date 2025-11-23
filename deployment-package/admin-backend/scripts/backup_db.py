"""
數據庫備份腳本（用於 Alembic 遷移前備份）

使用方式：
    python -m scripts.backup_db
"""
import os
import shutil
import datetime
from pathlib import Path

from app.core.config import get_settings


def backup_database() -> str | None:
    """
    備份數據庫（遷移前）
    
    返回備份文件路徑，如果失敗則返回 None
    """
    settings = get_settings()
    database_url = settings.database_url
    
    # 解析數據庫路徑
    if database_url.startswith("sqlite"):
        # SQLite: sqlite:///./admin.db 或 sqlite:////absolute/path/admin.db
        db_path_str = database_url.replace("sqlite:///", "")
        # 處理相對路徑（./）
        if db_path_str.startswith("./"):
            db_path = Path(__file__).parent.parent / db_path_str[2:]
        else:
            db_path = Path(db_path_str)
    else:
        # PostgreSQL/MySQL 等其他數據庫，備份方式不同
        print(f"[backup] 非 SQLite 數據庫 ({database_url})，跳過文件備份。")
        print("[backup] 建議使用數據庫特定的備份工具（如 pg_dump）進行備份。")
        return None
    
    if not db_path.exists():
        print(f"[backup] 數據庫文件 {db_path} 不存在，跳過備份。")
        return None
    
    # 創建備份目錄
    backup_dir = Path(__file__).parent.parent / "backup" / "db_bak"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成備份文件名
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_filename = f"before-migrate-{timestamp}-admin.db"
    backup_path = backup_dir / backup_filename
    
    try:
        # 複製數據庫文件
        shutil.copy2(db_path, backup_path)
        print(f"[backup] 數據庫已備份至: {backup_path}")
        return str(backup_path)
    except Exception as e:
        print(f"[backup] 備份失敗: {e}")
        return None


def backup_postgresql() -> str | None:
    """
    備份 PostgreSQL 數據庫（使用 pg_dump）
    
    返回備份文件路徑，如果失敗則返回 None
    """
    import subprocess
    
    settings = get_settings()
    database_url = settings.database_url
    
    if not database_url.startswith("postgresql"):
        return None
    
    # 創建備份目錄
    backup_dir = Path(__file__).parent.parent / "backup" / "db_bak"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成備份文件名
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_filename = f"before-migrate-{timestamp}-admin.sql"
    backup_path = backup_dir / backup_filename
    
    try:
        # 使用 pg_dump 備份
        result = subprocess.run(
            ["pg_dump", database_url],
            stdout=open(backup_path, "w"),
            stderr=subprocess.PIPE,
            text=True,
        )
        
        if result.returncode == 0:
            print(f"[backup] PostgreSQL 數據庫已備份至: {backup_path}")
            return str(backup_path)
        else:
            print(f"[backup] pg_dump 失敗: {result.stderr}")
            return None
    except FileNotFoundError:
        print("[backup] pg_dump 未找到，請確保 PostgreSQL 客戶端工具已安裝。")
        return None
    except Exception as e:
        print(f"[backup] 備份失敗: {e}")
        return None


if __name__ == "__main__":
    settings = get_settings()
    database_url = settings.database_url
    
    if database_url.startswith("postgresql"):
        backup_postgresql()
    else:
        backup_database()

