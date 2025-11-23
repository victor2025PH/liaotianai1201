"""
Telegram 告警管理 API
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.services.telegram_alert_service import get_telegram_alert_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/telegram-alerts/stats")
async def get_telegram_alert_stats(
    current_user: User = Depends(get_current_active_user),
):
    """獲取 Telegram 告警統計信息"""
    try:
        service = get_telegram_alert_service()
        stats = service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"獲取 Telegram 告警統計失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取統計失敗: {str(e)}"
        )


@router.post("/telegram-alerts/test")
async def test_telegram_alert(
    chat_id: Optional[str] = Query(None, description="測試 Chat ID（可選）"),
    current_user: User = Depends(get_current_active_user),
):
    """測試 Telegram 告警發送"""
    try:
        service = get_telegram_alert_service()
        
        if not service.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telegram 告警服務未啟用，請配置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID"
            )
        
        # 創建測試告警
        test_alert = {
            "alert_type": "test",
            "alert_level": "info",
            "message": "這是一條測試告警消息",
            "timestamp": "2025-11-19 10:00:00",
            "details": {
                "test": True,
                "user": current_user.email
            }
        }
        
        success = await service.send_alert(test_alert, chat_id=chat_id)
        
        if success:
            return {
                "success": True,
                "message": "測試告警已發送",
                "chat_id": chat_id or service.default_chat_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="發送測試告警失敗，請檢查配置和網絡連接"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"測試 Telegram 告警失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"測試失敗: {str(e)}"
        )

