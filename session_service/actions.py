import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from pyrogram.errors import FloodWait

from session_service.dispatch import DispatchManager
from session_service.session_pool import SessionClientPool
from tools.session_manager.account_db import record_event

logger = logging.getLogger(__name__)


@dataclass
class SessionAction:
    action: str
    phone: Optional[str]
    chat_id: int
    text: Optional[str] = None
    message_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionActionExecutor:
    def __init__(self, pool: SessionClientPool, dispatcher: DispatchManager) -> None:
        self.pool = pool
        self.dispatcher = dispatcher

    async def execute(self, action: SessionAction) -> None:
        if action.action == "send_message":
            await self._send_message(action)
        elif action.action == "grab_redpacket":
            await self._grab_redpacket(action)
        elif action.action == "announce_result":
            await self._announce_result(action)
        else:
            logger.warning("未知動作：%s", action.action)

    async def _send_message(self, action: SessionAction) -> None:
        if action.text is None:
            logger.warning("send_message 動作缺少 text")
            return
        if action.phone:
            client = self.pool.get_client(action.phone)
            if not client:
                logger.warning("帳號 %s 尚未初始化客戶端", action.phone)
                return
            await self._safe_send(
                account_phone=action.phone,
                client=client,
                chat_id=action.chat_id,
                text=action.text,
                reply_to=action.message_id,
            )
        else:
            await self.dispatcher.dispatch_send_message(
                client_map=self.pool.client_map,
                group_id=action.chat_id,
                text=action.text,
                reply_to_message_id=action.message_id,
            )

    async def _grab_redpacket(self, action: SessionAction) -> None:
        # TODO: 需依照紅包類型（按鈕 / 小遊戲）實作具體互動，目前僅記錄事件。
        logger.info("帳號 %s 準備搶紅包（尚待實作） metadata=%s", action.phone, action.metadata)
        if action.phone:
            record_event(action.phone, "REDPACKET_ATTEMPT", str(action.metadata))

    async def _announce_result(self, action: SessionAction) -> None:
        # 預設透過 send_message 公布結果
        if not action.text:
            logger.warning("announce_result 缺少 text")
            return
        await self._send_message(action)

    async def _safe_send(
        self,
        account_phone: str,
        client,
        chat_id: int,
        text: str,
        reply_to: Optional[int],
    ) -> None:
        try:
            await client.send_message(chat_id=chat_id, text=text, reply_to_message_id=reply_to)
            record_event(account_phone, "SEND_MESSAGE", f"{chat_id}:{text[:50]}")
        except FloodWait as exc:
            logger.warning("帳號 %s 遭遇 FloodWait：%s 秒", account_phone, exc.value)
            await asyncio.sleep(exc.value)
        except Exception as exc:
            logger.exception("帳號 %s 發送訊息失敗：%s", account_phone, exc)

