import os
import shutil
import asyncio
import datetime
import threading
import time
from typing import Awaitable, Callable, Dict, List, Optional

import config
from utils.async_utils import run_in_thread

DATA_DIR = config.DATA_DIR
BACKUP_DIR = config.BACKUP_DIR
LOGS_DIR = config.LOGS_DIR

EXCEL_PATH = config.EXCEL_PATH
DB_PATH = config.DB_PATH


def auto_init_backup_dirs():
    """
    自动创建备份目录
    """
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    if not os.path.exists(os.path.join(BACKUP_DIR, "excel_bak")):
        os.makedirs(os.path.join(BACKUP_DIR, "excel_bak"))
    if not os.path.exists(os.path.join(BACKUP_DIR, "db_bak")):
        os.makedirs(os.path.join(BACKUP_DIR, "db_bak"))
    if not os.path.exists(os.path.join(BACKUP_DIR, "log_bak")):
        os.makedirs(os.path.join(BACKUP_DIR, "log_bak"))


def backup_file(src, dst_dir, prefix=""):
    """
    通用文件备份函数
    """
    if not os.path.exists(src):
        return
    date_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = os.path.basename(src)
    bak_path = os.path.join(dst_dir, f"{prefix}{date_str}-{base}")
    shutil.copy2(src, bak_path)
    print(f"已自动备份: {bak_path}")
    return bak_path


def backup_excel():
    """
    备份用户Excel数据
    """
    dst_dir = os.path.join(BACKUP_DIR, "excel_bak")
    return backup_file(EXCEL_PATH, dst_dir, prefix="excel-")


def backup_db():
    """
    备份数据库文件
    """
    dst_dir = os.path.join(BACKUP_DIR, "db_bak")
    return backup_file(DB_PATH, dst_dir, prefix="db-")


def backup_logs() -> List[str]:
    """
    备份主日志
    """
    paths = []
    for file in os.listdir(LOGS_DIR):
        if file.endswith(".log"):
            src = os.path.join(LOGS_DIR, file)
            dst_dir = os.path.join(BACKUP_DIR, "log_bak")
            paths.append(backup_file(src, dst_dir, prefix="log-"))
    return paths


def backup_once() -> Dict[str, Optional[str]]:
    auto_init_backup_dirs()
    excel_path = backup_excel()
    db_path = backup_db()
    log_paths = backup_logs()
    return {"excel": excel_path, "db": db_path, "logs": log_paths}


async def backup_once_async() -> Dict[str, Optional[str]]:
    return await run_in_thread(backup_once)


def auto_backup_all(interval_hours=24):
    """
    自动定时全量备份（建议由主程序单独后台线程调用）
    """
    auto_init_backup_dirs()
    while True:
        backup_once()
        print(f"[{datetime.datetime.now()}] 已完成一次全量数据备份")
        time.sleep(interval_hours * 3600)


def start_backup_thread():
    """
    后台启动定时备份任务（建议主程序启动时自动调用）
    """
    t = threading.Thread(target=auto_backup_all, daemon=True)
    t.start()
    print("自动数据备份线程已启动。")
    return t


async def schedule_auto_backup(interval_seconds: float = 3600,
                               cycles: int = 0,
                               stop_event: Optional[asyncio.Event] = None,
                               validator: Optional[Callable[[Dict[str, Optional[str]]], Awaitable[None] | None]] = None) -> None:
    """
    使用 asyncio 調度定時備份。

    :param interval_seconds: 兩次備份之間的間隔秒數。
    :param cycles: 需要執行的備份輪數。若為 0 則持續執行直到 stop_event。
    :param stop_event: 可選 asyncio.Event，用於外部停止。
    :param validator: 傳入備份結果 dict 以進行驗證的協程或函式。
    """
    iteration = 0
    while True:
        result = await backup_once_async()
        if validator:
            value = validator(result)
            if asyncio.iscoroutine(value):
                await value
        iteration += 1
        if cycles and iteration >= cycles:
            break
        if stop_event:
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
                if stop_event.is_set():
                    break
            except asyncio.TimeoutError:
                continue
        else:
            await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    auto_init_backup_dirs()
    backup_excel()
    backup_db()
    backup_logs()
    print("手动备份完成。")
