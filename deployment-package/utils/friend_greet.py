import asyncio
import random
from typing import Iterable, Optional

import aiosqlite

import config
from utils import db_manager
from utils.async_utils import (AsyncRateLimiter, async_sleep_with_jitter,
                               run_in_thread)
from utils.db_manager import update_user_tag_async
from utils.prompt_manager import get_cold_scene_phrase, get_identity


async def auto_welcome_greet(user_id: str, tg_client=None, extra_info=None):
    """
    首轮自动欢迎新好友+主动业务介绍，风格自然，不AI腔
    支持TG分身矩阵批量欢迎，支持后续多平台扩展
    """
    # 读取AI身份和个性化欢迎语
    identity = get_identity(language="zh")
    greetings = [
        f"{identity}，很高兴认识新兄弟，AI分身全天候陪聊！",
        "欢迎新朋友！咱们专注TG自动化、批量云控，有啥业务或合作直接唠！😄",
        "兄弟，有什么想法尽管提，自动批量聊天、推广变现我都能安排的！",
        "新朋友好，咱团队AI分身成千上万，推广、定制、合作都行，随时欢迎唠嗑。"
    ]
    greet_text = random.choice(greetings)
    # 可调用TG/微信/企业IM客户端API，实际部署时写入对应SDK接口
    try:
        if tg_client and hasattr(tg_client, "send_message"):
            await _safe_send_message(tg_client, user_id, greet_text)
        else:
            print(f"[测试模式] 新好友{user_id}欢迎语: {greet_text}")
    except Exception as exc:
        print(f"[AUTO_GREET] 发送欢迎语失败 {user_id}: {exc}")
    # 入库标签“新好友”“已欢迎”
    await update_user_tag_async(user_id, tags="新好友,已欢迎")
    await async_sleep_with_jitter(config.REPLY_DELAY[0], config.REPLY_DELAY[1])


async def auto_growth_care(user_id, tg_client=None):
    """
    成长陪伴/自动关怀（如一段时间未互动、定期唤醒）
    """
    history = await run_in_thread(db_manager.get_user_history, user_id, 20)
    # 判断最近7天是否有互动，如无则主动关怀
    from datetime import datetime, timedelta
    now = datetime.now()
    interacted = False
    for h in history:
        t = h.get("timestamp", "")
        try:
            t_dt = datetime.strptime(t[:19], "%Y-%m-%d %H:%M:%S")
            if (now - t_dt).days < 7:
                interacted = True
                break
        except Exception:
            continue
    if not interacted:
        # 冷场/成长唤醒
        cold_msg = get_cold_scene_phrase()
        try:
            if tg_client and hasattr(tg_client, "send_message"):
                await _safe_send_message(tg_client, user_id, cold_msg)
            else:
                print(f"[测试模式] 成长陪伴关怀: {user_id} {cold_msg}")
        except Exception as exc:
            print(f"[AUTO_CARE] 发送成长陪伴失败 {user_id}: {exc}")


async def batch_auto_greet_new_friends(tg_client=None, user_id_list: Optional[Iterable[str]] = None,
                                       limiter: Optional[AsyncRateLimiter] = None):
    """
    批量新好友自动欢迎（可接入TG分身矩阵自动调度）
    """
    limiter = limiter or AsyncRateLimiter(config.GREET_RATE_PER_MINUTE, 60)
    if not user_id_list:
        async with aiosqlite.connect(config.DB_PATH) as conn:
            cursor = await conn.execute(
                "SELECT user_id FROM users WHERE friend_status='自动入库' OR tags LIKE '%新好友%'")
            rows = await cursor.fetchall()
            user_id_list = [row[0] for row in rows]

    for user_id in user_id_list:
        if not user_id:
            continue
        await limiter.acquire()
        await auto_welcome_greet(user_id, tg_client)
        await async_sleep_with_jitter(0.7, 1.8)


async def _safe_send_message(tg_client, user_id: str, text: str):
    send_method = getattr(tg_client, "send_message", None)
    if send_method is None:
        raise AttributeError("tg_client 缺少 send_message 方法")
    result = send_method(user_id, text)
    if asyncio.iscoroutine(result):
        await result

async def main():
    await batch_auto_greet_new_friends()


if __name__ == "__main__":
    asyncio.run(main())
