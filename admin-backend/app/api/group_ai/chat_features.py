"""
高級聊天功能 API - 控制人設、劇本、遊戲、排程等功能
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_current_active_user
from app.models.user import User
from app.api.workers import _add_command, _get_all_workers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat-features", tags=["Chat Features"])


# ============ 數據模型 ============

class PersonaConfig(BaseModel):
    """人設配置"""
    persona_id: str = Field(..., description="人設ID")
    name: str = Field(..., description="名字")
    nickname: str = Field(default="", description="暱稱")
    gender: str = Field(default="", description="性別")
    age: int = Field(default=25, description="年齡")
    occupation: str = Field(default="", description="職業")
    personality: str = Field(default="", description="性格")
    speaking_style: str = Field(default="", description="說話風格")
    interests: List[str] = Field(default_factory=list, description="興趣")
    emoji_frequency: str = Field(default="medium", description="表情頻率: low/medium/high")
    active_hours: List[int] = Field(default=[9, 23], description="活躍時段")


class ScheduleTaskConfig(BaseModel):
    """排程任務配置"""
    task_id: str = Field(..., description="任務ID")
    name: str = Field(..., description="任務名稱")
    task_type: str = Field(default="daily", description="類型: once/daily/interval")
    action: str = Field(..., description="動作")
    params: Dict[str, Any] = Field(default_factory=dict, description="參數")
    schedule_time: Optional[str] = Field(None, description="執行時間 (HH:MM)")
    interval_seconds: int = Field(default=0, description="間隔秒數")
    enabled: bool = Field(default=True, description="是否啟用")


class GameConfig(BaseModel):
    """遊戲配置"""
    game_type: str = Field(..., description="遊戲類型: dice/quiz/guess/lucky")
    enabled: bool = Field(default=True, description="是否啟用")
    auto_trigger: bool = Field(default=True, description="自動觸發")
    trigger_after_messages: int = Field(default=10, description="消息數觸發")
    cooldown_minutes: int = Field(default=30, description="冷卻時間(分鐘)")
    bet_amount_min: float = Field(default=10, description="最小金額")
    bet_amount_max: float = Field(default=100, description="最大金額")


class ScriptConfig(BaseModel):
    """劇本配置"""
    script_id: str = Field(..., description="劇本ID")
    name: str = Field(..., description="劇本名稱")
    enabled: bool = Field(default=True, description="是否啟用")
    scenes: List[Dict[str, Any]] = Field(default_factory=list, description="場景列表")


class ChatFeatureSettings(BaseModel):
    """聊天功能總設置"""
    auto_chat_enabled: bool = Field(default=True, description="自動聊天")
    games_enabled: bool = Field(default=True, description="遊戲功能")
    scripts_enabled: bool = Field(default=True, description="劇本功能")
    scheduler_enabled: bool = Field(default=True, description="排程功能")
    analytics_enabled: bool = Field(default=True, description="數據分析")
    chat_interval_min: int = Field(default=30, description="最小聊天間隔(秒)")
    chat_interval_max: int = Field(default=120, description="最大聊天間隔(秒)")
    redpacket_enabled: bool = Field(default=True, description="紅包功能")
    redpacket_interval: int = Field(default=300, description="紅包間隔(秒)")


class StartGameRequest(BaseModel):
    """啟動遊戲請求"""
    game_type: str = Field(..., description="遊戲類型")
    group_id: Optional[int] = Field(None, description="群組ID")


class SendMessageRequest(BaseModel):
    """發送消息請求"""
    group_id: int = Field(..., description="群組ID")
    message: str = Field(..., description="消息內容")
    sender_role: Optional[str] = Field(None, description="發送者角色")


# ============ 預設人設 ============

DEFAULT_PERSONAS = [
    {
        "id": "cheerful_girl",
        "name": "小美",
        "nickname": "美美",
        "gender": "女",
        "age": 23,
        "occupation": "自由職業",
        "personality": "開朗活潑、熱情友善、愛笑愛聊天",
        "speaking_style": "語氣輕鬆活潑，喜歡用疊字和可愛的表達方式",
        "interests": ["美食", "旅行", "追劇", "拍照"],
        "emoji_frequency": "high",
        "avatar": "👧"
    },
    {
        "id": "professional_guy",
        "name": "張明",
        "nickname": "老張",
        "gender": "男",
        "age": 32,
        "occupation": "金融分析師",
        "personality": "理性穩重、專業可靠、言簡意賅",
        "speaking_style": "說話直接有邏輯，偶爾會用專業術語",
        "interests": ["投資", "財經", "運動", "閱讀"],
        "emoji_frequency": "low",
        "avatar": "👨‍💼"
    },
    {
        "id": "funny_brother",
        "name": "阿杰",
        "nickname": "杰哥",
        "gender": "男",
        "age": 27,
        "occupation": "遊戲主播",
        "personality": "搞笑幽默、愛開玩笑、社交達人",
        "speaking_style": "說話誇張有趣，喜歡用網絡用語和梗",
        "interests": ["遊戲", "直播", "美食", "段子"],
        "emoji_frequency": "medium",
        "avatar": "🎮"
    },
    {
        "id": "gentle_sister",
        "name": "小雅",
        "nickname": "雅姐",
        "gender": "女",
        "age": 28,
        "occupation": "心理諮詢師",
        "personality": "溫柔體貼、善解人意、情商很高",
        "speaking_style": "語氣溫和柔軟，會關心他人感受",
        "interests": ["心理學", "瑜伽", "茶藝", "閱讀"],
        "emoji_frequency": "medium",
        "avatar": "👩"
    },
    {
        "id": "tech_geek",
        "name": "小K",
        "nickname": "K神",
        "gender": "男",
        "age": 25,
        "occupation": "程序員",
        "personality": "技術宅、話不多但很有料、偶爾會冷幽默",
        "speaking_style": "說話簡潔，偶爾會說一些技術詞彙",
        "interests": ["編程", "數碼", "科技", "動漫"],
        "emoji_frequency": "low",
        "avatar": "🤓"
    },
    {
        "id": "enthusiastic_auntie",
        "name": "王姐",
        "nickname": "熱心王姐",
        "gender": "女",
        "age": 45,
        "occupation": "社區工作者",
        "personality": "熱心腸、愛管閒事、消息靈通",
        "speaking_style": "說話親切熱情，喜歡關心別人的生活",
        "interests": ["養生", "八卦", "做飯", "跳廣場舞"],
        "emoji_frequency": "medium",
        "avatar": "👩‍🦱"
    }
]

# ============ 預設排程任務 ============

DEFAULT_SCHEDULES = [
    {
        "id": "morning_greeting",
        "name": "早安問候",
        "task_type": "daily",
        "action": "send_greeting",
        "schedule_time": "09:00",
        "params": {"messages": ["早上好呀！☀️", "早安各位！💪", "大家早~"]},
        "enabled": True
    },
    {
        "id": "lunch_topic",
        "name": "午餐話題",
        "task_type": "daily",
        "action": "start_topic",
        "schedule_time": "12:00",
        "params": {"topics": ["中午吃什麼？", "午餐時間到！🍜"]},
        "enabled": True
    },
    {
        "id": "afternoon_tea",
        "name": "下午茶時間",
        "task_type": "daily",
        "action": "start_activity",
        "schedule_time": "15:00",
        "params": {"activity": "afternoon_tea"},
        "enabled": True
    },
    {
        "id": "evening_redpacket",
        "name": "晚間紅包",
        "task_type": "daily",
        "action": "send_redpacket_activity",
        "schedule_time": "18:30",
        "params": {"messages": ["晚上福利時間！🧧"]},
        "enabled": True
    },
    {
        "id": "night_chat",
        "name": "晚間閒聊",
        "task_type": "daily",
        "action": "start_topic",
        "schedule_time": "21:00",
        "params": {"topics": ["晚上大家都在幹嘛？", "今天過得怎麼樣？"]},
        "enabled": True
    },
    {
        "id": "goodnight",
        "name": "晚安",
        "task_type": "daily",
        "action": "send_greeting",
        "schedule_time": "23:00",
        "params": {"messages": ["晚安啦！🌙", "明天見！💤"]},
        "enabled": True
    }
]

# ============ 預設遊戲 ============

DEFAULT_GAMES = [
    {
        "type": "dice",
        "name": "骰子遊戲",
        "description": "擲骰子比大小",
        "emoji": "🎲",
        "enabled": True
    },
    {
        "type": "quiz",
        "name": "問答搶答",
        "description": "搶答贏紅包",
        "emoji": "❓",
        "enabled": True
    },
    {
        "type": "guess",
        "name": "猜數字",
        "description": "猜 1-100 的數字",
        "emoji": "🔢",
        "enabled": True
    },
    {
        "type": "lucky",
        "name": "幸運抽獎",
        "description": "隨機抽獎",
        "emoji": "🎰",
        "enabled": True
    }
]


# ============ API 端點 ============

@router.get("/personas", status_code=status.HTTP_200_OK)
async def get_personas(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """獲取所有人設列表"""
    return {
        "success": True,
        "personas": DEFAULT_PERSONAS,
        "total": len(DEFAULT_PERSONAS)
    }


@router.post("/personas", status_code=status.HTTP_200_OK)
async def create_persona(
    config: PersonaConfig,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """創建新人設"""
    # 這裡可以保存到數據庫
    # 目前先廣播到所有節點
    command = {
        "action": "add_persona",
        "params": config.dict(),
        "timestamp": datetime.now().isoformat()
    }
    
    workers = _get_all_workers()
    for node_id in workers:
        _add_command(node_id, command)
    
    return {
        "success": True,
        "message": f"人設 {config.name} 已創建",
        "persona": config.dict()
    }


@router.get("/schedules", status_code=status.HTTP_200_OK)
async def get_schedules(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """獲取排程任務列表"""
    return {
        "success": True,
        "schedules": DEFAULT_SCHEDULES,
        "total": len(DEFAULT_SCHEDULES)
    }


@router.post("/schedules", status_code=status.HTTP_200_OK)
async def create_schedule(
    config: ScheduleTaskConfig,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """創建排程任務"""
    command = {
        "action": "add_schedule",
        "params": config.dict(),
        "timestamp": datetime.now().isoformat()
    }
    
    workers = _get_all_workers()
    for node_id in workers:
        _add_command(node_id, command)
    
    return {
        "success": True,
        "message": f"任務 {config.name} 已創建",
        "schedule": config.dict()
    }


@router.put("/schedules/{task_id}/toggle", status_code=status.HTTP_200_OK)
async def toggle_schedule(
    task_id: str,
    enabled: bool = True,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """啟用/禁用排程任務"""
    command = {
        "action": "toggle_schedule",
        "params": {"task_id": task_id, "enabled": enabled},
        "timestamp": datetime.now().isoformat()
    }
    
    workers = _get_all_workers()
    for node_id in workers:
        _add_command(node_id, command)
    
    return {
        "success": True,
        "message": f"任務 {task_id} 已{'啟用' if enabled else '禁用'}"
    }


@router.get("/games", status_code=status.HTTP_200_OK)
async def get_games(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """獲取遊戲列表"""
    return {
        "success": True,
        "games": DEFAULT_GAMES,
        "total": len(DEFAULT_GAMES)
    }


@router.post("/games/start", status_code=status.HTTP_200_OK)
async def start_game(
    request: StartGameRequest,
    node_id: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """在指定群組啟動遊戲"""
    command = {
        "action": "start_game",
        "params": {
            "game_type": request.game_type,
            "group_id": request.group_id
        },
        "timestamp": datetime.now().isoformat()
    }
    
    if node_id:
        _add_command(node_id, command)
        target = node_id
    else:
        workers = _get_all_workers()
        for nid in workers:
            _add_command(nid, command)
        target = "all nodes"
    
    return {
        "success": True,
        "message": f"遊戲 {request.game_type} 已發送到 {target}"
    }


@router.get("/settings", status_code=status.HTTP_200_OK)
async def get_settings(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """獲取聊天功能設置"""
    # 默認設置
    settings = {
        "auto_chat_enabled": True,
        "games_enabled": True,
        "scripts_enabled": True,
        "scheduler_enabled": True,
        "analytics_enabled": True,
        "chat_interval_min": 30,
        "chat_interval_max": 120,
        "redpacket_enabled": True,
        "redpacket_interval": 300,
        "emoji_frequency": "medium",
        "response_length": "medium"
    }
    
    return {
        "success": True,
        "settings": settings
    }


@router.put("/settings", status_code=status.HTTP_200_OK)
async def update_settings(
    settings: ChatFeatureSettings,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """更新聊天功能設置"""
    command = {
        "action": "set_config",
        "params": settings.dict(),
        "timestamp": datetime.now().isoformat()
    }
    
    workers = _get_all_workers()
    for node_id in workers:
        _add_command(node_id, command)
    
    return {
        "success": True,
        "message": "設置已更新",
        "settings": settings.dict()
    }


@router.post("/chat/start", status_code=status.HTTP_200_OK)
async def start_chat(
    node_id: Optional[str] = None,
    group_id: Optional[int] = None,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """啟動自動聊天"""
    command = {
        "action": "start_enhanced_chat",
        "params": {"group_id": group_id},
        "timestamp": datetime.now().isoformat()
    }
    
    if node_id:
        _add_command(node_id, command)
        logger.info(f"發送啟動聊天命令到節點 {node_id}")
    else:
        workers = _get_all_workers()
        for nid in workers:
            _add_command(nid, command)
        logger.info(f"發送啟動聊天命令到所有節點")
    
    return {
        "success": True,
        "message": f"聊天已啟動",
        "node_id": node_id or "all",
        "group_id": group_id
    }


@router.post("/chat/stop", status_code=status.HTTP_200_OK)
async def stop_chat(
    node_id: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """停止自動聊天"""
    command = {
        "action": "stop_enhanced_chat",
        "params": {},
        "timestamp": datetime.now().isoformat()
    }
    
    if node_id:
        _add_command(node_id, command)
    else:
        workers = _get_all_workers()
        for nid in workers:
            _add_command(nid, command)
    
    return {
        "success": True,
        "message": f"聊天已停止",
        "node_id": node_id or "all"
    }


@router.post("/chat/start-all-accounts", status_code=status.HTTP_200_OK)
async def start_all_accounts_chat(
    group_id: Optional[int] = None,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """一鍵啟動所有在線賬號的聊天功能"""
    try:
        from app.api.group_ai.accounts import get_service_manager
        from app.models.group_ai import GroupAIAccount
        
        service_manager = get_service_manager()
        if not service_manager:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ServiceManager 未初始化"
            )
        
        # 獲取所有在線賬號（從數據庫和 Worker 節點）
        db_accounts = db.query(GroupAIAccount).filter(
            GroupAIAccount.active == True
        ).all()
        
        # 從 Worker 節點獲取在線賬號列表
        workers = _get_all_workers()
        online_account_ids_from_workers = set()
        for node_id, worker_data in workers.items():
            if worker_data.get("status") == "online":
                accounts = worker_data.get("accounts", [])
                for acc in accounts:
                    if isinstance(acc, dict):
                        account_id = acc.get("account_id") or acc.get("id")
                        if account_id:
                            online_account_ids_from_workers.add(account_id)
        
        # 如果數據庫中有賬號但 Worker 節點中沒有，仍然嘗試啟動
        # 如果 Worker 節點中有賬號但數據庫中沒有，也包含進來
        all_account_ids = set()
        for acc in db_accounts:
            all_account_ids.add(acc.account_id)
        all_account_ids.update(online_account_ids_from_workers)
        
        if not all_account_ids:
            # 提供更詳細的錯誤信息
            total_accounts = db.query(GroupAIAccount).count()
            active_accounts = db.query(GroupAIAccount).filter(GroupAIAccount.active == True).count()
            online_workers = sum(1 for w in workers.values() if w.get("status") == "online")
            
            return {
                "success": False,
                "message": f"沒有找到在線賬號。數據庫中總共有 {total_accounts} 個賬號，其中 {active_accounts} 個標記為活躍，{online_workers} 個 Worker 節點在線。請確保：1) 賬號已標記為活躍(active=True)，2) Worker 節點正在運行並已同步賬號。",
                "accounts_started": 0,
                "accounts_total": 0,
                "diagnostics": {
                    "total_accounts_in_db": total_accounts,
                    "active_accounts_in_db": active_accounts,
                    "online_workers": online_workers,
                    "online_accounts_from_workers": len(online_account_ids_from_workers)
                }
            }
        
        # 使用所有找到的賬號 ID，優先使用數據庫中的賬號信息
        accounts_to_start = []
        for account_id in all_account_ids:
            db_account = next((acc for acc in db_accounts if acc.account_id == account_id), None)
            if db_account:
                accounts_to_start.append(db_account)
            else:
                # 如果數據庫中沒有，創建一個臨時對象（僅用於發送命令）
                from types import SimpleNamespace
                temp_account = SimpleNamespace()
                temp_account.account_id = account_id
                temp_account.server_id = None  # 不知道服務器ID，發送到所有節點
                accounts_to_start.append(temp_account)
        
        started_count = 0
        failed_accounts = []
        
        # 先啟動所有賬號
        for db_account in accounts_to_start:
            account_id = db_account.account_id
            try:
                server_id = getattr(db_account, 'server_id', None)
                
                # 如果賬號已分配到遠程服務器，不需要在本地啟動，直接發送命令
                if server_id:
                    logger.info(f"賬號 {account_id} 已分配到節點 {server_id}，跳過本地啟動，直接發送命令")
                else:
                    # 檢查賬號是否已在內存中
                    if account_id not in service_manager.account_manager.accounts:
                        # 如果不在內存中，嘗試啟動賬號
                        logger.info(f"賬號 {account_id} 不在內存中，嘗試啟動...")
                        try:
                            success = await service_manager.start_account(account_id)
                            if not success:
                                # 獲取詳細的錯誤信息
                                error_details = []
                                account = service_manager.account_manager.accounts.get(account_id)
                                
                                if not account:
                                    error_details.append("賬號未在 AccountManager 中")
                                else:
                                    # 檢查 session 文件是否存在
                                    from pathlib import Path
                                    session_path = Path(account.config.session_file)
                                    if not session_path.exists():
                                        error_details.append(f"Session 文件不存在: {account.config.session_file}")
                                    
                                    # 檢查賬號狀態
                                    from group_ai_service.models.account import AccountStatusEnum
                                    if account.status == AccountStatusEnum.ERROR:
                                        error_details.append("Telegram 連接失敗（請檢查 session 文件是否有效）")
                                    
                                    if account.error_count > 0:
                                        error_details.append(f"已嘗試 {account.error_count} 次啟動")
                                
                                error_msg = "啟動賬號失敗"
                                if error_details:
                                    error_msg += f": {', '.join(error_details)}"
                                else:
                                    error_msg += "（未知原因，請檢查日誌）"
                                
                                failed_accounts.append({
                                    "account_id": account_id,
                                    "error": error_msg
                                })
                                continue
                        except Exception as e:
                            logger.error(f"啟動賬號 {account_id} 時發生異常: {e}", exc_info=True)
                            failed_accounts.append({
                                "account_id": account_id,
                                "error": f"啟動賬號時發生異常: {str(e)}"
                            })
                            continue
                
                # 啟動聊天功能
                chat_command = {
                    "action": "start_enhanced_chat",
                    "params": {"group_id": group_id, "account_id": account_id},
                    "timestamp": datetime.now().isoformat()
                }
                
                # 發送啟動聊天命令
                if server_id:
                    _add_command(server_id, chat_command)
                    logger.info(f"發送啟動聊天命令到節點 {server_id} (賬號: {account_id})")
                else:
                    # 發送到所有在線節點
                    online_workers = {nid: data for nid, data in workers.items() if data.get("status") == "online"}
                    if online_workers:
                        for nid in online_workers:
                            _add_command(nid, chat_command)
                        logger.info(f"發送啟動聊天命令到所有在線節點 (共 {len(online_workers)} 個) (賬號: {account_id})")
                    else:
                        logger.warning(f"沒有在線的 Worker 節點，無法發送啟動聊天命令 (賬號: {account_id})")
                        failed_accounts.append({
                            "account_id": account_id,
                            "error": "沒有在線的 Worker 節點"
                        })
                        continue
                
                started_count += 1
                logger.info(f"已啟動賬號 {account_id} 的聊天功能")
                
            except Exception as e:
                logger.error(f"啟動賬號 {account_id} 聊天失敗: {e}", exc_info=True)
                failed_accounts.append({
                    "account_id": account_id,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "message": f"已啟動 {started_count}/{len(accounts_to_start)} 個賬號的聊天功能",
            "accounts_started": started_count,
            "accounts_total": len(accounts_to_start),
            "failed_accounts": failed_accounts,
            "group_id": group_id
        }
        
    except Exception as e:
        logger.error(f"一鍵啟動所有賬號聊天失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"啟動失敗: {str(e)}"
        )
    
    return {
        "success": True,
        "message": "聊天已停止"
    }


@router.post("/chat/send", status_code=status.HTTP_200_OK)
async def send_message(
    request: SendMessageRequest,
    node_id: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """手動發送消息"""
    command = {
        "action": "send_message",
        "params": {
            "group_id": request.group_id,
            "message": request.message,
            "sender_role": request.sender_role
        },
        "timestamp": datetime.now().isoformat()
    }
    
    if node_id:
        _add_command(node_id, command)
    else:
        workers = _get_all_workers()
        online = [nid for nid, data in workers.items() if data.get("status") == "online"]
        if online:
            _add_command(online[0], command)
    
    return {
        "success": True,
        "message": "消息已發送"
    }


@router.get("/analytics/summary", status_code=status.HTTP_200_OK)
async def get_analytics_summary(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """獲取數據分析摘要"""
    # 從 Workers 收集數據
    workers = _get_all_workers()
    
    total_accounts = 0
    total_groups = 0
    total_messages = 0
    
    for node_id, data in workers.items():
        accounts = data.get("accounts", [])
        total_accounts += len(accounts)
        
        metadata = data.get("metadata", {})
        total_groups += metadata.get("total_groups", 0)
    
    return {
        "success": True,
        "summary": {
            "total_nodes": len(workers),
            "online_nodes": sum(1 for d in workers.values() if d.get("status") == "online"),
            "total_accounts": total_accounts,
            "total_groups": total_groups,
            "total_messages_today": total_messages,
            "timestamp": datetime.now().isoformat()
        }
    }


@router.get("/analytics/funnel", status_code=status.HTTP_200_OK)
async def get_conversion_funnel(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """獲取轉化漏斗數據"""
    # 模擬數據 - 實際應從數據庫讀取
    funnel = {
        "stages": [
            {"name": "joined", "label": "加入群組", "count": 100, "rate": 100},
            {"name": "first_message", "label": "首次發言", "count": 75, "rate": 75},
            {"name": "active_chat", "label": "活躍聊天", "count": 45, "rate": 60},
            {"name": "game_participated", "label": "參與遊戲", "count": 30, "rate": 66.7},
            {"name": "redpacket_claimed", "label": "搶紅包", "count": 25, "rate": 83.3},
            {"name": "converted", "label": "轉化", "count": 12, "rate": 48},
        ],
        "overall_conversion": 12,
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "success": True,
        "funnel": funnel
    }


@router.get("/user-profiles", status_code=status.HTTP_200_OK)
async def get_user_profiles(
    limit: int = 50,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """獲取用戶畫像列表"""
    # 模擬數據
    profiles = [
        {
            "user_id": 123456789,
            "username": "user1",
            "engagement_level": "hot",
            "engagement_score": 85,
            "message_count": 45,
            "interests": ["遊戲", "投資"],
            "main_emotion": "positive",
            "intent": "interested",
            "last_active": datetime.now().isoformat()
        },
        {
            "user_id": 987654321,
            "username": "user2",
            "engagement_level": "warm",
            "engagement_score": 55,
            "message_count": 23,
            "interests": ["美食", "旅行"],
            "main_emotion": "curious",
            "intent": "seeking_info",
            "last_active": datetime.now().isoformat()
        }
    ]
    
    return {
        "success": True,
        "profiles": profiles,
        "total": len(profiles)
    }


@router.get("/optimization/suggestions", status_code=status.HTTP_200_OK)
async def get_optimization_suggestions(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """獲取優化建議"""
    suggestions = [
        {
            "target": "engagement",
            "current_value": 45,
            "suggestion": "參與度中等，建議增加遊戲活動頻率",
            "actions": [
                {"type": "increase_games", "description": "增加遊戲頻率"},
                {"type": "add_redpackets", "description": "增加紅包活動"}
            ]
        },
        {
            "target": "conversion",
            "current_value": 12,
            "suggestion": "轉化率偏低，建議優化劇本引導",
            "actions": [
                {"type": "optimize_script", "description": "優化轉化劇本"},
                {"type": "personalize", "description": "個性化互動"}
            ]
        }
    ]
    
    return {
        "success": True,
        "suggestions": suggestions,
        "overall_health": "good"
    }


@router.post("/optimization/apply", status_code=status.HTTP_200_OK)
async def apply_optimization(
    action_type: str,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """應用優化建議"""
    command = {
        "action": "apply_optimization",
        "params": {"action_type": action_type},
        "timestamp": datetime.now().isoformat()
    }
    
    workers = _get_all_workers()
    for node_id in workers:
        _add_command(node_id, command)
    
    return {
        "success": True,
        "message": f"優化 {action_type} 已應用"
    }
