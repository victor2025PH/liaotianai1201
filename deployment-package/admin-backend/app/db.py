import logging
from pathlib import Path
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# 將 SQLite 相對路徑轉換為絕對路徑，確保數據持久化
if "sqlite" in settings.database_url:
    # 解析 SQLite URL: sqlite:///./admin.db 或 sqlite:///admin.db
    if settings.database_url.startswith("sqlite:///./"):
        # 相對路徑，轉換為絕對路徑（基於項目根目錄）
        db_file = settings.database_url.replace("sqlite:///./", "")
        # 獲取項目根目錄（admin-backend 目錄）
        project_root = Path(__file__).resolve().parent.parent
        db_path = (project_root / db_file).resolve()
        # 確保目錄存在
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # 使用絕對路徑
        settings.database_url = f"sqlite:///{db_path}"
        logger.info(f"SQLite 數據庫路徑已轉換為絕對路徑: {db_path}")
    elif settings.database_url.startswith("sqlite:///") and not Path(settings.database_url.replace("sqlite:///", "")).is_absolute():
        # 相對路徑（沒有 ./ 前綴），也轉換為絕對路徑
        db_file = settings.database_url.replace("sqlite:///", "")
        project_root = Path(__file__).resolve().parent.parent
        db_path = (project_root / db_file).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        settings.database_url = f"sqlite:///{db_path}"
        logger.info(f"SQLite 數據庫路徑已轉換為絕對路徑: {db_path}")

# 連接池配置
# SQLite 不支持 pool_size, max_overflow, pool_timeout 等參數
is_sqlite = "sqlite" in settings.database_url

if is_sqlite:
    # SQLite 配置（使用 NullPool，因為 SQLite 不支持多線程連接池）
    pool_config = {
        "poolclass": pool.NullPool,
        "pool_pre_ping": True,
        "echo": False,
        "future": True
    }
else:
    # PostgreSQL/MySQL 等配置
    pool_config = {
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
        "pool_pre_ping": True,  # 連接前檢查
        "pool_recycle": settings.database_pool_recycle,
        "pool_timeout": settings.database_pool_timeout,
        "echo": False,
        "future": True
    }

try:
    engine = create_engine(settings.database_url, **pool_config)
except (ModuleNotFoundError, TypeError) as exc:
    logger.warning("無法加載數據庫驅動或配置錯誤 %s，回退到內置 SQLite。", exc)
    # 使用絕對路徑
    project_root = Path(__file__).resolve().parent.parent
    db_path = (project_root / "admin.db").resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    settings.database_url = f"sqlite:///{db_path}"
    logger.info(f"回退到 SQLite，使用絕對路徑: {db_path}")
    # SQLite 使用 NullPool
    pool_config = {
        "poolclass": pool.NullPool,
        "pool_pre_ping": True,
        "echo": False,
        "future": True
    }
    engine = create_engine(settings.database_url, **pool_config)

# SQLite 優化
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """SQLite 特定優化"""
    if "sqlite" in settings.database_url:
        cursor = dbapi_conn.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB 緩存
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA temp_store=MEMORY")
        except Exception as e:
            logger.warning(f"SQLite 優化失敗: {e}")
        finally:
            cursor.close()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    """獲取數據庫會話"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

