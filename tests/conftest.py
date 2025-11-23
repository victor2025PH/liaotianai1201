import asyncio
import os
from pathlib import Path
from typing import AsyncIterator, Dict, List

import pandas as pd
import pytest

import config
from utils import db_manager


@pytest.fixture()
def temp_env(tmp_path, monkeypatch):
    db_path = tmp_path / "test_chat_history.db"
    excel_path = tmp_path / "friends.xlsx"
    monkeypatch.setattr(config, "DB_PATH", str(db_path))
    monkeypatch.setattr(config, "EXCEL_PATH", str(excel_path))
    monkeypatch.setattr(db_manager, "DB_PATH", str(db_path))
    db_manager.auto_init_db()
    yield {"db_path": db_path, "excel_path": excel_path}


@pytest.fixture()
def fast_sleep(monkeypatch):
    async def _noop(*_args, **_kwargs):
        return None

    for target in [
        "utils.friend_greet.async_sleep_with_jitter",
        "utils.friend_auto_add.async_sleep_with_jitter",
        "utils.auto_batch_greet_and_reply.async_sleep_with_jitter",
    ]:
        monkeypatch.setattr(target, _noop)
    yield


class StubChat:
    def __init__(self, chat_id: int, username: str):
        self.id = chat_id
        self.username = username
        self.type = "private"


class StubMessage:
    def __init__(self, chat_id: int, text: str, from_user: bool = True):
        self.chat = StubChat(chat_id, "tester")
        self.text = text
        self.from_user = type("User", (), {"id": chat_id}) if from_user else None


class StubDialog:
    def __init__(self, chat_id: int, username: str, unread: int):
        self.chat = StubChat(chat_id, username)
        self.unread_messages_count = unread


class PyrogramStubClient:
    def __init__(self, dialogs: List[StubDialog], histories: Dict[int, List[StubMessage]]):
        self.sent_messages = []
        self._dialogs = dialogs
        self._histories = histories

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    async def send_message(self, chat_id, text):
        self.sent_messages.append({"chat_id": chat_id, "text": text})

    async def get_dialogs(self) -> AsyncIterator[StubDialog]:
        for dialog in self._dialogs:
            yield dialog

    async def get_chat_history(self, chat_id: int, limit: int = 0):
        return self._histories.get(chat_id, [])

