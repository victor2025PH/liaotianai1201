"""
紅包遊戲 API - 對接 Lucky Red 紅包遊戲系統
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_current_active_user
from app.models.user import User
from app.lib.lucky_red_sdk import LuckyRedAIClient, get_lucky_red_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/redpacket", tags=["redpacket"])

# ============ 配置存儲 ============

_redpacket_config = {
    "api_url": "",
    "api_key": "",
    "enabled": False,
    "auto_grab": True,
    "grab_delay_min": 1,
    "grab_delay_max": 5,
    "auto_send": False,
    "send_interval": 300,
    "send_amount_min": 1,
    "send_amount_max": 10,
}

# ============ 請求模型 ============

class RedpacketConfigUpdate(BaseModel):
    """紅包配置更新"""
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    enabled: Optional[bool] = None
    auto_grab: Optional[bool] = None
    grab_delay_min: Optional[int] = None
    grab_delay_max: Optional[int] = None
    auto_send: Optional[bool] = None
    send_interval: Optional[int] = None
    send_amount_min: Optional[float] = None
    send_amount_max: Optional[float] = None


class SendPacketRequest(BaseModel):
    """發送紅包請求"""
    telegram_user_id: int = Field(..., description="發送者 Telegram ID")
    total_amount: float = Field(..., gt=0, description="紅包總金額")
    total_count: int = Field(..., ge=1, le=100, description="紅包份數")
    currency: str = Field(default="usdt", description="幣種")
    packet_type: str = Field(default="random", description="類型: random/equal")
    message: str = Field(default="🤖 AI 紅包", description="祝福語")
    chat_id: Optional[int] = Field(default=None, description="目標群組 ID")
    bomb_number: Optional[int] = Field(default=None, ge=0, le=9, description="炸彈數字")


class ClaimPacketRequest(BaseModel):
    """領取紅包請求"""
    telegram_user_id: int = Field(..., description="領取者 Telegram ID")
    packet_uuid: str = Field(..., description="紅包 UUID")


class TransferRequest(BaseModel):
    """轉帳請求"""
    from_user_id: int = Field(..., description="轉出方 Telegram ID")
    to_user_id: int = Field(..., description="接收方 Telegram ID")
    amount: float = Field(..., gt=0, description="轉帳金額")
    currency: str = Field(default="usdt", description="幣種")
    note: str = Field(default="", description="備註")


# ============ API 端點 ============

@router.get("/config")
async def get_config(
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """獲取紅包配置"""
    # 隱藏敏感信息
    config = _redpacket_config.copy()
    if config.get("api_key"):
        config["api_key"] = config["api_key"][:8] + "..." if len(config["api_key"]) > 8 else "***"
    return {"success": True, "data": config}


@router.post("/config")
async def update_config(
    config: RedpacketConfigUpdate,
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """更新紅包配置"""
    global _redpacket_config
    
    update_data = config.dict(exclude_none=True)
    _redpacket_config.update(update_data)
    
    logger.info(f"紅包配置已更新: {list(update_data.keys())}")
    
    return {
        "success": True,
        "message": "配置已保存",
        "data": {k: v for k, v in _redpacket_config.items() if k != "api_key"}
    }


@router.post("/test-connection")
async def test_connection(
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """測試紅包 API 連接"""
    if not _redpacket_config.get("api_url"):
        raise HTTPException(status_code=400, detail="請先配置 API 地址")
    
    try:
        client = LuckyRedAIClient(
            api_key=_redpacket_config.get("api_key", "test-key"),
            base_url=_redpacket_config["api_url"]
        )
        
        result = client.check_health()
        
        if result.success:
            return {
                "success": True,
                "message": "連接成功",
                "data": result.data
            }
        else:
            return {
                "success": False,
                "message": f"連接失敗: {result.error_message}",
                "error": result.error
            }
    except Exception as e:
        logger.error(f"測試連接失敗: {e}")
        raise HTTPException(status_code=500, detail=f"連接錯誤: {str(e)}")


@router.get("/balance/{telegram_user_id}")
async def get_balance(
    telegram_user_id: int,
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """查詢用戶餘額"""
    client = _get_client()
    result = client.get_balance(telegram_user_id)
    
    if result.success:
        return {"success": True, "data": result.data}
    else:
        raise HTTPException(status_code=400, detail=result.error_message)


@router.get("/profile/{telegram_user_id}")
async def get_profile(
    telegram_user_id: int,
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """獲取用戶資料"""
    client = _get_client()
    result = client.get_profile(telegram_user_id)
    
    if result.success:
        return {"success": True, "data": result.data}
    else:
        raise HTTPException(status_code=400, detail=result.error_message)


@router.post("/send")
async def send_packet(
    request: SendPacketRequest,
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """發送紅包"""
    client = _get_client()
    
    result = client.send_packet(
        telegram_user_id=request.telegram_user_id,
        total_amount=request.total_amount,
        total_count=request.total_count,
        currency=request.currency,
        packet_type=request.packet_type,
        message=request.message,
        chat_id=request.chat_id,
        bomb_number=request.bomb_number
    )
    
    if result.success:
        logger.info(f"紅包已發送: {result.data.get('packet_id')} by user {request.telegram_user_id}")
        return {"success": True, "data": result.data}
    else:
        logger.warning(f"發送紅包失敗: {result.error_message}")
        raise HTTPException(status_code=400, detail=result.error_message)


@router.post("/claim")
async def claim_packet(
    request: ClaimPacketRequest,
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """領取紅包"""
    client = _get_client()
    
    result = client.claim_packet(
        telegram_user_id=request.telegram_user_id,
        packet_uuid=request.packet_uuid
    )
    
    if result.success:
        logger.info(f"紅包已領取: {request.packet_uuid} by user {request.telegram_user_id}, amount: {result.data.get('claimed_amount')}")
        return {"success": True, "data": result.data}
    else:
        logger.warning(f"領取紅包失敗: {result.error_message}")
        raise HTTPException(status_code=400, detail=result.error_message)


@router.get("/packet/{packet_uuid}")
async def get_packet_info(
    packet_uuid: str,
    telegram_user_id: int = 0,
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """獲取紅包詳情"""
    client = _get_client()
    result = client.get_packet_info(telegram_user_id, packet_uuid)
    
    if result.success:
        return {"success": True, "data": result.data}
    else:
        raise HTTPException(status_code=400, detail=result.error_message)


@router.post("/transfer")
async def transfer(
    request: TransferRequest,
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """內部轉帳"""
    client = _get_client()
    
    result = client.transfer(
        from_user_id=request.from_user_id,
        to_user_id=request.to_user_id,
        amount=request.amount,
        currency=request.currency,
        note=request.note
    )
    
    if result.success:
        logger.info(f"轉帳成功: {request.from_user_id} -> {request.to_user_id}, {request.amount} {request.currency}")
        return {"success": True, "data": result.data}
    else:
        logger.warning(f"轉帳失敗: {result.error_message}")
        raise HTTPException(status_code=400, detail=result.error_message)


@router.get("/stats")
async def get_stats(
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """獲取紅包統計（本地統計）"""
    # TODO: 從數據庫讀取統計
    return {
        "success": True,
        "data": {
            "total_sent": 0,
            "total_grabbed": 0,
            "total_amount_sent": 0,
            "total_amount_grabbed": 0,
            "today_sent": 0,
            "today_grabbed": 0,
            "connected": bool(_redpacket_config.get("api_url"))
        }
    }


# ============ 遊戲陪玩 API ============

class StartGameRequest(BaseModel):
    """開始遊戲請求"""
    target_user_id: int = Field(..., description="陪玩對象 Telegram ID")
    ai_player_ids: list[int] = Field(..., description="AI 玩家 Telegram ID 列表")


class GameClaimRequest(BaseModel):
    """遊戲搶紅包請求"""
    target_user_id: int = Field(..., description="遊戲會話用戶 ID")
    packet_uuid: str = Field(..., description="紅包 UUID")
    claimer_id: Optional[int] = Field(default=None, description="指定搶紅包的 AI")


class GameSendRequest(BaseModel):
    """遊戲發紅包請求"""
    target_user_id: int = Field(..., description="遊戲會話用戶 ID")
    sender_id: Optional[int] = Field(default=None, description="指定發紅包的 AI")
    packet_type: str = Field(default="random", description="紅包類型")
    amount: Optional[float] = Field(default=None, description="金額")
    count: Optional[int] = Field(default=None, description="份數")
    bomb_number: Optional[int] = Field(default=None, description="炸彈數字")


@router.post("/game/start")
async def start_game(
    request: StartGameRequest,
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """開始遊戲陪玩會話"""
    from app.services.redpacket_game import get_game_service
    
    service = get_game_service(
        api_key=_redpacket_config.get("api_key", ""),
        api_url=_redpacket_config.get("api_url", "")
    )
    
    try:
        session = await service.start_session(
            target_user_id=request.target_user_id,
            ai_player_ids=request.ai_player_ids
        )
        
        return {
            "success": True,
            "message": f"遊戲會話已開始，{len(session.ai_players)} 個 AI 玩家就緒",
            "data": {
                "target_user_id": request.target_user_id,
                "ai_players": [
                    {"id": p.telegram_id, "name": p.name, "balance": p.balance}
                    for p in session.ai_players
                ]
            }
        }
    except Exception as e:
        logger.error(f"開始遊戲失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/game/claim")
async def game_claim(
    request: GameClaimRequest,
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """AI 搶紅包"""
    from app.services.redpacket_game import get_game_service
    
    service = get_game_service()
    session = service.get_session(request.target_user_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="遊戲會話不存在")
    
    result = await service.claim_packet(
        session=session,
        packet_uuid=request.packet_uuid,
        claimer_id=request.claimer_id
    )
    
    return {"success": result.get("success", False), "data": result}


@router.post("/game/send")
async def game_send(
    request: GameSendRequest,
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """AI 發紅包"""
    from app.services.redpacket_game import get_game_service
    
    service = get_game_service()
    session = service.get_session(request.target_user_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="遊戲會話不存在")
    
    result = await service.send_packet(
        session=session,
        sender_id=request.sender_id,
        packet_type=request.packet_type,
        amount=request.amount,
        count=request.count,
        bomb_number=request.bomb_number
    )
    
    return {"success": result.get("success", False), "data": result}


@router.post("/game/auto-play")
async def game_auto_play(
    target_user_id: int = Body(..., embed=True),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """自動玩一輪遊戲"""
    from app.services.redpacket_game import get_game_service
    
    service = get_game_service()
    session = service.get_session(target_user_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="遊戲會話不存在")
    
    actions = await service.auto_play_round(session)
    
    return {"success": True, "data": {"actions": actions}}


@router.get("/game/session/{target_user_id}")
async def get_game_session(
    target_user_id: int,
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """獲取遊戲會話狀態"""
    from app.services.redpacket_game import get_game_service
    
    service = get_game_service()
    stats = service.get_session_stats(target_user_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="遊戲會話不存在")
    
    return {"success": True, "data": stats}


@router.post("/game/stop")
async def stop_game(
    target_user_id: int = Body(..., embed=True),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """停止遊戲會話"""
    from app.services.redpacket_game import get_game_service
    
    service = get_game_service()
    success = service.stop_session(target_user_id)
    
    if success:
        return {"success": True, "message": "遊戲會話已停止"}
    else:
        raise HTTPException(status_code=404, detail="遊戲會話不存在")


# ============ 輔助函數 ============

def _get_client() -> LuckyRedAIClient:
    """獲取配置好的客戶端"""
    if not _redpacket_config.get("api_url"):
        raise HTTPException(status_code=400, detail="紅包 API 未配置")
    
    return LuckyRedAIClient(
        api_key=_redpacket_config.get("api_key", ""),
        base_url=_redpacket_config["api_url"],
        ai_system_id="liaotian-ai-system"
    )
