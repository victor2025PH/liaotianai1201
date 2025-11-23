import asyncio
import pytest

from session_service.dispatch import (
    DispatchManager,
    DispatchStrategyConfig,
    RateLimitConfig,
)
from tools.session_manager.account_db import AccountRecord


@pytest.fixture
def accounts():
    return [
        AccountRecord(
            phone="+1001",
            display_name="Host",
            roles=["host"],
            status="ONLINE",
            session_path="sessions/host.session",
            session_string_path=None,
            last_heartbeat_at=None,
        ),
        AccountRecord(
            phone="+1002",
            display_name="PlayerA",
            roles=["player"],
            status="ONLINE",
            session_path="sessions/playerA.session",
            session_string_path=None,
            last_heartbeat_at=None,
        ),
        AccountRecord(
            phone="+1003",
            display_name="PlayerB",
            roles=["player"],
            status="ONLINE",
            session_path="sessions/playerB.session",
            session_string_path=None,
            last_heartbeat_at=None,
        ),
    ]


@pytest.mark.asyncio
async def test_round_robin_selection(accounts):
    manager = DispatchManager(
        accounts=accounts,
        per_account_limit=RateLimitConfig(max_per_minute=100, burst=10),
        per_group_limit=RateLimitConfig(max_per_minute=200, burst=20),
        strategy_config=DispatchStrategyConfig(mode="round_robin"),
    )
    results = [manager.select_account(group_id=123).phone for _ in range(5)]
    assert results == ["+1001", "+1002", "+1003", "+1001", "+1002"]


@pytest.mark.asyncio
async def test_host_priority(accounts):
    manager = DispatchManager(
        accounts=accounts,
        per_account_limit=RateLimitConfig(max_per_minute=100, burst=10),
        per_group_limit=RateLimitConfig(max_per_minute=200, burst=20),
        strategy_config=DispatchStrategyConfig(mode="host_priority", host_phones=["+1002", "+9999"]),
    )
    chosen = manager.select_account(group_id=456)
    assert chosen.phone == "+1002"


@pytest.mark.asyncio
async def test_weighted_selection(accounts):
    manager = DispatchManager(
        accounts=accounts,
        per_account_limit=RateLimitConfig(max_per_minute=100, burst=10),
        per_group_limit=RateLimitConfig(max_per_minute=200, burst=20),
        strategy_config=DispatchStrategyConfig(mode="weighted", weights={"+1002": 5, "+1003": 1}),
    )
    phones = [manager.select_account(group_id=789).phone for _ in range(100)]
    assert phones.count("+1002") > phones.count("+1003")


@pytest.mark.asyncio
async def test_rate_limiter_throttling(accounts):
    manager = DispatchManager(
        accounts=accounts[:1],
        per_account_limit=RateLimitConfig(max_per_minute=60, burst=5),
        per_group_limit=RateLimitConfig(max_per_minute=60, burst=5),
        strategy_config=DispatchStrategyConfig(mode="round_robin"),
    )
    account = accounts[0]
    class DummyClient:
        def __init__(self):
            self.calls = 0
            self.messages = []

        async def send_message(self, chat_id, text, reply_to_message_id=None):
            self.calls += 1
            self.messages.append(text)

    client = DummyClient()
    client_map = {account.phone: client}
    await manager.dispatch_send_message(client_map, group_id=1, text="Hello 1")
    await manager.dispatch_send_message(client_map, group_id=1, text="Hello 2")
    await manager.dispatch_send_message(client_map, group_id=1, text="Hello 3")
    assert client.calls == 3
    assert client.messages == ["Hello 1", "Hello 2", "Hello 3"]

