"""
關鍵詞監控 API - 管理關鍵詞監控規則和觸發事件
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_current_active_user
from app.models.user import User
from app.models.group_ai import KeywordMonitorRule, KeywordTriggerEvent
from app.api.workers import _add_command, _get_all_workers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/keyword-monitor", tags=["Keyword Monitor"])


# ============ 數據模型 ============

class KeywordMonitorRuleCreate(BaseModel):
    """創建關鍵詞監控規則請求"""
    name: str = Field(..., description="規則名稱")
    keywords: List[str] = Field(..., description="關鍵詞列表")
    group_id: Optional[int] = Field(None, description="監控的群組ID（NULL 表示所有群組）")
    account_id: Optional[str] = Field(None, description="觸發後使用的賬號ID（NULL 表示使用檢測到關鍵詞的賬號）")
    action: str = Field(default="send_private_message", description="觸發動作：send_private_message, send_message, notify")
    action_params: Dict[str, Any] = Field(default_factory=dict, description="動作參數")
    match_mode: str = Field(default="contains", description="匹配模式：contains, exact, regex")
    case_sensitive: bool = Field(default=False, description="是否區分大小寫")
    description: Optional[str] = Field(None, description="規則描述")
    enabled: bool = Field(default=True, description="是否啟用")


class KeywordMonitorRuleUpdate(BaseModel):
    """更新關鍵詞監控規則請求"""
    name: Optional[str] = None
    keywords: Optional[List[str]] = None
    group_id: Optional[int] = None
    account_id: Optional[str] = None
    action: Optional[str] = None
    action_params: Optional[Dict[str, Any]] = None
    match_mode: Optional[str] = None
    case_sensitive: Optional[bool] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


class KeywordMonitorRuleResponse(BaseModel):
    """關鍵詞監控規則響應"""
    id: str
    name: str
    keywords: List[str]
    group_id: Optional[int]
    account_id: Optional[str]
    action: str
    action_params: Dict[str, Any]
    match_mode: str
    case_sensitive: bool
    description: Optional[str]
    enabled: bool
    trigger_count: int
    last_triggered_at: Optional[str]
    created_by: Optional[str]
    created_at: str
    updated_at: str


class KeywordTriggerEventResponse(BaseModel):
    """關鍵詞觸發事件響應"""
    id: str
    rule_id: str
    rule_name: Optional[str]
    account_id: str
    group_id: int
    user_id: int
    message_id: int
    message_text: Optional[str]
    matched_keyword: str
    action_taken: str
    action_result: Dict[str, Any]
    triggered_at: str


# ============ API 端點 ============

@router.post("/rules", status_code=status.HTTP_201_CREATED, response_model=KeywordMonitorRuleResponse)
async def create_keyword_rule(
    rule: KeywordMonitorRuleCreate,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """創建關鍵詞監控規則"""
    try:
        # 驗證關鍵詞列表
        if not rule.keywords or len(rule.keywords) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="關鍵詞列表不能為空"
            )
        
        # 驗證匹配模式
        if rule.match_mode not in ["contains", "exact", "regex"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="匹配模式必須是 contains, exact 或 regex"
            )
        
        # 驗證動作
        valid_actions = ["send_private_message", "send_message", "notify"]
        if rule.action not in valid_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"動作必須是以下之一: {', '.join(valid_actions)}"
            )
        
        # 創建規則
        db_rule = KeywordMonitorRule(
            name=rule.name,
            keywords=rule.keywords,
            group_id=rule.group_id,
            account_id=rule.account_id,
            action=rule.action,
            action_params=rule.action_params,
            match_mode=rule.match_mode,
            case_sensitive=rule.case_sensitive,
            description=rule.description,
            enabled=rule.enabled,
            created_by=current_user.email if current_user else None
        )
        
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        
        logger.info(f"創建關鍵詞監控規則: {db_rule.id} ({db_rule.name})")
        
        return KeywordMonitorRuleResponse(
            id=db_rule.id,
            name=db_rule.name,
            keywords=db_rule.keywords or [],
            group_id=db_rule.group_id,
            account_id=db_rule.account_id,
            action=db_rule.action,
            action_params=db_rule.action_params or {},
            match_mode=db_rule.match_mode,
            case_sensitive=db_rule.case_sensitive,
            description=db_rule.description,
            enabled=db_rule.enabled,
            trigger_count=db_rule.trigger_count,
            last_triggered_at=db_rule.last_triggered_at.isoformat() if db_rule.last_triggered_at else None,
            created_by=db_rule.created_by,
            created_at=db_rule.created_at.isoformat(),
            updated_at=db_rule.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建關鍵詞監控規則失敗: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建規則失敗: {str(e)}"
        )


@router.get("/rules", status_code=status.HTTP_200_OK)
async def list_keyword_rules(
    enabled: Optional[bool] = Query(None, description="篩選啟用狀態"),
    group_id: Optional[int] = Query(None, description="篩選群組ID"),
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """獲取關鍵詞監控規則列表"""
    try:
        query = db.query(KeywordMonitorRule)
        
        if enabled is not None:
            query = query.filter(KeywordMonitorRule.enabled == enabled)
        
        if group_id is not None:
            query = query.filter(
                (KeywordMonitorRule.group_id == group_id) | 
                (KeywordMonitorRule.group_id.is_(None))
            )
        
        rules = query.order_by(KeywordMonitorRule.created_at.desc()).all()
        
        return {
            "success": True,
            "rules": [
                {
                    "id": rule.id,
                    "name": rule.name,
                    "keywords": rule.keywords or [],
                    "group_id": rule.group_id,
                    "account_id": rule.account_id,
                    "action": rule.action,
                    "action_params": rule.action_params or {},
                    "match_mode": rule.match_mode,
                    "case_sensitive": rule.case_sensitive,
                    "description": rule.description,
                    "enabled": rule.enabled,
                    "trigger_count": rule.trigger_count,
                    "last_triggered_at": rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
                    "created_by": rule.created_by,
                    "created_at": rule.created_at.isoformat(),
                    "updated_at": rule.updated_at.isoformat()
                }
                for rule in rules
            ],
            "total": len(rules)
        }
        
    except Exception as e:
        logger.error(f"獲取關鍵詞監控規則列表失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取規則列表失敗: {str(e)}"
        )


@router.get("/rules/{rule_id}", status_code=status.HTTP_200_OK, response_model=KeywordMonitorRuleResponse)
async def get_keyword_rule(
    rule_id: str,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """獲取單個關鍵詞監控規則"""
    try:
        rule = db.query(KeywordMonitorRule).filter(KeywordMonitorRule.id == rule_id).first()
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"規則 {rule_id} 不存在"
            )
        
        return KeywordMonitorRuleResponse(
            id=rule.id,
            name=rule.name,
            keywords=rule.keywords or [],
            group_id=rule.group_id,
            account_id=rule.account_id,
            action=rule.action,
            action_params=rule.action_params or {},
            match_mode=rule.match_mode,
            case_sensitive=rule.case_sensitive,
            description=rule.description,
            enabled=rule.enabled,
            trigger_count=rule.trigger_count,
            last_triggered_at=rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
            created_by=rule.created_by,
            created_at=rule.created_at.isoformat(),
            updated_at=rule.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取關鍵詞監控規則失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取規則失敗: {str(e)}"
        )


@router.put("/rules/{rule_id}", status_code=status.HTTP_200_OK, response_model=KeywordMonitorRuleResponse)
async def update_keyword_rule(
    rule_id: str,
    rule_update: KeywordMonitorRuleUpdate,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """更新關鍵詞監控規則"""
    try:
        rule = db.query(KeywordMonitorRule).filter(KeywordMonitorRule.id == rule_id).first()
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"規則 {rule_id} 不存在"
            )
        
        # 更新字段
        if rule_update.name is not None:
            rule.name = rule_update.name
        if rule_update.keywords is not None:
            rule.keywords = rule_update.keywords
        if rule_update.group_id is not None:
            rule.group_id = rule_update.group_id
        if rule_update.account_id is not None:
            rule.account_id = rule_update.account_id
        if rule_update.action is not None:
            rule.action = rule_update.action
        if rule_update.action_params is not None:
            rule.action_params = rule_update.action_params
        if rule_update.match_mode is not None:
            rule.match_mode = rule_update.match_mode
        if rule_update.case_sensitive is not None:
            rule.case_sensitive = rule_update.case_sensitive
        if rule_update.description is not None:
            rule.description = rule_update.description
        if rule_update.enabled is not None:
            rule.enabled = rule_update.enabled
        
        rule.updated_at = datetime.now()
        
        db.commit()
        db.refresh(rule)
        
        logger.info(f"更新關鍵詞監控規則: {rule_id}")
        
        return KeywordMonitorRuleResponse(
            id=rule.id,
            name=rule.name,
            keywords=rule.keywords or [],
            group_id=rule.group_id,
            account_id=rule.account_id,
            action=rule.action,
            action_params=rule.action_params or {},
            match_mode=rule.match_mode,
            case_sensitive=rule.case_sensitive,
            description=rule.description,
            enabled=rule.enabled,
            trigger_count=rule.trigger_count,
            last_triggered_at=rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
            created_by=rule.created_by,
            created_at=rule.created_at.isoformat(),
            updated_at=rule.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新關鍵詞監控規則失敗: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新規則失敗: {str(e)}"
        )


@router.delete("/rules/{rule_id}", status_code=status.HTTP_200_OK)
async def delete_keyword_rule(
    rule_id: str,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """刪除關鍵詞監控規則"""
    try:
        rule = db.query(KeywordMonitorRule).filter(KeywordMonitorRule.id == rule_id).first()
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"規則 {rule_id} 不存在"
            )
        
        db.delete(rule)
        db.commit()
        
        logger.info(f"刪除關鍵詞監控規則: {rule_id}")
        
        return {
            "success": True,
            "message": f"規則 {rule_id} 已刪除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除關鍵詞監控規則失敗: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除規則失敗: {str(e)}"
        )


@router.get("/events", status_code=status.HTTP_200_OK)
async def list_keyword_events(
    rule_id: Optional[str] = Query(None, description="篩選規則ID"),
    account_id: Optional[str] = Query(None, description="篩選賬號ID"),
    group_id: Optional[int] = Query(None, description="篩選群組ID"),
    limit: int = Query(100, description="返回數量限制"),
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """獲取關鍵詞觸發事件列表"""
    try:
        query = db.query(KeywordTriggerEvent)
        
        if rule_id:
            query = query.filter(KeywordTriggerEvent.rule_id == rule_id)
        if account_id:
            query = query.filter(KeywordTriggerEvent.account_id == account_id)
        if group_id:
            query = query.filter(KeywordTriggerEvent.group_id == group_id)
        
        events = query.order_by(KeywordTriggerEvent.triggered_at.desc()).limit(limit).all()
        
        # 獲取規則名稱
        rule_ids = {event.rule_id for event in events}
        rules = {rule.id: rule.name for rule in db.query(KeywordMonitorRule).filter(KeywordMonitorRule.id.in_(rule_ids)).all()}
        
        return {
            "success": True,
            "events": [
                {
                    "id": event.id,
                    "rule_id": event.rule_id,
                    "rule_name": rules.get(event.rule_id),
                    "account_id": event.account_id,
                    "group_id": event.group_id,
                    "user_id": event.user_id,
                    "message_id": event.message_id,
                    "message_text": event.message_text,
                    "matched_keyword": event.matched_keyword,
                    "action_taken": event.action_taken,
                    "action_result": event.action_result or {},
                    "triggered_at": event.triggered_at.isoformat()
                }
                for event in events
            ],
            "total": len(events)
        }
        
    except Exception as e:
        logger.error(f"獲取關鍵詞觸發事件列表失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取事件列表失敗: {str(e)}"
        )


class KeywordTriggerEventRequest(BaseModel):
    """關鍵詞觸發事件上報請求（Worker 節點調用）"""
    account_id: str = Field(..., description="檢測到關鍵詞的賬號ID")
    group_id: int = Field(..., description="群組ID")
    user_id: int = Field(..., description="發送消息的用戶ID")
    message_id: int = Field(..., description="消息ID")
    message_text: Optional[str] = Field(None, description="消息內容")
    matched_keyword: str = Field(..., description="匹配的關鍵詞")


@router.post("/events/trigger", status_code=status.HTTP_200_OK)
async def report_keyword_trigger(
    event: KeywordTriggerEventRequest,
    db: Session = Depends(get_db_session)
):
    """
    關鍵詞觸發事件上報（Worker 節點調用）
    
    Worker 節點檢測到關鍵詞後，調用此 API 上報事件。
    服務器會根據規則自動執行相應動作（如發送私聊消息）。
    """
    try:
        from app.models.group_ai import GroupAIAccount
        
        # 1. 查找匹配的規則
        # 獲取所有啟用的規則
        rules = db.query(KeywordMonitorRule).filter(
            KeywordMonitorRule.enabled == True
        ).all()
        
        matched_rules = []
        for rule in rules:
            # 檢查群組匹配
            if rule.group_id is not None and rule.group_id != event.group_id:
                continue
            
            # 檢查關鍵詞匹配
            keywords = rule.keywords or []
            if not keywords:
                continue
            
            matched_keyword = None
            message_text = (event.message_text or "").lower() if not rule.case_sensitive else (event.message_text or "")
            
            for keyword in keywords:
                keyword_to_match = keyword.lower() if not rule.case_sensitive else keyword
                
                if rule.match_mode == "contains":
                    if keyword_to_match in message_text:
                        matched_keyword = keyword
                        break
                elif rule.match_mode == "exact":
                    if keyword_to_match == message_text.strip():
                        matched_keyword = keyword
                        break
                elif rule.match_mode == "regex":
                    import re
                    try:
                        if re.search(keyword_to_match, message_text):
                            matched_keyword = keyword
                            break
                    except re.error:
                        logger.warning(f"規則 {rule.id} 的正則表達式無效: {keyword_to_match}")
                        continue
            
            if matched_keyword:
                matched_rules.append((rule, matched_keyword))
        
        if not matched_rules:
            logger.debug(f"未找到匹配的關鍵詞規則 (群組: {event.group_id}, 消息: {event.message_text[:50]})")
            return {
                "success": True,
                "message": "未找到匹配的規則",
                "rules_matched": 0
            }
        
        # 2. 處理每個匹配的規則
        action_results = []
        for rule, matched_keyword in matched_rules:
            try:
                # 記錄事件
                trigger_event = KeywordTriggerEvent(
                    rule_id=rule.id,
                    account_id=event.account_id,
                    group_id=event.group_id,
                    user_id=event.user_id,
                    message_id=event.message_id,
                    message_text=event.message_text,
                    matched_keyword=matched_keyword,
                    action_taken=rule.action,
                    action_result={}
                )
                
                # 執行動作
                action_result = await _execute_keyword_action(
                    rule=rule,
                    account_id=event.account_id,
                    user_id=event.user_id,
                    group_id=event.group_id,
                    matched_keyword=matched_keyword,
                    message_text=event.message_text,
                    db=db
                )
                
                trigger_event.action_result = action_result
                db.add(trigger_event)
                
                # 更新規則統計
                rule.trigger_count += 1
                rule.last_triggered_at = datetime.now()
                
                action_results.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "matched_keyword": matched_keyword,
                    "action": rule.action,
                    "result": action_result
                })
                
                logger.info(f"關鍵詞觸發: 規則 {rule.name} (關鍵詞: {matched_keyword}), 動作: {rule.action}, 結果: {action_result.get('success', False)}")
                
            except Exception as e:
                logger.error(f"處理關鍵詞規則 {rule.id} 失敗: {e}", exc_info=True)
                action_results.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "matched_keyword": matched_keyword,
                    "action": rule.action,
                    "result": {"success": False, "error": str(e)}
                })
        
        db.commit()
        
        return {
            "success": True,
            "message": f"處理了 {len(matched_rules)} 個匹配的規則",
            "rules_matched": len(matched_rules),
            "actions": action_results
        }
        
    except Exception as e:
        logger.error(f"處理關鍵詞觸發事件失敗: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"處理事件失敗: {str(e)}"
        )


async def _execute_keyword_action(
    rule: KeywordMonitorRule,
    account_id: str,
    user_id: int,
    group_id: int,
    matched_keyword: str,
    message_text: Optional[str],
    db: Session
) -> Dict[str, Any]:
    """
    執行關鍵詞觸發動作
    
    Args:
        rule: 關鍵詞監控規則
        account_id: 檢測到關鍵詞的賬號ID
        user_id: 發送消息的用戶ID
        group_id: 群組ID
        matched_keyword: 匹配的關鍵詞
        message_text: 消息內容
        db: 數據庫會話
    
    Returns:
        動作執行結果
    """
    try:
        from app.models.group_ai import GroupAIAccount
        
        # 確定使用的賬號ID
        target_account_id = rule.account_id or account_id
        
        # 獲取賬號信息
        db_account = db.query(GroupAIAccount).filter(
            GroupAIAccount.account_id == target_account_id
        ).first()
        
        if not db_account:
            return {
                "success": False,
                "error": f"賬號 {target_account_id} 不存在"
            }
        
        # 獲取 server_id
        server_id = db_account.server_id
        if not server_id:
            return {
                "success": False,
                "error": f"賬號 {target_account_id} 沒有 server_id"
            }
        
        # 檢查 Worker 節點是否在線
        workers = _get_all_workers()
        target_worker = workers.get(server_id)
        
        if not target_worker or target_worker.get("status") != "online":
            return {
                "success": False,
                "error": f"Worker 節點 {server_id} 不在線"
            }
        
        # 根據動作類型執行
        if rule.action == "send_private_message":
            # 發送私聊消息
            message = rule.action_params.get("message", f"您好！我看到您提到了「{matched_keyword}」，有什麼可以幫助您的嗎？")
            
            # 如果消息中有變量，進行替換
            message = message.replace("{keyword}", matched_keyword)
            message = message.replace("{user_id}", str(user_id))
            
            command = {
                "action": "send_private_message",
                "params": {
                    "account_id": target_account_id,
                    "user_id": user_id,
                    "message": message
                },
                "timestamp": datetime.now().isoformat()
            }
            
            _add_command(server_id, command)
            logger.info(f"發送私聊消息命令到節點 {server_id} (賬號: {target_account_id}, 用戶: {user_id})")
            
            return {
                "success": True,
                "action": "send_private_message",
                "message": "私聊消息命令已發送",
                "server_id": server_id
            }
        
        elif rule.action == "send_message":
            # 發送群組消息
            message = rule.action_params.get("message", f"檢測到關鍵詞「{matched_keyword}」")
            
            message = message.replace("{keyword}", matched_keyword)
            message = message.replace("{user_id}", str(user_id))
            
            command = {
                "action": "send_message",
                "params": {
                    "account_id": target_account_id,
                    "group_id": group_id,
                    "message": message
                },
                "timestamp": datetime.now().isoformat()
            }
            
            _add_command(server_id, command)
            logger.info(f"發送群組消息命令到節點 {server_id} (賬號: {target_account_id}, 群組: {group_id})")
            
            return {
                "success": True,
                "action": "send_message",
                "message": "群組消息命令已發送",
                "server_id": server_id
            }
        
        elif rule.action == "notify":
            # 通知（可以擴展為發送郵件、Webhook 等）
            logger.info(f"關鍵詞觸發通知: 規則 {rule.name}, 關鍵詞 {matched_keyword}, 用戶 {user_id}")
            
            return {
                "success": True,
                "action": "notify",
                "message": "通知已記錄"
            }
        
        else:
            return {
                "success": False,
                "error": f"不支持的動作類型: {rule.action}"
            }
            
    except Exception as e:
        logger.error(f"執行關鍵詞動作失敗: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

