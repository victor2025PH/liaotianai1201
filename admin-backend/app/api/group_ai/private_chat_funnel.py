"""
私聊轉化漏斗 API - 自動處理好友請求、私聊培養、定時邀請進群
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from fastapi import APIRouter, HTTPException, status, Depends, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_current_active_user
from app.models.user import User
from app.api.workers import _add_command, _get_all_workers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/private-funnel", tags=["Private Chat Funnel"])


# ============ 數據模型 ============

class UserStage(str, Enum):
    """用戶階段"""
    NEW_FRIEND = "new_friend"           # 剛加好友
    GREETING = "greeting"               # 打招呼階段
    WARMING_UP = "warming_up"           # 升溫階段
    BUILDING_TRUST = "building_trust"   # 建立信任
    READY_TO_INVITE = "ready_to_invite" # 準備邀請
    INVITED = "invited"                 # 已邀請
    JOINED_GROUP = "joined_group"       # 已進群
    CONVERTED = "converted"             # 已轉化


class ChatTopic(str, Enum):
    """聊天話題"""
    GREETING = "greeting"           # 問候
    DAILY_LIFE = "daily_life"       # 日常生活
    INTERESTS = "interests"         # 興趣愛好
    WORK = "work"                   # 工作
    ENTERTAINMENT = "entertainment" # 娛樂
    MONEY = "money"                 # 賺錢/投資
    GAMES = "games"                 # 遊戲
    RED_PACKET = "red_packet"       # 紅包


class PrivateUser(BaseModel):
    """私聊用戶"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    ai_account_id: str = Field(..., description="負責的 AI 賬號")
    stage: UserStage = Field(default=UserStage.NEW_FRIEND)
    added_at: datetime = Field(default_factory=datetime.now)
    last_message_at: Optional[datetime] = None
    message_count: int = Field(default=0)
    ai_message_count: int = Field(default=0)
    current_topic: Optional[ChatTopic] = None
    interests: List[str] = Field(default_factory=list)
    sentiment: str = Field(default="neutral")  # positive/neutral/negative
    invite_scheduled_at: Optional[datetime] = None
    invited_at: Optional[datetime] = None
    joined_group_at: Optional[datetime] = None
    target_group_id: Optional[int] = None
    notes: str = Field(default="")


class FunnelConfig(BaseModel):
    """漏斗配置"""
    enabled: bool = Field(default=True, description="是否啟用私聊轉化")
    auto_accept_friend: bool = Field(default=True, description="自動接受好友請求")
    
    # 聊天配置
    greeting_delay_seconds: int = Field(default=60, description="接受好友後多久發送問候")
    chat_interval_min: int = Field(default=1800, description="主動聊天最小間隔(秒)")
    chat_interval_max: int = Field(default=7200, description="主動聊天最大間隔(秒)")
    daily_message_limit: int = Field(default=10, description="每日主動消息上限")
    reply_delay_min: int = Field(default=3, description="回覆延遲最小(秒)")
    reply_delay_max: int = Field(default=30, description="回覆延遲最大(秒)")
    
    # 邀請配置
    invite_after_days: float = Field(default=3.0, description="幾天後邀請進群")
    min_messages_before_invite: int = Field(default=10, description="邀請前最少消息數")
    invite_message_template: str = Field(
        default="最近群裡在玩紅包遊戲，挺有意思的，要不要一起來玩？",
        description="邀請消息模板"
    )
    
    # 話題進度配置
    topic_progression: List[ChatTopic] = Field(
        default=[
            ChatTopic.GREETING,
            ChatTopic.DAILY_LIFE,
            ChatTopic.INTERESTS,
            ChatTopic.ENTERTAINMENT,
            ChatTopic.GAMES,
            ChatTopic.RED_PACKET,
        ],
        description="話題進度"
    )
    
    # 目標群組
    target_group_ids: List[int] = Field(default_factory=list, description="目標邀請群組")


class StageConfig(BaseModel):
    """階段配置"""
    stage: UserStage
    duration_hours: int = Field(default=24, description="階段持續時間(小時)")
    messages_per_day: int = Field(default=3, description="每天消息數")
    topics: List[ChatTopic] = Field(default_factory=list, description="本階段話題")
    triggers: List[str] = Field(default_factory=list, description="進入下一階段的觸發條件")


class ChatStrategy(BaseModel):
    """聊天策略"""
    strategy_id: str
    name: str
    description: str = ""
    stages: List[StageConfig] = Field(default_factory=list)
    enabled: bool = Field(default=True)


# ============ 預設配置 ============

# 默認階段配置
DEFAULT_STAGE_CONFIGS = [
    {
        "stage": "new_friend",
        "duration_hours": 0,  # 立即進入下一階段
        "messages_per_day": 1,
        "topics": ["greeting"],
        "triggers": ["first_message_sent"]
    },
    {
        "stage": "greeting",
        "duration_hours": 24,
        "messages_per_day": 3,
        "topics": ["greeting", "daily_life"],
        "triggers": ["user_replied", "24_hours_passed"]
    },
    {
        "stage": "warming_up",
        "duration_hours": 24,
        "messages_per_day": 4,
        "topics": ["daily_life", "interests"],
        "triggers": ["positive_sentiment", "24_hours_passed"]
    },
    {
        "stage": "building_trust",
        "duration_hours": 24,
        "messages_per_day": 5,
        "topics": ["interests", "entertainment", "games"],
        "triggers": ["high_engagement", "24_hours_passed"]
    },
    {
        "stage": "ready_to_invite",
        "duration_hours": 0,
        "messages_per_day": 2,
        "topics": ["games", "red_packet"],
        "triggers": ["invite_sent"]
    }
]

# 話題消息模板
TOPIC_MESSAGES = {
    "greeting": [
        "你好呀～很高興認識你 😊",
        "Hi～加個好友，以後多交流呀",
        "哈嘍～你也是{city}的嗎？",
        "終於加上了！之前看到你的頭像就覺得很有緣",
    ],
    "daily_life": [
        "今天過得怎麼樣？",
        "吃飯了嗎？😋",
        "最近忙不忙呀？",
        "這個天氣真的太熱了/冷了 🥵/🥶",
        "週末有什麼安排嗎？",
    ],
    "interests": [
        "平時喜歡做什麼呀？",
        "你有什麼愛好嗎？",
        "我最近迷上了{hobby}，你玩過嗎？",
        "看你朋友圈好像喜歡{interest}？",
    ],
    "entertainment": [
        "最近有什麼好看的劇推薦嗎？",
        "你玩遊戲嗎？",
        "週末一般怎麼放鬆？",
        "有沒有試過線上小遊戲？挺解壓的",
    ],
    "games": [
        "我發現了一個超好玩的遊戲，要不要一起？",
        "最近群裡大家都在玩小遊戲，挺有意思的",
        "你玩過搶紅包遊戲嗎？",
        "我們群裡經常搞遊戲活動，獎品還不錯",
    ],
    "red_packet": [
        "群裡今晚有紅包活動，要不要來試試手氣？🧧",
        "最近群裡紅包雨很多，我都搶了不少 😁",
        "我拉你進群吧，裡面經常有福利活動",
        "群裡有個紅包遊戲，我帶你玩玩？",
    ],
}

# 邀請話術
INVITE_SCRIPTS = [
    {
        "pre_invite": "對了，我有個群，裡面大家經常聊天玩遊戲，氣氛很好",
        "invite": "要不要我拉你進去？認識多點朋友",
        "follow_up": "群裡今晚有紅包活動哦 🧧"
    },
    {
        "pre_invite": "最近群裡在玩一個搶紅包的遊戲，挺刺激的",
        "invite": "我拉你進來一起玩吧？",
        "follow_up": "手氣好的話能搶不少呢"
    },
    {
        "pre_invite": "我們有個小群，經常搞福利活動",
        "invite": "想不想進來看看？",
        "follow_up": "裡面都是聊得來的朋友"
    },
]


# ============ 內存存儲 ============

_funnel_config: Dict[str, Any] = {
    "enabled": True,
    "auto_accept_friend": True,
    "greeting_delay_seconds": 60,
    "chat_interval_min": 1800,
    "chat_interval_max": 7200,
    "daily_message_limit": 10,
    "reply_delay_min": 3,
    "reply_delay_max": 30,
    "invite_after_days": 3.0,
    "min_messages_before_invite": 10,
    "invite_message_template": "最近群裡在玩紅包遊戲，挺有意思的，要不要一起來玩？",
    "target_group_ids": [],
}

_private_users: Dict[int, Dict[str, Any]] = {}  # user_id -> user data
_chat_strategies: List[Dict] = []
_funnel_stats: Dict[str, int] = {
    "total_friends": 0,
    "active_conversations": 0,
    "invites_sent": 0,
    "invites_accepted": 0,
    "conversions": 0,
}


# ============ API 端點 ============

@router.get("/config")
async def get_funnel_config():
    """獲取漏斗配置"""
    return {"success": True, "config": _funnel_config}


@router.put("/config")
async def update_funnel_config(config: FunnelConfig):
    """更新漏斗配置"""
    global _funnel_config
    _funnel_config = config.dict()
    
    # 廣播到所有節點
    command = {
        "action": "set_private_funnel_config",
        "params": _funnel_config,
        "timestamp": datetime.now().isoformat()
    }
    for node_id in _get_all_workers():
        _add_command(node_id, command)
    
    return {"success": True, "message": "配置已更新", "config": _funnel_config}


@router.post("/enable")
async def enable_funnel():
    """啟用私聊轉化"""
    global _funnel_config
    _funnel_config["enabled"] = True
    
    command = {
        "action": "start_private_funnel",
        "params": _funnel_config,
        "timestamp": datetime.now().isoformat()
    }
    for node_id in _get_all_workers():
        _add_command(node_id, command)
    
    return {"success": True, "message": "私聊轉化已啟用"}


@router.post("/disable")
async def disable_funnel():
    """禁用私聊轉化"""
    global _funnel_config
    _funnel_config["enabled"] = False
    
    command = {
        "action": "stop_private_funnel",
        "params": {},
        "timestamp": datetime.now().isoformat()
    }
    for node_id in _get_all_workers():
        _add_command(node_id, command)
    
    return {"success": True, "message": "私聊轉化已禁用"}


@router.get("/users")
async def get_private_users(
    stage: Optional[UserStage] = None,
    limit: int = 50
):
    """獲取私聊用戶列表"""
    users = list(_private_users.values())
    
    if stage:
        users = [u for u in users if u.get("stage") == stage.value]
    
    # 按添加時間倒序
    users.sort(key=lambda x: x.get("added_at", ""), reverse=True)
    
    return {
        "success": True,
        "users": users[:limit],
        "total": len(users),
        "by_stage": {
            stage.value: sum(1 for u in _private_users.values() if u.get("stage") == stage.value)
            for stage in UserStage
        }
    }


@router.get("/users/{user_id}")
async def get_private_user(user_id: int):
    """獲取單個用戶詳情"""
    user = _private_users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    return {"success": True, "user": user}


@router.put("/users/{user_id}/stage")
async def update_user_stage(user_id: int, stage: UserStage):
    """手動更新用戶階段"""
    if user_id not in _private_users:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    _private_users[user_id]["stage"] = stage.value
    
    return {"success": True, "message": f"用戶階段已更新為 {stage.value}"}


@router.post("/users/{user_id}/invite")
async def invite_user_to_group(
    user_id: int,
    group_id: Optional[int] = None,
    node_id: Optional[str] = None
):
    """立即邀請用戶進群"""
    if user_id not in _private_users:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    user = _private_users[user_id]
    target_group = group_id or (_funnel_config.get("target_group_ids") or [None])[0]
    
    if not target_group:
        raise HTTPException(status_code=400, detail="未指定目標群組")
    
    command = {
        "action": "invite_user_to_group",
        "params": {
            "user_id": user_id,
            "group_id": target_group,
            "ai_account_id": user.get("ai_account_id"),
            "invite_message": _funnel_config.get("invite_message_template")
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
    
    # 更新用戶狀態
    _private_users[user_id]["stage"] = UserStage.INVITED.value
    _private_users[user_id]["invited_at"] = datetime.now().isoformat()
    _private_users[user_id]["target_group_id"] = target_group
    _funnel_stats["invites_sent"] += 1
    
    return {"success": True, "message": f"已發送邀請到群組 {target_group}"}


@router.post("/users/{user_id}/send-message")
async def send_message_to_user(
    user_id: int,
    message: str = Body(..., embed=True),
    node_id: Optional[str] = None
):
    """向用戶發送消息"""
    if user_id not in _private_users:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    user = _private_users[user_id]
    
    command = {
        "action": "send_private_message",
        "params": {
            "user_id": user_id,
            "message": message,
            "ai_account_id": user.get("ai_account_id"),
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
    
    return {"success": True, "message": "消息已發送"}


@router.get("/stats")
async def get_funnel_stats():
    """獲取漏斗統計"""
    # 計算各階段用戶數
    stage_counts = {stage.value: 0 for stage in UserStage}
    for user in _private_users.values():
        stage = user.get("stage", "new_friend")
        if stage in stage_counts:
            stage_counts[stage] += 1
    
    # 計算轉化率
    total = len(_private_users)
    invited = _funnel_stats.get("invites_sent", 0)
    joined = sum(1 for u in _private_users.values() if u.get("stage") == "joined_group")
    
    return {
        "success": True,
        "stats": {
            "total_friends": total,
            "by_stage": stage_counts,
            "invites_sent": invited,
            "invites_accepted": joined,
            "invite_rate": round(invited / total * 100, 1) if total > 0 else 0,
            "join_rate": round(joined / invited * 100, 1) if invited > 0 else 0,
            "overall_conversion": round(joined / total * 100, 1) if total > 0 else 0,
        },
        "funnel": [
            {"stage": "新好友", "count": stage_counts.get("new_friend", 0)},
            {"stage": "打招呼", "count": stage_counts.get("greeting", 0)},
            {"stage": "升溫中", "count": stage_counts.get("warming_up", 0)},
            {"stage": "建立信任", "count": stage_counts.get("building_trust", 0)},
            {"stage": "準備邀請", "count": stage_counts.get("ready_to_invite", 0)},
            {"stage": "已邀請", "count": stage_counts.get("invited", 0)},
            {"stage": "已進群", "count": stage_counts.get("joined_group", 0)},
            {"stage": "已轉化", "count": stage_counts.get("converted", 0)},
        ]
    }


@router.get("/stages")
async def get_stage_configs():
    """獲取階段配置"""
    return {
        "success": True,
        "stages": DEFAULT_STAGE_CONFIGS,
        "topics": {topic.value: TOPIC_MESSAGES.get(topic.value, []) for topic in ChatTopic}
    }


@router.get("/invite-scripts")
async def get_invite_scripts():
    """獲取邀請話術"""
    return {"success": True, "scripts": INVITE_SCRIPTS}


@router.post("/invite-scripts")
async def add_invite_script(
    pre_invite: str = Body(...),
    invite: str = Body(...),
    follow_up: str = Body(...)
):
    """添加邀請話術"""
    INVITE_SCRIPTS.append({
        "pre_invite": pre_invite,
        "invite": invite,
        "follow_up": follow_up
    })
    return {"success": True, "message": "話術已添加"}


@router.get("/topic-messages/{topic}")
async def get_topic_messages(topic: ChatTopic):
    """獲取話題消息"""
    messages = TOPIC_MESSAGES.get(topic.value, [])
    return {"success": True, "topic": topic.value, "messages": messages}


@router.post("/topic-messages/{topic}")
async def add_topic_message(topic: ChatTopic, message: str = Body(..., embed=True)):
    """添加話題消息"""
    if topic.value not in TOPIC_MESSAGES:
        TOPIC_MESSAGES[topic.value] = []
    TOPIC_MESSAGES[topic.value].append(message)
    return {"success": True, "message": "消息已添加"}


@router.post("/batch-invite")
async def batch_invite_ready_users(
    group_id: Optional[int] = None,
    limit: int = 10
):
    """批量邀請準備好的用戶"""
    ready_users = [
        u for u in _private_users.values()
        if u.get("stage") == UserStage.READY_TO_INVITE.value
    ][:limit]
    
    if not ready_users:
        return {"success": True, "message": "沒有準備好的用戶", "count": 0}
    
    target_group = group_id or (_funnel_config.get("target_group_ids") or [None])[0]
    if not target_group:
        raise HTTPException(status_code=400, detail="未指定目標群組")
    
    invited_count = 0
    for user in ready_users:
        command = {
            "action": "invite_user_to_group",
            "params": {
                "user_id": user.get("user_id"),
                "group_id": target_group,
                "ai_account_id": user.get("ai_account_id"),
                "invite_message": _funnel_config.get("invite_message_template")
            },
            "timestamp": datetime.now().isoformat()
        }
        
        workers = _get_all_workers()
        online = [nid for nid, data in workers.items() if data.get("status") == "online"]
        if online:
            _add_command(online[0], command)
            user["stage"] = UserStage.INVITED.value
            user["invited_at"] = datetime.now().isoformat()
            invited_count += 1
    
    _funnel_stats["invites_sent"] += invited_count
    
    return {"success": True, "message": f"已邀請 {invited_count} 個用戶", "count": invited_count}


@router.post("/simulate-add-friend")
async def simulate_add_friend(
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    ai_account_id: str = "default_ai"
):
    """模擬用戶添加好友（用於測試）"""
    global _private_users
    
    _private_users[user_id] = {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "ai_account_id": ai_account_id,
        "stage": UserStage.NEW_FRIEND.value,
        "added_at": datetime.now().isoformat(),
        "last_message_at": None,
        "message_count": 0,
        "ai_message_count": 0,
        "current_topic": ChatTopic.GREETING.value,
        "interests": [],
        "sentiment": "neutral",
        "invite_scheduled_at": (datetime.now() + timedelta(days=_funnel_config.get("invite_after_days", 3))).isoformat(),
        "invited_at": None,
        "joined_group_at": None,
        "target_group_id": None,
        "notes": ""
    }
    
    _funnel_stats["total_friends"] += 1
    
    return {
        "success": True,
        "message": f"用戶 {user_id} 已添加",
        "user": _private_users[user_id],
        "invite_scheduled_at": _private_users[user_id]["invite_scheduled_at"]
    }


@router.get("/ready-to-invite")
async def get_ready_to_invite_users():
    """獲取準備邀請的用戶（已達到時間要求）"""
    now = datetime.now()
    invite_days = _funnel_config.get("invite_after_days", 3)
    min_messages = _funnel_config.get("min_messages_before_invite", 10)
    
    ready_users = []
    for user in _private_users.values():
        added_at = datetime.fromisoformat(user.get("added_at", now.isoformat()))
        days_since_added = (now - added_at).total_seconds() / 86400
        message_count = user.get("message_count", 0)
        stage = user.get("stage", "")
        
        # 檢查是否滿足邀請條件
        if (days_since_added >= invite_days and 
            message_count >= min_messages and
            stage not in ["invited", "joined_group", "converted"]):
            ready_users.append({
                **user,
                "days_since_added": round(days_since_added, 1),
                "ready_reason": f"已添加 {round(days_since_added, 1)} 天，已交流 {message_count} 條消息"
            })
    
    return {
        "success": True,
        "users": ready_users,
        "count": len(ready_users),
        "criteria": {
            "invite_after_days": invite_days,
            "min_messages_before_invite": min_messages
        }
    }


@router.post("/set-target-groups")
async def set_target_groups(group_ids: List[int] = Body(...)):
    """設置目標邀請群組"""
    global _funnel_config
    _funnel_config["target_group_ids"] = group_ids
    
    command = {
        "action": "set_funnel_target_groups",
        "params": {"group_ids": group_ids},
        "timestamp": datetime.now().isoformat()
    }
    for node_id in _get_all_workers():
        _add_command(node_id, command)
    
    return {"success": True, "message": f"已設置 {len(group_ids)} 個目標群組", "group_ids": group_ids}


@router.get("/overview")
async def get_funnel_overview():
    """獲取漏斗總覽"""
    now = datetime.now()
    
    # 統計各項數據
    total = len(_private_users)
    today_added = sum(
        1 for u in _private_users.values()
        if datetime.fromisoformat(u.get("added_at", "2000-01-01")).date() == now.date()
    )
    
    active_today = sum(
        1 for u in _private_users.values()
        if u.get("last_message_at") and 
        datetime.fromisoformat(u.get("last_message_at")).date() == now.date()
    )
    
    pending_invite = sum(
        1 for u in _private_users.values()
        if u.get("stage") == UserStage.READY_TO_INVITE.value
    )
    
    return {
        "success": True,
        "overview": {
            "enabled": _funnel_config.get("enabled", True),
            "total_users": total,
            "today_added": today_added,
            "active_today": active_today,
            "pending_invite": pending_invite,
            "invite_after_days": _funnel_config.get("invite_after_days", 3),
            "target_groups": len(_funnel_config.get("target_group_ids", [])),
        }
    }
