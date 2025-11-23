import asyncio
import json
import logging
from typing import Any, Dict, Optional

from session_service.actions import SessionAction, SessionActionExecutor

logger = logging.getLogger(__name__)


class RedpacketEventProcessor:
    def __init__(self, action_executor: SessionActionExecutor) -> None:
        self.action_executor = action_executor

    async def handle_event(self, event: Dict[str, Any]) -> None:
        event_type = event.get("type")
        payload = event.get("payload") or {}
        if event_type == "session.action":
            await self._handle_session_action(payload)
        elif event_type == "redpacket.event":
            await self._handle_redpacket_event(payload)
        else:
            logger.debug("忽略未知事件：%s", event_type)

    async def _handle_session_action(self, payload: Dict[str, Any]) -> None:
        action = SessionAction(
            action=payload.get("action", ""),
            phone=payload.get("phone"),
            chat_id=payload.get("chat_id"),
            text=payload.get("text"),
            message_id=payload.get("reply_to_message_id"),
            metadata=payload.get("metadata"),
        )
        await self.action_executor.execute(action)

    async def _handle_redpacket_event(self, payload: Dict[str, Any]) -> None:
        status = payload.get("status")
        group_id = payload.get("group_id")
        if status == "START":
            announcement = payload.get("announcement") or "紅包即將發放，準備開搶！"
            await self.action_executor.execute(
                SessionAction(
                    action="send_message",
                    phone=payload.get("host_phone"),
                    chat_id=group_id,
                    text=announcement,
                    metadata={"event": payload.get("event_id")},
                )
            )
        elif status == "RESULT":
            summary = payload.get("summary_text")
            if summary:
                await self.action_executor.execute(
                    SessionAction(
                        action="announce_result",
                        phone=payload.get("host_phone"),
                        chat_id=group_id,
                        text=summary,
                        metadata={"event": payload.get("event_id")},
                    )
                )
        elif status == "GRAB":
            await self.action_executor.execute(
                SessionAction(
                    action="grab_redpacket",
                    phone=payload.get("target_phone"),
                    chat_id=group_id,
                    metadata=payload,
                )
            )
        else:
            logger.info("收到未處理的紅包事件狀態：%s", status)

