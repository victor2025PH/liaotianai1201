import asyncio
import os
from typing import List, Dict

import pandas as pd

import config

EXCEL_PATH = config.EXCEL_PATH

# Excel表头标准映射，中英对照
TABLE_HEADER = [
    ("用户ID", "user_id"),
    ("昵称", "nickname"),
    ("标签", "tags"),
    ("入库时间", "add_time"),
    ("最新对话", "recent_chat"),
    ("好友分组", "friend_status")
]


def get_excel_columns():
    """返回中文(英文)表头双语列"""
    return [f"{zh}({en})" for zh, en in TABLE_HEADER]


def get_excel_columns_map():
    """返回Excel列到英文字段名的映射dict"""
    return {f"{zh}({en})": en for zh, en in TABLE_HEADER}


def auto_init_excel():
    """
    自动初始化用户Excel，带中英表头（如不存在）
    """
    if not os.path.exists(EXCEL_PATH):
        columns = get_excel_columns()
        df = pd.DataFrame(columns=columns)
        df.to_excel(EXCEL_PATH, index=False)
        print(f"用户数据Excel已自动创建: {EXCEL_PATH}")


def export_users_to_excel(users, excel_path=EXCEL_PATH):
    """
    导出users数据到Excel，支持中英双语表头
    users: List[dict]
    """
    columns = get_excel_columns()
    rows = []
    for user in users:
        row = []
        for _, en in TABLE_HEADER:
            row.append(user.get(en, ""))
        rows.append(row)
    df = pd.DataFrame(rows, columns=columns)
    df.to_excel(excel_path, index=False)
    print(f"已导出{len(users)}条用户数据到Excel: {excel_path}")


def import_users_from_excel(excel_path=EXCEL_PATH):
    """
    从Excel导入用户数据，返回List[dict]（自动识别中英表头）
    """
    columns_map = get_excel_columns_map()
    df = pd.read_excel(excel_path)
    users = []
    for _, row in df.iterrows():
        user = {}
        for excel_col, en in columns_map.items():
            user[en] = row.get(excel_col, "")
        users.append(user)
    return users


def update_excel_from_db():
    """
    自动从数据库读取所有用户，导出到Excel（覆盖）
    """
    from utils.db_manager import sqlite3, DB_PATH
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT user_id, nickname, tags, add_time, recent_chat, friend_status FROM users")
    data = c.fetchall()
    conn.close()
    users = []
    for row in data:
        users.append(dict(zip([en for _, en in TABLE_HEADER], row)))
    export_users_to_excel(users)


def batch_add_users_from_excel():
    """
    批量从Excel导入用户并写入数据库（如有新增用户）
    """
    from utils.db_manager import add_user
    users = import_users_from_excel()
    for user in users:
        add_user(
            user_id=user.get("user_id", ""),
            nickname=user.get("nickname", ""),
            tags=user.get("tags", ""),
            friend_status=user.get("friend_status", "普通好友")
        )
    print(f"已批量导入{len(users)}条用户到数据库")


async def import_users_from_excel_async(excel_path: str = EXCEL_PATH) -> List[Dict]:
    return await asyncio.to_thread(import_users_from_excel, excel_path)


async def update_excel_from_db_async() -> None:
    await asyncio.to_thread(update_excel_from_db)


if __name__ == "__main__":
    auto_init_excel()
    print("Excel初始化完成。")
