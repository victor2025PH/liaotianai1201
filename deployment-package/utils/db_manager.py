import asyncio
import sqlite3
import aiosqlite
import config

DB_PATH = config.DB_PATH

USER_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    first_name TEXT,        -- 用户昵称/名字
    nickname TEXT,          -- 备用昵称
    tags TEXT,              -- 用户标签（逗号分隔）
    bio TEXT,               -- 用户个人简介
    remark TEXT,            -- 我们的备注
    country TEXT,           -- 用户国家/地区
    add_time TEXT,
    recent_chat TEXT,
    friend_status TEXT      -- 备注关系/分组
);
"""

CHAT_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    timestamp TEXT,
    role TEXT,              -- user/assistant
    content TEXT
);
"""

TAG_TABLE = """
CREATE TABLE IF NOT EXISTS tags (
    tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    tag TEXT,
    create_time TEXT
);
"""


def auto_init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(USER_TABLE)
    c.execute(CHAT_HISTORY_TABLE)
    c.execute(TAG_TABLE)
    conn.commit()
    conn.close()


def add_user(user_id, first_name, nickname="", tags="", friend_status="普通好友"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO users (user_id, first_name, nickname, tags, bio, remark, country, add_time, recent_chat, friend_status) VALUES (?, ?, ?, ?, '', '', '', datetime('now', 'localtime'), '', ?)",
        (user_id, first_name, nickname, tags, friend_status)
    )
    conn.commit()
    conn.close()

# --- v6.0 新增功能：統一標籤更新 ---


def _normalize_tags(tags):
    if tags is None:
        return set()
    if isinstance(tags, str):
        parts = tags.split(",")
    elif isinstance(tags, (list, set, tuple)):
        parts = tags
    else:
        raise TypeError("tags 參數必須為字串或可迭代物件")
    normalized = []
    for item in parts:
        value = str(item).strip()
        if value:
            normalized.append(value)
    return set(normalized)


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            raise RuntimeError("Cannot 在事件循環內直接調用同步包裹的資料庫方法，請改用對應的 async 函式。")
    except RuntimeError:
        return asyncio.run(coro)
    return loop.run_until_complete(coro)


async def update_user_tag_async(user_id, tags, overwrite=False):
    """
    更新使用者標籤。

    :param user_id: 使用者 ID
    :param tags: str 或 Iterable，逗號分隔或列表的標籤集合
    :param overwrite: 是否覆蓋既有標籤，預設為 False（合併）
    """
    new_tags = _normalize_tags(tags)
    async with aiosqlite.connect(DB_PATH) as conn:
        if not overwrite:
            cursor = await conn.execute(
                "SELECT tags FROM users WHERE user_id=?", (user_id,))
            row = await cursor.fetchone()
            if row and row[0]:
                existing = _normalize_tags(row[0])
                new_tags = existing.union(new_tags)

        tags_str = ",".join(sorted(new_tags))
        cursor = await conn.execute(
            "UPDATE users SET tags=? WHERE user_id=?",
            (tags_str, user_id)
        )
        if cursor.rowcount == 0:
            await conn.execute(
                "INSERT INTO users (user_id, first_name, nickname, tags, bio, remark, country, add_time, recent_chat, friend_status) VALUES (?, '', '', ?, '', '', '', datetime('now', 'localtime'), '', '普通好友')",
                (user_id, tags_str)
            )
        await conn.commit()


def update_user_tag(user_id, tags, overwrite=False):
    """
    同步封裝，供非 async 腳本調用。
    """
    return _run_async(update_user_tag_async(user_id, tags, overwrite=overwrite))

# --- v4.0 新增功能：更新用户资料 ---


async def update_user_profile_async(user_id, profile_data):
    """
    通用更新用户资料函数。
    :param user_id: 用户ID
    :param profile_data: 一个包含要更新字段的字典，例如 {"first_name": "小明", "tags": "重要客户"}
    """
    if not profile_data:
        return

    # 动态构建 SET 子句
    set_clauses = []
    values = []
    for key, value in profile_data.items():
        set_clauses.append(f"{key} = ?")
        values.append(value)

    if not set_clauses:
        return

    values.append(user_id)
    sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = ?"

    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(sql, tuple(values))
        await conn.commit()


def update_user_profile(user_id, profile_data):
    """
    同步封裝，與舊腳本兼容。若在 async 環境中請使用 update_user_profile_async。
    """
    return _run_async(update_user_profile_async(user_id, profile_data))


def add_chat_history(user_id, role, content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO chat_history (user_id, timestamp, role, content) VALUES (?, datetime('now', 'localtime'), ?, ?)",
        (user_id, role, content)
    )
    conn.commit()
    conn.close()


def get_user_history(user_id, limit=50):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT role, content, timestamp FROM chat_history WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (user_id, limit)
    )
    data = c.fetchall()
    conn.close()
    return [{"role": r, "content": c, "timestamp": t} for r, c, t in reversed(data)]


def get_user_tags(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT tags FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result and result[0]:
        return [tag.strip() for tag in result[0].split(",") if tag.strip()]
    return []


def batch_export_to_excel(excel_path):
    import pandas as pd
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT user_id as 用户ID, first_name as 名字, nickname as 备用昵称, tags as 标签, bio as 个人简介, remark as 备注, country as 国家, add_time as 入库时间, recent_chat as 最新对话, friend_status as 好友分组 FROM users", conn)
    df.to_excel(excel_path, index=False)
    conn.close()
