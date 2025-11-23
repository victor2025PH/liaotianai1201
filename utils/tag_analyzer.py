import asyncio
import re
from typing import Iterable, Optional, Sequence, Set

import aiosqlite

import config
from utils.async_utils import AsyncRateLimiter, run_in_thread
from utils.db_manager import get_user_history, update_user_tag_async

TAG_KEYWORDS = [
    ("AI", ["AI", "人工智能", "GPT", "OpenAI", "ChatGPT"]),
    ("推广", ["推广", "市场", "广告", "拉人", "流量"]),
    ("技术", ["开发", "代码", "软件", "技术", "API"]),
    ("博彩", ["菠菜", "博彩", "游戏", "彩票", "娱乐"]),
    ("情感", ["感情", "情感", "分手", "恋爱", "婚姻", "女朋友", "男朋友"]),
    ("创业", ["创业", "项目", "投资", "老板", "合伙", "资源"]),
    ("生活", ["生活", "家人", "日常", "吃饭", "旅游", "健康"])
]


def extract_tags_from_text(text: str) -> Set[str]:
    """
    基于关键词/正则，智能识别文本标签
    """
    tags = set()
    for tag, keywords in TAG_KEYWORDS:
        for kw in keywords:
            if re.search(kw, text, re.IGNORECASE):
                tags.add(tag)
    return tags


async def analyze_and_update_user_tags(user_id: str, history_limit: int = 30) -> Sequence[str]:
    """
    读取最近多轮聊天，根据内容自动补全用户标签（成长/兴趣/业务/行为）
    """
    history = await run_in_thread(get_user_history, user_id, history_limit)
    all_text = " ".join([h["content"] for h in history])
    tags = extract_tags_from_text(all_text)
    old_tags = set(await get_user_tags(user_id))
    all_tags = sorted(tags.union(old_tags))
    await update_user_tag_async(user_id, ",".join(all_tags), overwrite=True)
    print(f"用户{user_id}标签已更新: {all_tags}")
    return all_tags


async def batch_analyze_all_users(limiter: Optional[AsyncRateLimiter] = None) -> None:
    """
    批量分析全用户标签（适合日常定时/人工审核/业务分流）
    """
    limiter = limiter or AsyncRateLimiter(config.TAG_ANALYZE_RATE_PER_MINUTE, 60)
    async with aiosqlite.connect(config.DB_PATH) as conn:
        cursor = await conn.execute("SELECT user_id FROM users")
        rows = await cursor.fetchall()
    for (user_id,) in rows:
        await limiter.acquire()
        await analyze_and_update_user_tags(user_id)


async def get_user_tags(user_id: str) -> Sequence[str]:
    """
    获取单用户已打标签
    """
    async with aiosqlite.connect(config.DB_PATH) as conn:
        cursor = await conn.execute(
            "SELECT tags FROM users WHERE user_id=?", (user_id,))
        result = await cursor.fetchone()
    if result and result[0]:
        return [tag.strip() for tag in result[0].split(",") if tag.strip()]
    return []


async def main():
    await batch_analyze_all_users()
    print("全用户标签已批量分析/补全。")


if __name__ == "__main__":
    asyncio.run(main())
