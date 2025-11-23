async def get_turn_count(user_id):
    """
    获取对话轮次（用户+AI各记1次）。
    """
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM chat_history WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
    total = row[0] if row else 0
    # 每轮包含用户和AI各一次，向上取整
    return (total + 1) // 2
import sqlite3
import aiosqlite
import config

DB_PATH = config.DB_PATH


def init_history_db():
    """
    确保历史聊天表存在（如缺失则自动建表）
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        timestamp TEXT,
        role TEXT,          -- user/assistant
        content TEXT
    );
    """)
    conn.commit()
    conn.close()


async def add_to_history(user_id, role, content):
    """
    新增一条聊天历史（写入数据库）
    """
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "INSERT INTO chat_history (user_id, timestamp, role, content) VALUES (?, datetime('now', 'localtime'), ?, ?)",
            (user_id, role, content)
        )
        await conn.commit()


async def get_history(user_id, max_len=30):
    """
    获取最近max_len条历史（倒序排列，role+content标准格式，适配OpenAI messages历史）
    """
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            "SELECT role, content, timestamp FROM chat_history WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, max_len)
        )
        data = await cursor.fetchall()
    # 按OpenAI要求格式返回，最新的在后
    return [{"role": r, "content": c, "timestamp": t} for r, c, t in reversed(data)]


async def get_message_count(user_id):
    """
    获取指定用户发送的消息总数。
    """
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM chat_history WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
    count = row[0] if row else 0
    return count


def batch_get_all_history(user_id):
    """
    获取该用户所有历史（用于成长陪伴/标签分析）
    """
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT role, content, timestamp FROM chat_history WHERE user_id=? ORDER BY id ASC",
        (user_id,)
    )
    data = c.fetchall()
    conn.close()
    return [{"role": r, "content": c, "timestamp": t} for r, c, t in data]


def delete_user_history(user_id):
    """
    删除某用户所有历史记录
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM chat_history WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def get_last_user_message(user_id):
    """
    获取该用户最后一条用户消息（不含AI回复）
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT content FROM chat_history WHERE user_id=? AND role='user' ORDER BY id DESC LIMIT 1",
        (user_id,)
    )
    result = c.fetchone()
    conn.close()
    return result[0] if result else ""


def get_last_ai_reply(user_id):
    """
    获取该用户最后一条AI回复（不含用户输入）
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT content FROM chat_history WHERE user_id=? AND role='assistant' ORDER BY id DESC LIMIT 1",
        (user_id,)
    )
    result = c.fetchone()
    conn.close()
    return result[0] if result else ""


if __name__ == "__main__":
    init_history_db()
    print("聊天历史表初始化完成。")
