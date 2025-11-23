"""
游戏系统 Webhook 接收 API
接收游戏系统发送的事件通知
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, status, Body
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/game-webhook", tags=["game-webhook"])


class GameEventRequest(BaseModel):
    """游戏事件请求"""
    event_type: str
    event_id: str
    group_id: int
    game_id: str = None
    timestamp: str
    payload: Dict[str, Any] = {}


@router.post("/events", status_code=status.HTTP_200_OK)
async def receive_game_event(
    request: Request,
    event: GameEventRequest = Body(...)
):
    """
    接收游戏系统事件
    
    事件类型：
    - GAME_START: 游戏开始
    - GAME_END: 游戏结束
    - REDPACKET_SENT: 红包发放
    - REDPACKET_CLAIMED: 红包被领取
    - RESULT_ANNOUNCED: 结果公布
    """
    try:
        # 导入游戏事件处理器
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from group_ai_service.game_api_client import GameEventWebhook
        from group_ai_service.service_manager import ServiceManager
        
        # 获取 ServiceManager 实例
        service_manager = ServiceManager.get_instance()
        
        # 创建 GameEvent 对象
        from datetime import datetime
        from group_ai_service.game_api_client import GameEvent
        
        try:
            # 解析时间戳
            if isinstance(event.timestamp, str):
                timestamp = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
            else:
                timestamp = datetime.now()
        except Exception:
            timestamp = datetime.now()
        
        game_event = GameEvent(
            event_type=event.event_type,
            event_id=event.event_id,
            group_id=event.group_id,
            game_id=event.game_id,
            timestamp=timestamp,
            payload=event.payload
        )
        
        # 直接调用 ServiceManager 的事件处理方法
        if game_event.event_type == "GAME_START":
            await service_manager.handle_game_start(game_event)
        elif game_event.event_type == "REDPACKET_SENT":
            await service_manager.handle_redpacket_sent(game_event)
        elif game_event.event_type == "REDPACKET_CLAIMED":
            await service_manager.handle_redpacket_claimed(game_event)
        elif game_event.event_type == "GAME_END":
            await service_manager.handle_game_end(game_event)
        elif game_event.event_type == "RESULT_ANNOUNCED":
            await service_manager.handle_result_announced(game_event)
        else:
            logger.warning(f"未处理的游戏事件类型: {game_event.event_type}")
        
        return {"success": True, "message": "事件处理成功", "event_id": event.event_id}
        
    except Exception as e:
        logger.exception(f"处理游戏事件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理事件失败: {str(e)}"
        )

