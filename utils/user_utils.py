"""
用户画像信息读取工具
- 自动从数据库和Excel表格读取user_id对应的昵称、标签、签名、备注等
- 全程日志输出，便于业务追踪
"""
import asyncio
import logging

import pandas as pd
import aiosqlite
import config

logger = logging.getLogger("user_utils")


async def get_user_profile_from_db(user_id):
    """
    从数据库读取用户画像信息（异步）
    """
    async with aiosqlite.connect(config.DB_PATH) as conn:
        cursor = await conn.execute(
            "SELECT first_name, tags, bio, remark, country FROM users WHERE user_id=?",
            (user_id,)
        )
        row = await cursor.fetchone()
    if not row:
        logger.warning(f"[user_utils] 数据库无user_id={user_id}信息")
        return {}
    profile = {
        "first_name": row[0] or "",
        "tags": [t.strip() for t in (row[1] or "").split(",") if t.strip()],
        "bio": row[2] or "",
        "remark": row[3] or "",
        "country": row[4] or "",
        "user_id": user_id
    }
    logger.info(f"[user_utils] 读取数据库user_profile: {profile}")
    return profile


async def get_user_profile_from_excel(user_id):
    """
    从Excel读取用户画像信息（异步封装）
    """
    loop = asyncio.get_running_loop()
    df = await loop.run_in_executor(None, pd.read_excel, config.EXCEL_PATH)
    row = df[df["用户ID"] == user_id]
    if row.empty:
        logger.warning(f"[user_utils] Excel无user_id={user_id}信息")
        return {}
    row = row.iloc[0]
    profile = {
        "first_name": row.get("昵称", ""),
        "tags": [t.strip() for t in str(row.get("用户标签", "")).split(",") if t.strip()],
        "bio": row.get("签名", ""),
        "remark": row.get("备注", ""),
        "country": row.get("国家", ""),
        "user_id": user_id
    }
    logger.info(f"[user_utils] 读取Excel user_profile: {profile}")
    return profile


async def get_user_profile(user_id):
    """
    自动优先用DB，无则用Excel（异步）
    """
    profile = await get_user_profile_from_db(user_id)
    if not profile:
        profile = await get_user_profile_from_excel(user_id)
    logger.info(f"[user_utils] 综合user_profile: {profile}")
    return profile


def get_user_profile_sync(user_id):
    """
    同步封装，供离线脚本或非异步场景使用。
    """
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            raise RuntimeError("請在異步環境中直接 await get_user_profile。")
    except RuntimeError:
        return asyncio.run(get_user_profile(user_id))
    return loop.run_until_complete(get_user_profile(user_id))
