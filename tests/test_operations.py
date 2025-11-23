import asyncio
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

import config

from utils import db_manager
from utils.async_utils import AsyncRateLimiter
from utils.friend_greet import batch_auto_greet_new_friends
from utils.tag_analyzer import (analyze_and_update_user_tags,
                                batch_analyze_all_users)
from utils.auto_batch_greet_and_reply import auto_batch_greet_and_reply
from utils import auto_backup


@pytest.mark.asyncio
async def test_friend_greet_updates_tags_and_sends_message(temp_env, fast_sleep, monkeypatch):
    db_manager.add_user("1001", "测试用户")

    class DummyClient:
        def __init__(self):
            self.sent = []

        async def send_message(self, chat_id, text):
            self.sent.append((chat_id, text))

    client = DummyClient()
    limiter = AsyncRateLimiter(100, 60)
    await batch_auto_greet_new_friends(tg_client=client, user_id_list=["1001"], limiter=limiter)
    assert client.sent, "应发送自动欢迎消息"
    tags = db_manager.get_user_tags("1001")
    assert "已欢迎" in tags


@pytest.mark.asyncio
async def test_tag_analyzer_updates_tags(temp_env, fast_sleep, monkeypatch):
    user_id = "u-2001"
    db_manager.add_user(user_id, "标记用户")
    now = datetime.now()
    for text in ["我想了解AI推广", "我们团队专注自动化和创业"]:
        db_manager.add_chat_history(user_id, "user", text)
    tags = await analyze_and_update_user_tags(user_id)
    assert {"AI", "推广", "创业"}.issubset(set(tags))


@pytest.mark.asyncio
async def test_batch_tag_analyzer_uses_rate_limit(temp_env, fast_sleep, monkeypatch):
    db_manager.add_user("u1", "A")
    db_manager.add_user("u2", "B")
    limiter = AsyncRateLimiter(100, 60)
    await batch_analyze_all_users(limiter)


@pytest.mark.asyncio
async def test_auto_batch_greet_and_reply(monkeypatch, temp_env, fast_sleep):
    from tests.conftest import PyrogramStubClient, StubDialog, StubMessage

    df = pd.DataFrame([{
        "用户名(username)": "@tester",
        "用户ID(user_id)": "3001",
        "昵称(first_name)": "小测",
        "是否已欢迎(greet_sent)": "",
        "消息数(msg_count)": 0,
        "最近对话时间(last_chat_time)": "",
        "未回复消息数(unread)": 1
    }])
    df.to_excel(temp_env["excel_path"], index=False)

    dialog = StubDialog(chat_id=3001, username="tester", unread=1)
    message = StubMessage(chat_id=3001, text="你好", from_user=True)
    client = PyrogramStubClient(dialogs=[dialog], histories={3001: [message]})

    greet_limiter = AsyncRateLimiter(100, 60)
    reply_limiter = AsyncRateLimiter(100, 60)

    await auto_batch_greet_and_reply(excel_path=temp_env["excel_path"],
                                     client=client,
                                     greet_limiter=greet_limiter,
                                     reply_limiter=reply_limiter)

    assert any("@tester" in str(item["chat_id"]) or item["chat_id"] == "@tester" for item in client.sent_messages)
    assert any(item["chat_id"] == 3001 for item in client.sent_messages)

    result_df = pd.read_excel(temp_env["excel_path"])
    assert result_df.iloc[0]["是否已欢迎(greet_sent)"] == "是"
    assert result_df.iloc[0]["未回复消息数(unread)"] == 0


@pytest.mark.asyncio
async def test_schedule_auto_backup(monkeypatch, tmp_path):
    backup_dir = tmp_path / "backup"
    data_dir = tmp_path / "data"
    logs_dir = tmp_path / "logs"
    data_dir.mkdir()
    logs_dir.mkdir()

    excel_path = data_dir / "friends.xlsx"
    db_path = data_dir / "chat_history.db"
    log_path = logs_dir / "bot.log"
    excel_path.write_text("excel")
    db_path.write_text("db")
    log_path.write_text("log")

    monkeypatch.setattr(config, "BACKUP_DIR", str(backup_dir))
    monkeypatch.setattr(config, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(config, "LOGS_DIR", str(logs_dir))
    monkeypatch.setattr(config, "EXCEL_PATH", str(excel_path))
    monkeypatch.setattr(config, "DB_PATH", str(db_path))

    monkeypatch.setattr(auto_backup, "BACKUP_DIR", str(backup_dir))
    monkeypatch.setattr(auto_backup, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(auto_backup, "LOGS_DIR", str(logs_dir))
    monkeypatch.setattr(auto_backup, "EXCEL_PATH", str(excel_path))
    monkeypatch.setattr(auto_backup, "DB_PATH", str(db_path))

    results = []

    async def validator(payload):
        results.append(payload)

    await auto_backup.schedule_auto_backup(interval_seconds=0.1, cycles=1, validator=validator)

    assert results, "备份结果应记录"
    entry = results[0]
    assert (backup_dir / "excel_bak").exists()
    assert (backup_dir / "db_bak").exists()
    assert (backup_dir / "log_bak").exists()
    assert entry["excel"] and Path(entry["excel"]).exists()
    assert entry["db"] and Path(entry["db"]).exists()
    assert entry["logs"] and all(Path(p).exists() for p in entry["logs"])

