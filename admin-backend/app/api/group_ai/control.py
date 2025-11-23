"""
調控 API - 動態調整 AI 賬號行為
"""
import logging
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from group_ai_service import AccountManager
from group_ai_service.models.account import AccountConfig
from app.db import get_db
from app.api.group_ai.accounts import get_service_manager
from group_ai_service.service_manager import ServiceManager
from app.models.group_ai import GroupAIAccount

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Group AI Control"])


class AccountParamsUpdate(BaseModel):
    """賬號參數更新"""
    reply_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="回復頻率 (0-1)")
    redpacket_enabled: Optional[bool] = Field(None, description="是否啟用紅包")
    redpacket_probability: Optional[float] = Field(None, ge=0.0, le=1.0, description="紅包參與概率 (0-1)")
    max_replies_per_hour: Optional[int] = Field(None, ge=0, description="每小時最大回復數")
    min_reply_interval: Optional[int] = Field(None, ge=0, description="最小回復間隔（秒）")
    active: Optional[bool] = Field(None, description="是否激活")
    # 新增：時間段控制
    work_hours_start: Optional[int] = Field(None, ge=0, le=23, description="工作時間開始（小時，0-23）")
    work_hours_end: Optional[int] = Field(None, ge=0, le=23, description="工作時間結束（小時，0-23）")
    work_days: Optional[List[int]] = Field(None, description="工作日（0=週一，6=週日）")
    # 新增：關鍵詞過濾
    keyword_whitelist: Optional[List[str]] = Field(None, description="關鍵詞白名單（僅回復包含這些關鍵詞的消息）")
    keyword_blacklist: Optional[List[str]] = Field(None, description="關鍵詞黑名單（不回復包含這些關鍵詞的消息）")
    # 新增：AI生成參數
    ai_temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="AI溫度參數（0-2）")
    ai_max_tokens: Optional[int] = Field(None, ge=1, le=4000, description="AI最大生成token數")
    # 新增：群組特定設置
    group_specific_settings: Optional[Dict[int, Dict[str, Any]]] = Field(None, description="群組特定設置（群組ID -> 設置）")
    # 新增：優先級控制
    reply_priority: Optional[int] = Field(None, ge=1, le=10, description="回復優先級（1-10，數字越大優先級越高）")
    # 自定義參數
    custom_params: Optional[Dict[str, Any]] = Field(None, description="自定義參數")


class BatchUpdateRequest(BaseModel):
    """批量更新請求"""
    account_ids: List[str] = Field(..., description="賬號 ID 列表")
    params: AccountParamsUpdate = Field(..., description="更新參數")


class ControlResponse(BaseModel):
    """調控響應"""
    account_id: str
    updated_params: Dict[str, Any]
    success: bool
    message: str = ""


@router.put("/accounts/{account_id}/params", response_model=ControlResponse)
async def update_account_params(
    account_id: str,
    params: AccountParamsUpdate,
    db: Session = Depends(get_db),
    service_manager: ServiceManager = Depends(get_service_manager)
):
    """更新賬號參數"""
    try:
        account_manager = service_manager.account_manager
        account = account_manager.accounts.get(account_id)
        
        # 如果不在內存中，檢查數據庫
        if not account:
            db_account = db.query(GroupAIAccount).filter(
                GroupAIAccount.account_id == account_id
            ).first()
            
            if not db_account:
                # 如果賬號不存在，返回錯誤（不能僅憑參數創建賬號，需要 session 文件等信息）
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"賬號 {account_id} 不存在。請先創建賬號後再更新參數。"
                )
            
            # 更新數據庫記錄的基本參數
            updated_params = {}
            
            if params.reply_rate is not None:
                db_account.reply_rate = params.reply_rate
                updated_params["reply_rate"] = params.reply_rate
            if params.redpacket_enabled is not None:
                db_account.redpacket_enabled = params.redpacket_enabled
                updated_params["redpacket_enabled"] = params.redpacket_enabled
            if params.redpacket_probability is not None:
                db_account.redpacket_probability = params.redpacket_probability
                updated_params["redpacket_probability"] = params.redpacket_probability
            if params.max_replies_per_hour is not None:
                db_account.max_replies_per_hour = params.max_replies_per_hour
                updated_params["max_replies_per_hour"] = params.max_replies_per_hour
            if params.min_reply_interval is not None:
                db_account.min_reply_interval = params.min_reply_interval
                updated_params["min_reply_interval"] = params.min_reply_interval
            if params.active is not None:
                db_account.active = params.active
                updated_params["active"] = params.active
            
            # 處理 custom_params（合併更新）
            custom_params = db_account.custom_params if hasattr(db_account, 'custom_params') and db_account.custom_params else {}
            
            # 更新 custom_params 中的各個字段
            if params.work_hours_start is not None:
                custom_params["work_hours_start"] = params.work_hours_start
                updated_params["work_hours_start"] = params.work_hours_start
            
            if params.work_hours_end is not None:
                custom_params["work_hours_end"] = params.work_hours_end
                updated_params["work_hours_end"] = params.work_hours_end
            
            if params.work_days is not None:
                custom_params["work_days"] = params.work_days
                updated_params["work_days"] = params.work_days
            
            if params.keyword_whitelist is not None:
                custom_params["keyword_whitelist"] = params.keyword_whitelist
                updated_params["keyword_whitelist"] = params.keyword_whitelist
            
            if params.keyword_blacklist is not None:
                custom_params["keyword_blacklist"] = params.keyword_blacklist
                updated_params["keyword_blacklist"] = params.keyword_blacklist
            
            if params.ai_temperature is not None:
                custom_params["ai_temperature"] = params.ai_temperature
                updated_params["ai_temperature"] = params.ai_temperature
            
            if params.ai_max_tokens is not None:
                custom_params["ai_max_tokens"] = params.ai_max_tokens
                updated_params["ai_max_tokens"] = params.ai_max_tokens
            
            if params.reply_priority is not None:
                custom_params["reply_priority"] = params.reply_priority
                updated_params["reply_priority"] = params.reply_priority
            
            if params.custom_params is not None:
                custom_params.update(params.custom_params)
                updated_params["custom_params"] = params.custom_params
            
            # 保存 custom_params 到數據庫
            db_account.custom_params = custom_params
            
            db.commit()
            
            logger.info(f"賬號 {account_id} 參數已更新（數據庫）: {updated_params}")
            
            return ControlResponse(
                account_id=account_id,
                updated_params=updated_params,
                success=True,
                message="參數更新成功（已保存到數據庫，賬號未運行）"
            )
        
        updated_params = {}
        
        # 更新基本參數
        if params.reply_rate is not None:
            account.config.reply_rate = params.reply_rate
            updated_params["reply_rate"] = params.reply_rate
        
        if params.redpacket_enabled is not None:
            account.config.redpacket_enabled = params.redpacket_enabled
            updated_params["redpacket_enabled"] = params.redpacket_enabled
        
        if params.redpacket_probability is not None:
            account.config.redpacket_probability = params.redpacket_probability
            updated_params["redpacket_probability"] = params.redpacket_probability
        
        if params.max_replies_per_hour is not None:
            account.config.max_replies_per_hour = params.max_replies_per_hour
            updated_params["max_replies_per_hour"] = params.max_replies_per_hour
        
        if params.min_reply_interval is not None:
            account.config.min_reply_interval = params.min_reply_interval
            updated_params["min_reply_interval"] = params.min_reply_interval
        
        if params.active is not None:
            account.config.active = params.active
            updated_params["active"] = params.active
        
        # 更新新增的控制參數（存儲在custom_params中）
        if params.work_hours_start is not None:
            account.config.custom_params["work_hours_start"] = params.work_hours_start
            updated_params["work_hours_start"] = params.work_hours_start
        
        if params.work_hours_end is not None:
            account.config.custom_params["work_hours_end"] = params.work_hours_end
            updated_params["work_hours_end"] = params.work_hours_end
        
        if params.work_days is not None:
            account.config.custom_params["work_days"] = params.work_days
            updated_params["work_days"] = params.work_days
        
        if params.keyword_whitelist is not None:
            account.config.custom_params["keyword_whitelist"] = params.keyword_whitelist
            updated_params["keyword_whitelist"] = params.keyword_whitelist
        
        if params.keyword_blacklist is not None:
            account.config.custom_params["keyword_blacklist"] = params.keyword_blacklist
            updated_params["keyword_blacklist"] = params.keyword_blacklist
        
        if params.ai_temperature is not None:
            account.config.custom_params["ai_temperature"] = params.ai_temperature
            updated_params["ai_temperature"] = params.ai_temperature
        
        if params.ai_max_tokens is not None:
            account.config.custom_params["ai_max_tokens"] = params.ai_max_tokens
            updated_params["ai_max_tokens"] = params.ai_max_tokens
        
        if params.group_specific_settings is not None:
            account.config.custom_params["group_specific_settings"] = params.group_specific_settings
            updated_params["group_specific_settings"] = params.group_specific_settings
        
        if params.reply_priority is not None:
            account.config.custom_params["reply_priority"] = params.reply_priority
            updated_params["reply_priority"] = params.reply_priority
        
        if params.custom_params is not None:
            account.config.custom_params.update(params.custom_params)
            updated_params["custom_params"] = params.custom_params
        
        logger.info(f"賬號 {account_id} 參數已更新: {updated_params}")
        
        return ControlResponse(
            account_id=account_id,
            updated_params=updated_params,
            success=True,
            message="參數更新成功"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新賬號參數失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新賬號參數失敗: {str(e)}"
        )


@router.post("/batch-update", response_model=List[ControlResponse])
async def batch_update_accounts(
    request: BatchUpdateRequest,
    db: Session = Depends(get_db)
):
    """批量更新賬號參數"""
    try:
        results = []
        
        for account_id in request.account_ids:
            account = account_manager.accounts.get(account_id)
            if not account:
                results.append(ControlResponse(
                    account_id=account_id,
                    updated_params={},
                    success=False,
                    message="賬號不存在"
                ))
                continue
            
            # 更新參數（重用單個更新的邏輯）
            updated_params = {}
            
            if request.params.reply_rate is not None:
                account.config.reply_rate = request.params.reply_rate
                updated_params["reply_rate"] = request.params.reply_rate
            
            if request.params.redpacket_enabled is not None:
                account.config.redpacket_enabled = request.params.redpacket_enabled
                updated_params["redpacket_enabled"] = request.params.redpacket_enabled
            
            if request.params.redpacket_probability is not None:
                account.config.redpacket_probability = request.params.redpacket_probability
                updated_params["redpacket_probability"] = request.params.redpacket_probability
            
            if request.params.max_replies_per_hour is not None:
                account.config.max_replies_per_hour = request.params.max_replies_per_hour
                updated_params["max_replies_per_hour"] = request.params.max_replies_per_hour
            
            if request.params.min_reply_interval is not None:
                account.config.min_reply_interval = request.params.min_reply_interval
                updated_params["min_reply_interval"] = request.params.min_reply_interval
            
            if request.params.active is not None:
                account.config.active = request.params.active
                updated_params["active"] = request.params.active
            
            if request.params.custom_params is not None:
                account.config.custom_params.update(request.params.custom_params)
                updated_params["custom_params"] = request.params.custom_params
            
            results.append(ControlResponse(
                account_id=account_id,
                updated_params=updated_params,
                success=True,
                message="參數更新成功"
            ))
        
        logger.info(f"批量更新完成: {len(results)} 個賬號")
        
        return results
    
    except Exception as e:
        logger.error(f"批量更新失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量更新失敗: {str(e)}"
        )


@router.get("/accounts/{account_id}/params", response_model=Dict[str, Any])
async def get_account_params(
    account_id: str,
    db: Session = Depends(get_db),
    service_manager: ServiceManager = Depends(get_service_manager)
):
    """獲取賬號參數"""
    try:
        account_manager = service_manager.account_manager
        
        # 先從內存中獲取
        account = account_manager.accounts.get(account_id)
        
        if account:
            # 從 AccountManager 獲取參數
            custom_params = account.config.custom_params if hasattr(account.config, 'custom_params') and account.config.custom_params else {}
            return {
                "account_id": account.account_id,
                "reply_rate": account.config.reply_rate,
                "redpacket_enabled": account.config.redpacket_enabled,
                "redpacket_probability": account.config.redpacket_probability,
                "max_replies_per_hour": account.config.max_replies_per_hour,
                "min_reply_interval": account.config.min_reply_interval,
                "active": account.config.active,
                "work_hours_start": custom_params.get("work_hours_start", 9),
                "work_hours_end": custom_params.get("work_hours_end", 18),
                "work_days": custom_params.get("work_days", [0, 1, 2, 3, 4, 5, 6]),
                "keyword_whitelist": custom_params.get("keyword_whitelist", []),
                "keyword_blacklist": custom_params.get("keyword_blacklist", []),
                "ai_temperature": custom_params.get("ai_temperature", 0.7),
                "ai_max_tokens": custom_params.get("ai_max_tokens", 500),
                "reply_priority": custom_params.get("reply_priority", 5),
                "custom_params": custom_params
            }
        
        # 如果不在內存中，嘗試從數據庫加載
        db_account = db.query(GroupAIAccount).filter(
            GroupAIAccount.account_id == account_id
        ).first()
        
        if db_account:
            # 從數據庫構建配置
            custom_params = db_account.custom_params if hasattr(db_account, 'custom_params') and db_account.custom_params else {}
            
            return {
                "account_id": db_account.account_id,
                "reply_rate": db_account.reply_rate if db_account.reply_rate is not None else 0.3,
                "redpacket_enabled": db_account.redpacket_enabled if db_account.redpacket_enabled is not None else True,
                "redpacket_probability": db_account.redpacket_probability if db_account.redpacket_probability is not None else 0.5,
                "max_replies_per_hour": db_account.max_replies_per_hour if db_account.max_replies_per_hour is not None else 50,
                "min_reply_interval": db_account.min_reply_interval if db_account.min_reply_interval is not None else 3,
                "active": db_account.active if db_account.active is not None else True,
                "work_hours_start": custom_params.get("work_hours_start", 9),
                "work_hours_end": custom_params.get("work_hours_end", 18),
                "work_days": custom_params.get("work_days", [0, 1, 2, 3, 4, 5, 6]),
                "keyword_whitelist": custom_params.get("keyword_whitelist", []),
                "keyword_blacklist": custom_params.get("keyword_blacklist", []),
                "ai_temperature": custom_params.get("ai_temperature", 0.7),
                "ai_max_tokens": custom_params.get("ai_max_tokens", 500),
                "reply_priority": custom_params.get("reply_priority", 5),
                "custom_params": custom_params
            }
        
        # 如果都不存在，返回默認參數（而不是 404）
        # 這樣前端可以顯示參數頁面，用戶可以配置並保存（保存時會創建賬號記錄）
        logger.warning(f"賬號 {account_id} 不在 AccountManager 和數據庫中，返回默認參數")
        return {
            "account_id": account_id,
            "reply_rate": 0.3,
            "redpacket_enabled": True,
            "redpacket_probability": 0.5,
            "max_replies_per_hour": 50,
            "min_reply_interval": 3,
            "active": False,
            "work_hours_start": 9,
            "work_hours_end": 18,
            "work_days": [0, 1, 2, 3, 4, 5, 6],
            "keyword_whitelist": [],
            "keyword_blacklist": [],
            "ai_temperature": 0.7,
            "ai_max_tokens": 500,
            "reply_priority": 5,
            "custom_params": {}
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取賬號參數失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取賬號參數失敗: {str(e)}"
        )
