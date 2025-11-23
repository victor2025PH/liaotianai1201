import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from session_service.session_pool import SessionClientConfig, SessionClientPool
from tools.session_manager import account_db
from tools.session_manager.account_db import AccountRecord


@pytest.mark.asyncio
async def test_session_pool_start_stop():
    account = AccountRecord(
        phone="+1001",
        display_name="Host",
        roles=["host"],
        status="ONLINE",
        session_path="sessions/host.session",
        session_string_path=None,
        last_heartbeat_at=None,
    )

    async def fake_message_handler(acc, client, message):
        return None

    config = SessionClientConfig(api_id=1, api_hash="hash", message_handler=fake_message_handler)
    pool = SessionClientPool(config=config, accounts=[account])

    with patch("session_service.session_pool.Client", autospec=True) as mock_client_cls, patch.object(
        account_db, "update_status", autospec=True
    ):
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        mock_client.is_connected = False
        mock_client.add_handler = lambda handler: None
        mock_client.remove_handler = lambda handler: None
        mock_client.stop = AsyncMock()

        start_task = asyncio.create_task(pool.start())
        await asyncio.sleep(0.1)
        await pool.stop()
        await asyncio.sleep(0.1)
        start_task.cancel()

        assert mock_client.start.await_count >= 1

