import asyncio
from typing import Iterable, Optional

import config
from utils.async_utils import AsyncRateLimiter, async_sleep_with_jitter, maybe_await, run_in_thread
from utils.db_manager import add_user
from utils.excel_manager import import_users_from_excel_async, update_excel_from_db_async


async def _maybe_add_friend(tg_client, account: str) -> None:
    if tg_client is None:
        return
    if hasattr(tg_client, "add_friend"):
        await maybe_await(tg_client.add_friend, account)
    elif hasattr(tg_client, "add_contact"):
        await maybe_await(tg_client.add_contact, account)


async def batch_auto_add_friends(tg_client, account_list: Iterable[str], batch_size: int = 5,
                                 limiter: Optional[AsyncRateLimiter] = None) -> int:
    """
    批量账号自动加好友入库（支持多分身矩阵）
    tg_client: TG客户端对象（需兼容云控/多账号SDK）
    account_list: 待加好友账号（手机号或用户名列表）
    batch_size: 每个分身每天自动添加上限，防风控
    """
    limiter = limiter or AsyncRateLimiter(
        config.ADD_FRIENDS_RATE_PER_MINUTE, 60)
    count = 0
    for acc in account_list:
        if not acc:
            continue
        try:
            await limiter.acquire()
            print(f"[AUTO_ADD] 准备添加好友: {acc}")
            await _maybe_add_friend(tg_client, acc)
            await run_in_thread(add_user, user_id=acc, nickname="",
                               tags="新好友,自动加", friend_status="自动入库")
            count += 1
            await async_sleep_with_jitter(
                config.SEND_MSG_MIN_DELAY, config.SEND_MSG_MAX_DELAY)
            if count >= batch_size:
                print(
                    f"[AUTO_ADD] 本次批量加好友已达上限 {batch_size}，暫停。")
                break
        except Exception as exc:
            print(f"[AUTO_ADD] 加好友失敗 {acc}: {exc}")
    await update_excel_from_db_async()  # 每次批量后同步导出最新Excel
    print(f"[AUTO_ADD] 已自动添加并入库 {count} 个好友。")
    return count


async def batch_import_from_excel(tg_client, excel_path: Optional[str] = None) -> int:
    """
    从Excel批量读取账号并自动加好友（可用于运营定时导入任务）
    """
    users = await import_users_from_excel_async(excel_path or config.EXCEL_PATH)
    account_list = [u.get("user_id") for u in users if u.get("user_id")]
    return await batch_auto_add_friends(tg_client, account_list)


async def main():
    # 示例入口，可依需求替換為實際客戶端與資料入口
    print("批量自动加好友脚本就绪。（示例中未注入 tg_client）")


if __name__ == "__main__":
    asyncio.run(main())
