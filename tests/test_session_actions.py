import asyncio
from unittest.mock import AsyncMock

import pytest

from session_service.actions import SessionAction, SessionActionExecutor
from session_service.dispatch import DispatchManager, DispatchStrategyConfig, RateLimitConfig
from tools.session_manager.account_db import AccountRecord


class DummyPool:
    def __init__(self, client):
        self._client_map = {"+1001": client}

    def get_client(self, phone):
        return self._client_map.get(phone)

    @property
    def client_map(self):
        return self._client_map

    def get_account(self, phone):
        return AccountRecord(
            phone=phone,
            display_name="Host",
            roles=["host"],
            status="ONLINE",
            session_path="sessions/host.session",
            session_string_path=None,
            last_heartbeat_at=None,
        )


@pytest.mark.asyncio
async def test_action_executor_send_message():
    client = AsyncMock()
    pool = DummyPool(client)
    dispatcher = DispatchManager(
        accounts=[pool.get_account("+1001")],
        per_account_limit=RateLimitConfig(max_per_minute=100, burst=10),
        per_group_limit=RateLimitConfig(max_per_minute=100, burst=10),
        strategy_config=DispatchStrategyConfig(mode="round_robin"),
    )
    executor = SessionActionExecutor(pool, dispatcher)
    action = SessionAction(action="send_message", phone="+1001", chat_id=123, text="Hello")
    await executor.execute(action)
    client.send_message.assert_awaited_with(chat_id=123, text="Hello", reply_to_message_id=None)

