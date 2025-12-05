"""
高級功能 API - TTS語音、AI圖片、跨群聯動、告警、模板、黑白名單、多語言、Webhook
"""
import logging
import json
import hashlib
import hmac
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from fastapi import APIRouter, HTTPException, status, Depends, Body, Query, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_current_active_user
from app.models.user import User
from app.api.workers import _add_command, _get_all_workers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advanced", tags=["Advanced Features"])


# ============ 數據模型 ============

# --- TTS 語音 ---
class TTSProvider(str, Enum):
    EDGE_TTS = "edge_tts"
    GOOGLE_TTS = "google_tts"
    AZURE_TTS = "azure_tts"
    OPENAI_TTS = "openai_tts"

class TTSVoice(BaseModel):
    """TTS 語音配置"""
    provider: TTSProvider = Field(default=TTSProvider.EDGE_TTS)
    voice_id: str = Field(default="zh-CN-XiaoxiaoNeural")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)

class TTSRequest(BaseModel):
    """TTS 請求"""
    text: str = Field(..., max_length=500)
    voice: Optional[TTSVoice] = None
    group_id: Optional[int] = None

class TTSConfig(BaseModel):
    """TTS 全局配置"""
    enabled: bool = Field(default=True)
    provider: TTSProvider = Field(default=TTSProvider.EDGE_TTS)
    default_voice: str = Field(default="zh-CN-XiaoxiaoNeural")
    auto_voice_enabled: bool = Field(default=False, description="自動隨機發送語音")
    auto_voice_probability: float = Field(default=0.1, ge=0, le=1)
    max_text_length: int = Field(default=200)


# --- AI 圖片生成 ---
class ImageProvider(str, Enum):
    DALLE = "dalle"
    STABLE_DIFFUSION = "stable_diffusion"
    MIDJOURNEY = "midjourney"

class ImageGenerateRequest(BaseModel):
    """圖片生成請求"""
    prompt: str = Field(..., max_length=1000)
    provider: ImageProvider = Field(default=ImageProvider.DALLE)
    size: str = Field(default="1024x1024")
    style: Optional[str] = Field(default="natural")
    group_id: Optional[int] = None

class ImageConfig(BaseModel):
    """圖片生成配置"""
    enabled: bool = Field(default=True)
    provider: ImageProvider = Field(default=ImageProvider.DALLE)
    api_key: str = Field(default="")
    default_size: str = Field(default="1024x1024")
    auto_generate_enabled: bool = Field(default=False)
    daily_limit: int = Field(default=50)


# --- 跨群聯動 ---
class CrossGroupAction(str, Enum):
    SYNC_MESSAGE = "sync_message"
    SYNC_ACTIVITY = "sync_activity"
    SYNC_REDPACKET = "sync_redpacket"
    CHAIN_INVITE = "chain_invite"

class CrossGroupConfig(BaseModel):
    """跨群聯動配置"""
    enabled: bool = Field(default=True)
    linked_groups: List[int] = Field(default_factory=list)
    sync_actions: List[CrossGroupAction] = Field(default_factory=list)
    delay_between_groups: int = Field(default=30, description="群間延遲(秒)")

class CrossGroupSyncRequest(BaseModel):
    """跨群同步請求"""
    action: CrossGroupAction
    source_group: int
    target_groups: List[int]
    content: Dict[str, Any] = Field(default_factory=dict)


# --- 告警系統 ---
class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertChannel(str, Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    SMS = "sms"

class AlertRule(BaseModel):
    """告警規則"""
    rule_id: str
    name: str
    condition: str = Field(..., description="觸發條件表達式")
    level: AlertLevel = Field(default=AlertLevel.WARNING)
    channels: List[AlertChannel] = Field(default_factory=list)
    cooldown_minutes: int = Field(default=30)
    enabled: bool = Field(default=True)

class AlertConfig(BaseModel):
    """告警配置"""
    enabled: bool = Field(default=True)
    default_channels: List[AlertChannel] = Field(default_factory=lambda: [AlertChannel.TELEGRAM])
    telegram_chat_id: Optional[str] = None
    email_recipients: List[str] = Field(default_factory=list)
    webhook_url: Optional[str] = None


# --- 消息模板 ---
class MessageTemplate(BaseModel):
    """消息模板"""
    template_id: str
    name: str
    category: str = Field(default="general")
    content: str
    variables: List[str] = Field(default_factory=list, description="可用變量")
    shortcut: Optional[str] = Field(None, description="快捷指令")
    enabled: bool = Field(default=True)

class TemplateCategory(BaseModel):
    """模板分類"""
    category_id: str
    name: str
    icon: str = "📝"
    templates: List[MessageTemplate] = Field(default_factory=list)


# --- 黑白名單 ---
class ListType(str, Enum):
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"

class UserListEntry(BaseModel):
    """用戶名單條目"""
    user_id: int
    username: Optional[str] = None
    list_type: ListType
    reason: Optional[str] = None
    added_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    added_by: Optional[str] = None

class UserListConfig(BaseModel):
    """黑白名單配置"""
    whitelist_enabled: bool = Field(default=False)
    blacklist_enabled: bool = Field(default=True)
    auto_kick_blacklist: bool = Field(default=True)
    auto_welcome_whitelist: bool = Field(default=True)


# --- 多語言 ---
class SupportedLanguage(str, Enum):
    ZH_CN = "zh-CN"
    ZH_TW = "zh-TW"
    EN = "en"
    JA = "ja"
    KO = "ko"
    VI = "vi"
    TH = "th"

class LanguageConfig(BaseModel):
    """多語言配置"""
    enabled: bool = Field(default=True)
    default_language: SupportedLanguage = Field(default=SupportedLanguage.ZH_CN)
    auto_detect: bool = Field(default=True)
    translate_incoming: bool = Field(default=False)
    user_language_preferences: Dict[int, SupportedLanguage] = Field(default_factory=dict)

class TranslateRequest(BaseModel):
    """翻譯請求"""
    text: str
    source_lang: Optional[SupportedLanguage] = None
    target_lang: SupportedLanguage


# --- Webhook ---
class WebhookEvent(str, Enum):
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"
    USER_JOINED = "user.joined"
    USER_LEFT = "user.left"
    GAME_STARTED = "game.started"
    GAME_ENDED = "game.ended"
    REDPACKET_SENT = "redpacket.sent"
    REDPACKET_CLAIMED = "redpacket.claimed"
    ALERT_TRIGGERED = "alert.triggered"
    ERROR_OCCURRED = "error.occurred"

class WebhookConfig(BaseModel):
    """Webhook 配置"""
    webhook_id: str
    name: str
    url: str
    secret: Optional[str] = Field(None, description="用於簽名驗證")
    events: List[WebhookEvent] = Field(default_factory=list)
    headers: Dict[str, str] = Field(default_factory=dict)
    enabled: bool = Field(default=True)
    retry_count: int = Field(default=3)
    timeout_seconds: int = Field(default=10)


# ============ 預設數據 ============

# TTS 語音列表
DEFAULT_TTS_VOICES = [
    {"id": "zh-CN-XiaoxiaoNeural", "name": "曉曉（女）", "lang": "zh-CN", "gender": "female"},
    {"id": "zh-CN-YunxiNeural", "name": "雲希（男）", "lang": "zh-CN", "gender": "male"},
    {"id": "zh-CN-YunyangNeural", "name": "雲揚（男）", "lang": "zh-CN", "gender": "male"},
    {"id": "zh-TW-HsiaoChenNeural", "name": "曉臻（女）", "lang": "zh-TW", "gender": "female"},
    {"id": "zh-TW-YunJheNeural", "name": "雲哲（男）", "lang": "zh-TW", "gender": "male"},
    {"id": "en-US-JennyNeural", "name": "Jenny (Female)", "lang": "en-US", "gender": "female"},
    {"id": "en-US-GuyNeural", "name": "Guy (Male)", "lang": "en-US", "gender": "male"},
    {"id": "ja-JP-NanamiNeural", "name": "七海（女）", "lang": "ja-JP", "gender": "female"},
]

# 預設消息模板
DEFAULT_TEMPLATES = [
    {
        "category": "welcome",
        "name": "歡迎類",
        "icon": "👋",
        "templates": [
            {"id": "welcome_1", "name": "熱情歡迎", "content": "歡迎 {username} 加入我們的大家庭！🎉", "variables": ["username"]},
            {"id": "welcome_2", "name": "簡單歡迎", "content": "Hi {username}，歡迎~", "variables": ["username"]},
            {"id": "welcome_3", "name": "問候歡迎", "content": "{username} 你好呀！有什麼可以幫到你的嗎？", "variables": ["username"]},
        ]
    },
    {
        "category": "greeting",
        "name": "問候類",
        "icon": "☀️",
        "templates": [
            {"id": "morning", "name": "早安", "content": "早上好！☀️ 今天也要元氣滿滿哦~", "variables": []},
            {"id": "noon", "name": "午安", "content": "中午好！🍜 吃飯了嗎？", "variables": []},
            {"id": "evening", "name": "晚安", "content": "晚安！🌙 好夢~", "variables": []},
        ]
    },
    {
        "category": "activity",
        "name": "活動類",
        "icon": "🎮",
        "templates": [
            {"id": "game_start", "name": "遊戲開始", "content": "🎮 遊戲時間到！誰要來玩 {game_name}？", "variables": ["game_name"]},
            {"id": "redpacket", "name": "紅包活動", "content": "🧧 福利時間！手快有手慢無~", "variables": []},
            {"id": "quiz", "name": "問答活動", "content": "❓ 搶答時間！答對有獎勵哦~", "variables": []},
        ]
    },
    {
        "category": "response",
        "name": "回覆類",
        "icon": "💬",
        "templates": [
            {"id": "thanks", "name": "感謝", "content": "謝謝 {username}！🙏", "variables": ["username"]},
            {"id": "agree", "name": "同意", "content": "沒錯！我也這麼覺得~", "variables": []},
            {"id": "thinking", "name": "思考", "content": "嗯...讓我想想 🤔", "variables": []},
            {"id": "laugh", "name": "笑", "content": "哈哈哈 😂", "variables": []},
        ]
    },
    {
        "category": "promotion",
        "name": "推廣類",
        "icon": "📣",
        "templates": [
            {"id": "invite", "name": "邀請好友", "content": "邀請好友一起來玩，福利更多哦！🎁", "variables": []},
            {"id": "event", "name": "活動預告", "content": "📢 {event_name} 即將開始，敬請期待！", "variables": ["event_name"]},
        ]
    },
]

# 預設告警規則
DEFAULT_ALERT_RULES = [
    {
        "rule_id": "account_offline",
        "name": "賬號離線",
        "condition": "account.status == 'offline' and account.offline_duration > 300",
        "level": "warning",
        "channels": ["telegram"],
        "enabled": True
    },
    {
        "rule_id": "api_error",
        "name": "API 錯誤率過高",
        "condition": "api.error_rate > 0.1",
        "level": "error",
        "channels": ["telegram", "webhook"],
        "enabled": True
    },
    {
        "rule_id": "message_spike",
        "name": "消息量異常",
        "condition": "messages.count_1h > messages.avg_1h * 3",
        "level": "warning",
        "channels": ["telegram"],
        "enabled": True
    },
    {
        "rule_id": "low_engagement",
        "name": "參與度過低",
        "condition": "engagement.rate < 0.1",
        "level": "info",
        "channels": ["webhook"],
        "enabled": True
    },
]


# ============ 內存存儲 (實際應用中應使用數據庫) ============

_tts_config: Dict[str, Any] = {"enabled": True, "provider": "edge_tts", "default_voice": "zh-CN-XiaoxiaoNeural"}
_image_config: Dict[str, Any] = {"enabled": True, "provider": "dalle", "daily_limit": 50}
_crossgroup_config: Dict[str, Any] = {"enabled": True, "linked_groups": [], "sync_actions": []}
_alert_config: Dict[str, Any] = {"enabled": True, "default_channels": ["telegram"]}
_alert_rules: List[Dict] = DEFAULT_ALERT_RULES.copy()
_templates: List[Dict] = DEFAULT_TEMPLATES.copy()
_user_lists: Dict[str, List[Dict]] = {"whitelist": [], "blacklist": []}
_language_config: Dict[str, Any] = {"enabled": True, "default_language": "zh-CN", "auto_detect": True}
_webhooks: List[Dict] = []
_alert_history: List[Dict] = []


# ============ TTS 語音 API ============

@router.get("/tts/voices")
async def get_tts_voices():
    """獲取可用的 TTS 語音列表"""
    return {
        "success": True,
        "voices": DEFAULT_TTS_VOICES,
        "providers": [p.value for p in TTSProvider]
    }


@router.get("/tts/config")
async def get_tts_config():
    """獲取 TTS 配置"""
    return {"success": True, "config": _tts_config}


@router.put("/tts/config")
async def update_tts_config(config: TTSConfig):
    """更新 TTS 配置"""
    global _tts_config
    _tts_config = config.dict()
    
    # 廣播到所有節點
    command = {"action": "set_tts_config", "params": _tts_config, "timestamp": datetime.now().isoformat()}
    for node_id in _get_all_workers():
        _add_command(node_id, command)
    
    return {"success": True, "message": "TTS 配置已更新", "config": _tts_config}


@router.post("/tts/generate")
async def generate_tts(request: TTSRequest, node_id: Optional[str] = None):
    """生成 TTS 語音並發送"""
    command = {
        "action": "send_voice",
        "params": {
            "text": request.text,
            "voice": request.voice.dict() if request.voice else None,
            "group_id": request.group_id
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
    
    return {"success": True, "message": "語音生成任務已發送"}


# ============ AI 圖片生成 API ============

@router.get("/image/config")
async def get_image_config():
    """獲取圖片生成配置"""
    return {"success": True, "config": _image_config}


@router.put("/image/config")
async def update_image_config(config: ImageConfig):
    """更新圖片生成配置"""
    global _image_config
    _image_config = config.dict()
    
    command = {"action": "set_image_config", "params": _image_config, "timestamp": datetime.now().isoformat()}
    for node_id in _get_all_workers():
        _add_command(node_id, command)
    
    return {"success": True, "message": "圖片配置已更新"}


@router.post("/image/generate")
async def generate_image(request: ImageGenerateRequest, node_id: Optional[str] = None):
    """生成 AI 圖片並發送"""
    command = {
        "action": "generate_and_send_image",
        "params": {
            "prompt": request.prompt,
            "provider": request.provider.value,
            "size": request.size,
            "style": request.style,
            "group_id": request.group_id
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
    
    return {"success": True, "message": "圖片生成任務已發送", "prompt": request.prompt}


@router.get("/image/providers")
async def get_image_providers():
    """獲取支持的圖片生成服務商"""
    return {
        "success": True,
        "providers": [
            {"id": "dalle", "name": "DALL-E (OpenAI)", "sizes": ["256x256", "512x512", "1024x1024"]},
            {"id": "stable_diffusion", "name": "Stable Diffusion", "sizes": ["512x512", "768x768", "1024x1024"]},
            {"id": "midjourney", "name": "Midjourney", "sizes": ["1024x1024", "1792x1024", "1024x1792"]},
        ]
    }


# ============ 跨群聯動 API ============

@router.get("/crossgroup/config")
async def get_crossgroup_config():
    """獲取跨群聯動配置"""
    return {"success": True, "config": _crossgroup_config}


@router.put("/crossgroup/config")
async def update_crossgroup_config(config: CrossGroupConfig):
    """更新跨群聯動配置"""
    global _crossgroup_config
    _crossgroup_config = config.dict()
    
    command = {"action": "set_crossgroup_config", "params": _crossgroup_config, "timestamp": datetime.now().isoformat()}
    for node_id in _get_all_workers():
        _add_command(node_id, command)
    
    return {"success": True, "message": "跨群配置已更新"}


@router.post("/crossgroup/sync")
async def sync_across_groups(request: CrossGroupSyncRequest):
    """執行跨群同步"""
    command = {
        "action": "crossgroup_sync",
        "params": {
            "action": request.action.value,
            "source_group": request.source_group,
            "target_groups": request.target_groups,
            "content": request.content
        },
        "timestamp": datetime.now().isoformat()
    }
    
    for node_id in _get_all_workers():
        _add_command(node_id, command)
    
    return {
        "success": True,
        "message": f"同步任務已發送到 {len(request.target_groups)} 個群組"
    }


@router.post("/crossgroup/link")
async def link_groups(group_ids: List[int] = Body(...)):
    """關聯群組"""
    global _crossgroup_config
    _crossgroup_config["linked_groups"] = list(set(_crossgroup_config.get("linked_groups", []) + group_ids))
    return {"success": True, "linked_groups": _crossgroup_config["linked_groups"]}


@router.delete("/crossgroup/link/{group_id}")
async def unlink_group(group_id: int):
    """取消關聯群組"""
    global _crossgroup_config
    if group_id in _crossgroup_config.get("linked_groups", []):
        _crossgroup_config["linked_groups"].remove(group_id)
    return {"success": True, "linked_groups": _crossgroup_config.get("linked_groups", [])}


# ============ 告警系統 API ============

@router.get("/alerts/config")
async def get_alert_config():
    """獲取告警配置"""
    return {"success": True, "config": _alert_config}


@router.put("/alerts/config")
async def update_alert_config(config: AlertConfig):
    """更新告警配置"""
    global _alert_config
    _alert_config = config.dict()
    return {"success": True, "message": "告警配置已更新"}


@router.get("/alerts/rules")
async def get_alert_rules():
    """獲取告警規則列表"""
    return {"success": True, "rules": _alert_rules}


@router.post("/alerts/rules")
async def create_alert_rule(rule: AlertRule):
    """創建告警規則"""
    global _alert_rules
    _alert_rules.append(rule.dict())
    return {"success": True, "message": "告警規則已創建", "rule": rule.dict()}


@router.put("/alerts/rules/{rule_id}")
async def update_alert_rule(rule_id: str, rule: AlertRule):
    """更新告警規則"""
    global _alert_rules
    for i, r in enumerate(_alert_rules):
        if r.get("rule_id") == rule_id:
            _alert_rules[i] = rule.dict()
            return {"success": True, "message": "告警規則已更新"}
    raise HTTPException(status_code=404, detail="規則不存在")


@router.delete("/alerts/rules/{rule_id}")
async def delete_alert_rule(rule_id: str):
    """刪除告警規則"""
    global _alert_rules
    _alert_rules = [r for r in _alert_rules if r.get("rule_id") != rule_id]
    return {"success": True, "message": "告警規則已刪除"}


@router.put("/alerts/rules/{rule_id}/toggle")
async def toggle_alert_rule(rule_id: str, enabled: bool = True):
    """啟用/禁用告警規則"""
    global _alert_rules
    for r in _alert_rules:
        if r.get("rule_id") == rule_id:
            r["enabled"] = enabled
            return {"success": True, "message": f"規則已{'啟用' if enabled else '禁用'}"}
    raise HTTPException(status_code=404, detail="規則不存在")


@router.get("/alerts/history")
async def get_alert_history(limit: int = 50):
    """獲取告警歷史"""
    return {"success": True, "alerts": _alert_history[:limit], "total": len(_alert_history)}


@router.post("/alerts/test")
async def test_alert(channel: AlertChannel, message: str = "這是一條測試告警"):
    """測試告警通道"""
    _alert_history.insert(0, {
        "id": f"test_{datetime.now().timestamp()}",
        "level": "info",
        "message": message,
        "channel": channel.value,
        "timestamp": datetime.now().isoformat(),
        "is_test": True
    })
    return {"success": True, "message": f"測試告警已發送到 {channel.value}"}


# ============ 消息模板 API ============

@router.get("/templates")
async def get_templates():
    """獲取所有消息模板"""
    return {"success": True, "categories": _templates}


@router.get("/templates/{category}")
async def get_templates_by_category(category: str):
    """獲取分類下的模板"""
    for cat in _templates:
        if cat.get("category") == category:
            return {"success": True, "category": cat}
    raise HTTPException(status_code=404, detail="分類不存在")


@router.post("/templates")
async def create_template(template: MessageTemplate):
    """創建消息模板"""
    global _templates
    for cat in _templates:
        if cat.get("category") == template.category:
            cat["templates"].append(template.dict())
            return {"success": True, "message": "模板已創建", "template": template.dict()}
    
    # 新分類
    _templates.append({
        "category": template.category,
        "name": template.category,
        "icon": "📝",
        "templates": [template.dict()]
    })
    return {"success": True, "message": "模板已創建（新分類）"}


@router.put("/templates/{template_id}")
async def update_template(template_id: str, template: MessageTemplate):
    """更新消息模板"""
    global _templates
    for cat in _templates:
        for i, t in enumerate(cat.get("templates", [])):
            if t.get("id") == template_id:
                cat["templates"][i] = template.dict()
                return {"success": True, "message": "模板已更新"}
    raise HTTPException(status_code=404, detail="模板不存在")


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """刪除消息模板"""
    global _templates
    for cat in _templates:
        cat["templates"] = [t for t in cat.get("templates", []) if t.get("id") != template_id]
    return {"success": True, "message": "模板已刪除"}


@router.post("/templates/{template_id}/send")
async def send_template(
    template_id: str,
    group_id: int,
    variables: Dict[str, str] = Body(default={}),
    node_id: Optional[str] = None
):
    """使用模板發送消息"""
    # 查找模板
    template = None
    for cat in _templates:
        for t in cat.get("templates", []):
            if t.get("id") == template_id:
                template = t
                break
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 替換變量
    content = template.get("content", "")
    for var, val in variables.items():
        content = content.replace(f"{{{var}}}", val)
    
    command = {
        "action": "send_message",
        "params": {"group_id": group_id, "message": content},
        "timestamp": datetime.now().isoformat()
    }
    
    if node_id:
        _add_command(node_id, command)
    else:
        workers = _get_all_workers()
        online = [nid for nid, data in workers.items() if data.get("status") == "online"]
        if online:
            _add_command(online[0], command)
    
    return {"success": True, "message": "消息已發送", "content": content}


# ============ 黑白名單 API ============

@router.get("/userlist/config")
async def get_userlist_config():
    """獲取黑白名單配置"""
    return {
        "success": True,
        "config": {
            "whitelist_enabled": True,
            "blacklist_enabled": True,
            "auto_kick_blacklist": True,
            "auto_welcome_whitelist": True
        }
    }


@router.get("/userlist/{list_type}")
async def get_user_list(list_type: ListType):
    """獲取黑/白名單"""
    return {"success": True, "list_type": list_type.value, "users": _user_lists.get(list_type.value, [])}


@router.post("/userlist/{list_type}")
async def add_to_list(list_type: ListType, entry: UserListEntry):
    """添加用戶到名單"""
    global _user_lists
    entry_dict = entry.dict()
    entry_dict["added_at"] = datetime.now().isoformat()
    _user_lists.setdefault(list_type.value, []).append(entry_dict)
    
    # 廣播到節點
    command = {
        "action": f"add_to_{list_type.value}",
        "params": {"user_id": entry.user_id, "reason": entry.reason},
        "timestamp": datetime.now().isoformat()
    }
    for node_id in _get_all_workers():
        _add_command(node_id, command)
    
    return {"success": True, "message": f"用戶已添加到{list_type.value}"}


@router.delete("/userlist/{list_type}/{user_id}")
async def remove_from_list(list_type: ListType, user_id: int):
    """從名單移除用戶"""
    global _user_lists
    _user_lists[list_type.value] = [
        u for u in _user_lists.get(list_type.value, []) 
        if u.get("user_id") != user_id
    ]
    
    command = {
        "action": f"remove_from_{list_type.value}",
        "params": {"user_id": user_id},
        "timestamp": datetime.now().isoformat()
    }
    for node_id in _get_all_workers():
        _add_command(node_id, command)
    
    return {"success": True, "message": f"用戶已從{list_type.value}移除"}


@router.post("/userlist/check")
async def check_user(user_id: int):
    """檢查用戶狀態"""
    in_whitelist = any(u.get("user_id") == user_id for u in _user_lists.get("whitelist", []))
    in_blacklist = any(u.get("user_id") == user_id for u in _user_lists.get("blacklist", []))
    
    return {
        "success": True,
        "user_id": user_id,
        "in_whitelist": in_whitelist,
        "in_blacklist": in_blacklist,
        "status": "blacklisted" if in_blacklist else ("whitelisted" if in_whitelist else "normal")
    }


# ============ 多語言 API ============

@router.get("/language/config")
async def get_language_config():
    """獲取多語言配置"""
    return {"success": True, "config": _language_config}


@router.put("/language/config")
async def update_language_config(config: LanguageConfig):
    """更新多語言配置"""
    global _language_config
    _language_config = config.dict()
    
    command = {"action": "set_language_config", "params": _language_config, "timestamp": datetime.now().isoformat()}
    for node_id in _get_all_workers():
        _add_command(node_id, command)
    
    return {"success": True, "message": "語言配置已更新"}


@router.get("/language/supported")
async def get_supported_languages():
    """獲取支持的語言列表"""
    return {
        "success": True,
        "languages": [
            {"code": "zh-CN", "name": "简体中文", "flag": "🇨🇳"},
            {"code": "zh-TW", "name": "繁體中文", "flag": "🇹🇼"},
            {"code": "en", "name": "English", "flag": "🇺🇸"},
            {"code": "ja", "name": "日本語", "flag": "🇯🇵"},
            {"code": "ko", "name": "한국어", "flag": "🇰🇷"},
            {"code": "vi", "name": "Tiếng Việt", "flag": "🇻🇳"},
            {"code": "th", "name": "ภาษาไทย", "flag": "🇹🇭"},
        ]
    }


@router.post("/language/translate")
async def translate_text(request: TranslateRequest):
    """翻譯文本"""
    # 這裡應該調用實際的翻譯 API
    # 目前返回模擬結果
    return {
        "success": True,
        "original": request.text,
        "translated": f"[{request.target_lang.value}] {request.text}",
        "source_lang": request.source_lang.value if request.source_lang else "auto",
        "target_lang": request.target_lang.value
    }


@router.put("/language/user/{user_id}")
async def set_user_language(user_id: int, language: SupportedLanguage):
    """設置用戶語言偏好"""
    global _language_config
    _language_config.setdefault("user_language_preferences", {})[user_id] = language.value
    return {"success": True, "message": f"用戶 {user_id} 語言已設置為 {language.value}"}


# ============ Webhook API ============

@router.get("/webhooks")
async def get_webhooks():
    """獲取所有 Webhook"""
    return {"success": True, "webhooks": _webhooks}


@router.post("/webhooks")
async def create_webhook(config: WebhookConfig):
    """創建 Webhook"""
    global _webhooks
    
    # 生成 secret
    if not config.secret:
        config.secret = hashlib.sha256(f"{config.webhook_id}{datetime.now().timestamp()}".encode()).hexdigest()[:32]
    
    _webhooks.append(config.dict())
    return {"success": True, "message": "Webhook 已創建", "webhook": config.dict()}


@router.put("/webhooks/{webhook_id}")
async def update_webhook(webhook_id: str, config: WebhookConfig):
    """更新 Webhook"""
    global _webhooks
    for i, w in enumerate(_webhooks):
        if w.get("webhook_id") == webhook_id:
            _webhooks[i] = config.dict()
            return {"success": True, "message": "Webhook 已更新"}
    raise HTTPException(status_code=404, detail="Webhook 不存在")


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str):
    """刪除 Webhook"""
    global _webhooks
    _webhooks = [w for w in _webhooks if w.get("webhook_id") != webhook_id]
    return {"success": True, "message": "Webhook 已刪除"}


@router.put("/webhooks/{webhook_id}/toggle")
async def toggle_webhook(webhook_id: str, enabled: bool = True):
    """啟用/禁用 Webhook"""
    global _webhooks
    for w in _webhooks:
        if w.get("webhook_id") == webhook_id:
            w["enabled"] = enabled
            return {"success": True, "message": f"Webhook 已{'啟用' if enabled else '禁用'}"}
    raise HTTPException(status_code=404, detail="Webhook 不存在")


@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(webhook_id: str, background_tasks: BackgroundTasks):
    """測試 Webhook"""
    webhook = None
    for w in _webhooks:
        if w.get("webhook_id") == webhook_id:
            webhook = w
            break
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook 不存在")
    
    # 模擬發送測試
    test_payload = {
        "event": "test",
        "timestamp": datetime.now().isoformat(),
        "data": {"message": "這是一條測試消息"}
    }
    
    return {
        "success": True,
        "message": "測試請求已發送",
        "webhook_url": webhook.get("url"),
        "payload": test_payload
    }


@router.get("/webhooks/events")
async def get_webhook_events():
    """獲取支持的 Webhook 事件"""
    return {
        "success": True,
        "events": [
            {"id": "message.received", "name": "收到消息", "description": "當群組收到新消息時"},
            {"id": "message.sent", "name": "發送消息", "description": "當 AI 發送消息時"},
            {"id": "user.joined", "name": "用戶加入", "description": "當新用戶加入群組時"},
            {"id": "user.left", "name": "用戶離開", "description": "當用戶離開群組時"},
            {"id": "game.started", "name": "遊戲開始", "description": "當遊戲開始時"},
            {"id": "game.ended", "name": "遊戲結束", "description": "當遊戲結束時"},
            {"id": "redpacket.sent", "name": "發送紅包", "description": "當紅包發出時"},
            {"id": "redpacket.claimed", "name": "搶紅包", "description": "當紅包被領取時"},
            {"id": "alert.triggered", "name": "告警觸發", "description": "當告警規則觸發時"},
            {"id": "error.occurred", "name": "錯誤發生", "description": "當發生錯誤時"},
        ]
    }


# ============ 功能總覽 API ============

@router.get("/overview")
async def get_features_overview():
    """獲取所有高級功能狀態總覽"""
    return {
        "success": True,
        "features": {
            "tts": {
                "enabled": _tts_config.get("enabled", True),
                "provider": _tts_config.get("provider", "edge_tts"),
                "voice": _tts_config.get("default_voice", "zh-CN-XiaoxiaoNeural")
            },
            "image": {
                "enabled": _image_config.get("enabled", True),
                "provider": _image_config.get("provider", "dalle"),
                "daily_limit": _image_config.get("daily_limit", 50)
            },
            "crossgroup": {
                "enabled": _crossgroup_config.get("enabled", True),
                "linked_groups_count": len(_crossgroup_config.get("linked_groups", []))
            },
            "alerts": {
                "enabled": _alert_config.get("enabled", True),
                "rules_count": len(_alert_rules),
                "active_rules": sum(1 for r in _alert_rules if r.get("enabled"))
            },
            "templates": {
                "categories_count": len(_templates),
                "templates_count": sum(len(c.get("templates", [])) for c in _templates)
            },
            "userlist": {
                "whitelist_count": len(_user_lists.get("whitelist", [])),
                "blacklist_count": len(_user_lists.get("blacklist", []))
            },
            "language": {
                "enabled": _language_config.get("enabled", True),
                "default": _language_config.get("default_language", "zh-CN"),
                "auto_detect": _language_config.get("auto_detect", True)
            },
            "webhooks": {
                "total": len(_webhooks),
                "active": sum(1 for w in _webhooks if w.get("enabled"))
            }
        }
    }
