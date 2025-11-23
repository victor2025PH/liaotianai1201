import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable, Dict, Iterable, List, Optional, Sequence

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from tools.session_manager.account_db import (
    AccountRecord,
    fetch_account_records,
    update_status,
)

logger = logging.getLogger(__name__)

MessageCallback = Callable[[AccountRecord, Client, Message], Awaitable[None]]


@dataclass
class SessionClientConfig:
    api_id: int
    api_hash: str
    target_group_ids: Optional[Sequence[int]] = None
    message_handler: Optional[MessageCallback] = None
    auto_status: bool = True


class SessionClientPool:
    def __init__(
        self,
        config: SessionClientConfig,
        accounts: Optional[Iterable[AccountRecord]] = None,
    ) -> None:
        self.config = config
        self.accounts: Dict[str, AccountRecord] = {acc.phone: acc for acc in (accounts or [])}
        self._clients: List[Client] = []
        self._client_map: Dict[str, Client] = {}
        self._tasks: List[asyncio.Task] = []
        self._stop_event = asyncio.Event()
        self._handlers = {}

    def load_accounts(
        self,
        roles: Optional[Sequence[str]] = None,
        status_in: Optional[Sequence[str]] = None,
    ) -> None:
        records = fetch_account_records(roles=roles, status_in=status_in)
        self.accounts = {acc.phone: acc for acc in records}

    async def start(self) -> None:
        if not self.accounts:
            logger.warning("SessionClientPool 沒有可啟動的帳號")
            return
        logger.info("準備啟動 %d 個 Session 客戶端", len(self.accounts))
        for account in self.accounts.values():
            task = asyncio.create_task(self._run_client(account), name=f"session-client-{account.phone}")
            self._tasks.append(task)
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def stop(self) -> None:
        self._stop_event.set()
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        await asyncio.gather(*(client.stop() for client in self._clients if client.is_connected))
        self._clients.clear()
        self._client_map.clear()
        logger.info("SessionClientPool 已停止")

    async def _run_client(self, account: AccountRecord) -> None:
        client = self._create_client(account)
        handler = self._build_handler(account)
        try:
            client.add_handler(handler)
            await client.start()
            self._clients.append(client)
            self._client_map[account.phone] = client
            if self.config.auto_status:
                update_status(account.phone, "ONLINE")
            logger.info("Session 帳號 %s 已上線", account.phone)
            await self._stop_event.wait()
        except Exception as exc:
            logger.exception("Session 帳號 %s 啟動失敗：%s", account.phone, exc)
        finally:
            try:
                client.remove_handler(handler)
            except ValueError:
                pass
            if client.is_connected:
                await client.stop()
            self._client_map.pop(account.phone, None)
            if self.config.auto_status:
                update_status(account.phone, "OFFLINE")
            logger.info("Session 帳號 %s 已離線", account.phone)

    def _create_client(self, account: AccountRecord) -> Client:
        session_path = Path(account.session_path)
        session_name = session_path.stem
        workdir = session_path.parent if session_path.parent.name else Path(".")
        kwargs = {}
        if account.session_string_path:
            string_path = Path(account.session_string_path)
            if string_path.exists():
                kwargs["session_string"] = string_path.read_text().strip()
        client = Client(
            name=session_name,
            api_id=self.config.api_id,
            api_hash=self.config.api_hash,
            workdir=str(workdir.resolve()),
            plugins=None,
            **kwargs,
        )
        return client

    def _build_handler(self, account: AccountRecord) -> MessageHandler:
        if account.phone in self._handlers:
            return self._handlers[account.phone]

        async def _on_message(client: Client, message: Message):
            if self.config.target_group_ids and message.chat.id not in self.config.target_group_ids:
                return
            if self.config.message_handler:
                await self.config.message_handler(account, client, message)

        handler = MessageHandler(_on_message, filters=filters.group)
        self._handlers[account.phone] = handler
        return handler

    @property
    def client_map(self) -> Dict[str, Client]:
        return dict(self._client_map)

    def get_client(self, phone: str) -> Optional[Client]:
        return self._client_map.get(phone)

    def get_account(self, phone: str) -> Optional[AccountRecord]:
        return self.accounts.get(phone)


__all__ = [
    "SessionClientConfig",
    "SessionClientPool",
]


