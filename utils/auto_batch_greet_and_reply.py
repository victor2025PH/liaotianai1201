import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd
from pyrogram import Client
from pyrogram.errors import PeerIdInvalid

import config
from utils.async_utils import (AsyncRateLimiter, async_sleep_with_jitter,
                               run_in_thread)

EXCEL_PATH = config.EXCEL_PATH

USER_FIELD_CANDIDATES = {
    "username": ["用户名(username)", "用户名", "user_name", "username"],
    "user_id": ["用户ID(user_id)", "用户ID", "id", "user_id"],
    "first_name": ["昵称(first_name)", "昵称", "first_name"],
    "greet_sent": ["是否已欢迎(greet_sent)", "是否打招呼", "是否已欢迎", "greet_sent"],
    "msg_count": ["消息数(msg_count)", "消息数", "msg_count"],
    "last_chat_time": ["最近对话时间(last_chat_time)", "最后聊天时间",
                       "last_chat_time"],
    "unread": ["未回复消息数(unread)", "未回复消息数", "未回复消息数_", "未回复消息数", "unread"],
}

GREETING_MESSAGE_TEMPLATE = "你好，{name}，我是阿龙AI分身，TG业务自动化和推广专家，欢迎加好友合作~"
DEFAULT_REPLY = "你好，这里是阿龙AI分身，刚刚看到你的消息，有什么可以帮到你的吗？"


@dataclass
class UserRow:
    excel_row: int
    username: Optional[str]
    user_id: Optional[str]
    first_name: Optional[str]
    greet_sent: str
    msg_count: int
    last_chat_time: str
    unread: int


def _match_column(columns: Iterable[str], candidates: List[str]) -> Optional[str]:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


async def read_excel_users(path: str) -> Tuple[pd.DataFrame, List[UserRow], Dict[str, Optional[str]]]:
    df = await run_in_thread(pd.read_excel, path)
    columns = set(df.columns)
    mapping: Dict[str, Optional[str]] = {}
    for key, candidates in USER_FIELD_CANDIDATES.items():
        mapping[key] = _match_column(columns, candidates)
    users: List[UserRow] = []
    for idx, row in df.iterrows():
        users.append(
            UserRow(
                excel_row=idx,
                username=str(row.get(mapping["username"], "")).strip()
                if mapping["username"] else None,
                user_id=str(row.get(mapping["user_id"], "")).strip()
                if mapping["user_id"] else None,
                first_name=str(row.get(mapping["first_name"], "")).strip()
                if mapping["first_name"] else None,
                greet_sent=str(row.get(mapping["greet_sent"], "")).strip()
                if mapping["greet_sent"] else "",
                msg_count=int(row.get(mapping["msg_count"], 0)
                              ) if mapping["msg_count"] else 0,
                last_chat_time=str(row.get(mapping["last_chat_time"], ""))
                if mapping["last_chat_time"] else "",
                unread=int(row.get(mapping["unread"], 0)
                           ) if mapping["unread"] else 0,
            )
        )
    return df, users, mapping


async def write_back(df: pd.DataFrame, path: str) -> None:
    await run_in_thread(lambda: df.to_excel(path, index=False))


def _build_client_kwargs() -> Dict[str, str]:
    kwargs: Dict[str, str] = {}
    if config.SESSION_STRING:
        kwargs["session_string"] = config.SESSION_STRING
    return kwargs


def _resolve_session_name() -> str:
    if config.SESSION_STRING:
        return config.SESSION_NAME
    if config.SESSION_FILE:
        return config.SESSION_FILE
    return config.SESSION_NAME


async def _send_with_retry(client: Client, chat_id: int | str, text: str,
                           limiter: AsyncRateLimiter) -> None:
    await limiter.acquire()
    try:
        await client.send_message(chat_id, text)
    except PeerIdInvalid as exc:
        print(f"[AUTO_BATCH] 无法向 {chat_id} 发送消息: {exc}")
    except Exception as exc:
        print(f"[AUTO_BATCH] 发送消息发生异常 {chat_id}: {exc}")
        raise


async def auto_batch_greet_and_reply(excel_path: str = EXCEL_PATH,
                                     client: Optional[Client] = None,
                                     greet_limiter: Optional[AsyncRateLimiter] = None,
                                     reply_limiter: Optional[AsyncRateLimiter] = None) -> None:
    greet_limiter = greet_limiter or AsyncRateLimiter(
        config.GREET_RATE_PER_MINUTE, 60)
    reply_limiter = reply_limiter or AsyncRateLimiter(
        config.AUTO_REPLY_RATE_PER_MINUTE, 60)

    df, users, column_map = await read_excel_users(excel_path)
    for key in ("greet_sent", "last_chat_time"):
        col = column_map.get(key)
        if col and df[col].dtype != "object":
            df[col] = df[col].astype("object")
    session_kwargs = _build_client_kwargs()
    own_client = False
    if client is None:
        client = Client(
            _resolve_session_name(),
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            **session_kwargs
        )
        own_client = True

    async def _process_greeting(user: UserRow) -> None:
        if user.greet_sent.strip() == "是":
            return
        target = user.username or user.user_id
        if not target:
            return
        greet_text = GREETING_MESSAGE_TEMPLATE.format(
            name=user.first_name or user.username or "朋友")
        try:
            await _send_with_retry(client, target, greet_text, greet_limiter)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if column_map["msg_count"]:
                df.at[user.excel_row, column_map["msg_count"]
                      ] = user.msg_count + 1
            if column_map["last_chat_time"]:
                df.at[user.excel_row, column_map["last_chat_time"]] = now_str
            if column_map["greet_sent"]:
                df.at[user.excel_row, column_map["greet_sent"]] = "是"
            print(f"[AUTO_BATCH] 成功给 {target} 发送问候")
            await async_sleep_with_jitter(1.0, 2.5)
        except Exception as exc:
            print(f"[AUTO_BATCH] 发送问候失败 {target}: {exc}")

    async def _process_replies() -> None:
        async for dialog in client.get_dialogs():
            if dialog.chat.type != "private":
                continue
            user_id = str(dialog.chat.id)
            username = dialog.chat.username
            target_row = None
            for user in users:
                if (user.user_id and user.user_id == user_id) or (
                        user.username and username and user.username == f"@{username}"):
                    target_row = user
                    break
            if target_row is None:
                continue
            unread_count = dialog.unread_messages_count or 0
            if unread_count <= 0:
                if column_map["unread"]:
                    df.at[target_row.excel_row, column_map["unread"]] = 0
                continue
            try:
                history = await client.get_chat_history(dialog.chat.id, limit=unread_count)
            except Exception as exc:
                print(f"[AUTO_BATCH] 读取 {dialog.chat.id} 历史消息失败: {exc}")
                continue
            for message in reversed(list(history)):
                if not message.from_user or message.from_user.id != dialog.chat.id:
                    continue
                try:
                    await _send_with_retry(client, dialog.chat.id,
                                           DEFAULT_REPLY, reply_limiter)
                    print(f"[AUTO_BATCH] 自动回复 {dialog.chat.id}")
                except Exception:
                    continue
                await async_sleep_with_jitter(0.8, 2.0)
            if column_map["unread"]:
                df.at[target_row.excel_row, column_map["unread"]] = 0

    async def _runner():
        for user in users:
            await _process_greeting(user)
        await _process_replies()
        await write_back(df, excel_path)

    if own_client:
        async with client:
            await _runner()
    else:
        await _runner()


async def main():
    await auto_batch_greet_and_reply()


if __name__ == "__main__":
    asyncio.run(main())
