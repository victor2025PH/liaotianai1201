"""
運行 Alembic 遷移（含遷移前備份）

使用方式：
    python -m scripts.run_migrations
    poetry run python -m scripts.run_migrations
"""
import os
import sys
import subprocess
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.backup_db import backup_database, backup_postgresql
from app.core.config import get_settings


def run_migrations():
    """運行 Alembic 遷移（含遷移前備份）"""
    settings = get_settings()
    database_url = settings.database_url
    
    print("=" * 60)
    print("Alembic 數據庫遷移")
    print("=" * 60)
    
    # 步驟 1: 備份數據庫
    print("\n[1/2] 備份數據庫...")
    if database_url.startswith("postgresql"):
        backup_path = backup_postgresql()
    else:
        backup_path = backup_database()
    
    if backup_path:
        print(f"✅ 備份完成: {backup_path}")
    else:
        print("⚠️  備份跳過或失敗，繼續遷移...")
    
    # 步驟 2: 運行 Alembic 遷移
    print("\n[2/2] 運行 Alembic 遷移...")
    try:
        # 切換到 admin-backend 目錄
        os.chdir(project_root)
        
        # 運行 alembic upgrade head
        result = subprocess.run(
            ["poetry", "run", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        if result.returncode == 0:
            print("✅ 遷移完成")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ 遷移失敗")
            if result.stderr:
                print(result.stderr)
            if result.stdout:
                print(result.stdout)
            sys.exit(1)
            
    except FileNotFoundError:
        print("❌ 未找到 poetry 或 alembic，請確保已安裝依賴。")
        print("   嘗試使用: poetry install")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 遷移過程出錯: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("遷移完成！")
    print("=" * 60)


if __name__ == "__main__":
    run_migrations()

