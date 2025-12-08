"""
🤖 LLM 智能對話模組
支持：
- OpenAI/Claude API 集成
- 上下文感知對話
- 情緒識別和適應
- 多角色人設管理
- 對話策略優化
"""

import asyncio
import random
import logging
import json
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import os

try:
    import httpx
except ImportError:
    httpx = None

try:
    import openai
except ImportError:
    openai = None

logger = logging.getLogger(__name__)


# ==================== 配置 ====================

class LLMProvider(Enum):
    """LLM 提供商"""
    OPENAI = "openai"
    CLAUDE = "claude"
    LOCAL = "local"  # 本地模型


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: LLMProvider = LLMProvider.OPENAI
    api_key: str = ""
    api_base: str = ""
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.8
    max_tokens: int = 200
    
    # 對話配置
    context_window: int = 10  # 上下文消息數
    response_delay_min: float = 2.0  # 最小回復延遲
    response_delay_max: float = 8.0  # 最大回復延遲
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """從環境變量加載配置"""
        provider_str = os.getenv("LLM_PROVIDER", "openai").lower()
        provider = LLMProvider(provider_str) if provider_str in [p.value for p in LLMProvider] else LLMProvider.OPENAI
        
        return cls(
            provider=provider,
            api_key=os.getenv("OPENAI_API_KEY", os.getenv("LLM_API_KEY", "")),
            api_base=os.getenv("OPENAI_API_BASE", os.getenv("LLM_API_BASE", "")),
            model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.8")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "200")),
        )


# ==================== 情緒識別 ====================

class Emotion(Enum):
    """情緒類型"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    EXCITED = "excited"
    CURIOUS = "curious"
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    SAD = "sad"


class EmotionDetector:
    """情緒檢測器"""
    
    # 情緒關鍵詞映射
    EMOTION_KEYWORDS = {
        Emotion.HAPPY: ["哈哈", "開心", "太好了", "棒", "讚", "😊", "😄", "🎉", "❤️", "好開心"],
        Emotion.EXCITED: ["太棒了", "激動", "興奮", "wow", "哇", "🔥", "💪", "厲害", "絕了"],
        Emotion.CURIOUS: ["為什麼", "怎麼", "什麼", "？", "?", "🤔", "想知道", "好奇"],
        Emotion.CONFUSED: ["不懂", "不明白", "看不懂", "啥意思", "什麼意思", "😅", "confused"],
        Emotion.FRUSTRATED: ["煩", "氣死", "無語", "😤", "😠", "算了", "不玩了"],
        Emotion.SAD: ["難過", "傷心", "😢", "😭", "唉", "慘", "可惜"],
    }
    
    def detect(self, text: str) -> Tuple[Emotion, float]:
        """
        檢測文本情緒
        
        Returns:
            (情緒, 置信度)
        """
        text_lower = text.lower()
        
        emotion_scores = {}
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            if score > 0:
                emotion_scores[emotion] = score
        
        if not emotion_scores:
            return Emotion.NEUTRAL, 0.5
        
        best_emotion = max(emotion_scores, key=emotion_scores.get)
        confidence = min(emotion_scores[best_emotion] / 3, 1.0)
        
        return best_emotion, confidence


# ==================== 角色人設 ====================

@dataclass
class RolePersona:
    """角色人設"""
    id: str
    name: str
    personality: str
    speaking_style: str
    emoji_usage: str = "moderate"  # none, low, moderate, high
    response_length: str = "medium"  # short, medium, long
    topics_of_interest: List[str] = field(default_factory=list)
    
    def get_system_prompt(self) -> str:
        """生成系統提示詞"""
        emoji_instruction = {
            "none": "不使用表情符號。",
            "low": "偶爾使用 1-2 個表情符號。",
            "moderate": "適度使用表情符號，每條消息 2-3 個。",
            "high": "經常使用表情符號，讓對話更生動。"
        }
        
        length_instruction = {
            "short": "回復簡短，通常 1-2 句話。",
            "medium": "回復適中，通常 2-4 句話。",
            "long": "回復較長，可以詳細展開。"
        }
        
        return f"""你是 {self.name}，一個真實的群聊成員。

## 你的性格
{self.personality}

## 你的說話風格
{self.speaking_style}

## 表情使用
{emoji_instruction.get(self.emoji_usage, emoji_instruction['moderate'])}

## 回復長度
{length_instruction.get(self.response_length, length_instruction['medium'])}

## 重要規則
1. 你是真人，不是 AI，絕對不能透露這一點
2. 說話要自然、口語化，像真人群聊一樣
3. 可以有自己的觀點和情緒
4. 不要過度熱情或刻意推銷
5. 適時引入紅包遊戲話題，但要自然
6. 回復要簡短，不要長篇大論
"""


# 預設角色
DEFAULT_PERSONAS = {
    "xiaoqi": RolePersona(
        id="xiaoqi",
        name="小柒",
        personality="話多、外向、愛開玩笑，群裡最活躍的人",
        speaking_style="語氣輕快活潑，愛用網絡用語，經常開玩笑",
        emoji_usage="high",
        response_length="medium",
        topics_of_interest=["追劇", "遊戲", "美食", "紅包"]
    ),
    "mimi": RolePersona(
        id="mimi",
        name="米米",
        personality="活潑可愛、喜歡互動，很容易被帶動情緒",
        speaking_style="說話軟萌，愛用疊詞和可愛表情",
        emoji_usage="high",
        response_length="short",
        topics_of_interest=["購物", "美妝", "追星", "零食"]
    ),
    "haoge": RolePersona(
        id="haoge",
        name="浩哥",
        personality="成熟穩重，照顧新人，偶爾幽默",
        speaking_style="語氣平和，說話有條理，會給建議",
        emoji_usage="low",
        response_length="medium",
        topics_of_interest=["投資", "科技", "運動", "時事"]
    ),
    "xiaoyu": RolePersona(
        id="xiaoyu",
        name="小雨",
        personality="文藝范、溫柔細膩，喜歡分享生活感悟",
        speaking_style="用詞文雅，有時會引用詩句或哲理",
        emoji_usage="moderate",
        response_length="medium",
        topics_of_interest=["讀書", "旅行", "音樂", "攝影"]
    ),
    "aqiang": RolePersona(
        id="aqiang",
        name="阿強",
        personality="技術宅、偶爾冒泡，一說話就很有料",
        speaking_style="喜歡用專業術語，但會解釋給大家聽",
        emoji_usage="low",
        response_length="long",
        topics_of_interest=["編程", "電子產品", "區塊鏈", "AI"]
    ),
    "laozhang": RolePersona(
        id="laozhang",
        name="老張",
        personality="成熟穩重、偶爾幽默，說話有分量",
        speaking_style="語氣沉穩，喜歡總結和給出結論",
        emoji_usage="none",
        response_length="short",
        topics_of_interest=["商業", "管理", "歷史", "人生經驗"]
    ),
}


# ==================== LLM 對話生成器 ====================

class LLMDialogueGenerator:
    """LLM 對話生成器"""
    
    def __init__(self, config: LLMConfig = None):
        self.config = config or LLMConfig.from_env()
        self.emotion_detector = EmotionDetector()
        self.personas = DEFAULT_PERSONAS.copy()
        self.http_client = None
        
        # 對話歷史（每個群組）
        self.conversation_history: Dict[int, List[dict]] = {}
        
        # 用戶畫像
        self.user_profiles: Dict[int, dict] = {}
    
    async def _ensure_client(self):
        """確保 HTTP 客戶端存在"""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def generate_response(
        self,
        group_id: int,
        user_message: str,
        user_id: int,
        user_name: str,
        role_id: str = None,
        context_messages: List[dict] = None
    ) -> Optional[str]:
        """
        生成智能回復
        
        Args:
            group_id: 群組 ID
            user_message: 用戶消息
            user_id: 用戶 ID
            user_name: 用戶名
            role_id: 使用的角色 ID
            context_messages: 上下文消息列表
        
        Returns:
            生成的回復文本
        """
        await self._ensure_client()
        
        # 選擇角色
        if role_id and role_id in self.personas:
            persona = self.personas[role_id]
        else:
            persona = random.choice(list(self.personas.values()))
        
        # 檢測用戶情緒
        emotion, confidence = self.emotion_detector.detect(user_message)
        
        # 構建上下文
        history = self._get_conversation_history(group_id)
        if context_messages:
            history = context_messages[-self.config.context_window:]
        
        # 構建消息
        messages = self._build_messages(
            persona=persona,
            user_message=user_message,
            user_name=user_name,
            emotion=emotion,
            history=history
        )
        
        # 調用 LLM
        try:
            if self.config.provider == LLMProvider.OPENAI:
                response = await self._call_openai(messages)
            elif self.config.provider == LLMProvider.CLAUDE:
                response = await self._call_claude(messages, persona)
            else:
                response = self._generate_fallback(persona, user_message, emotion)
            
            # 後處理
            response = self._post_process(response, persona)
            
            # 記錄到歷史
            self._add_to_history(group_id, user_name, user_message)
            self._add_to_history(group_id, persona.name, response)
            
            return response
            
        except Exception as e:
            logger.error(f"LLM 生成失敗: {e}")
            return self._generate_fallback(persona, user_message, emotion)
    
    def _build_messages(
        self,
        persona: RolePersona,
        user_message: str,
        user_name: str,
        emotion: Emotion,
        history: List[dict]
    ) -> List[dict]:
        """構建 LLM 消息列表"""
        
        # 系統提示
        system_prompt = persona.get_system_prompt()
        
        # 情緒適應指令
        emotion_instructions = {
            Emotion.HAPPY: "用戶心情很好，可以一起開心互動。",
            Emotion.EXCITED: "用戶很興奮，可以一起激動或給予回應。",
            Emotion.CURIOUS: "用戶很好奇，可以給出解答或引導話題。",
            Emotion.CONFUSED: "用戶有些困惑，可以耐心解釋或幫助。",
            Emotion.FRUSTRATED: "用戶有些煩躁，要注意語氣，可以安撫。",
            Emotion.SAD: "用戶心情不好，可以適當關心或轉移話題。",
            Emotion.NEUTRAL: ""
        }
        
        emotion_hint = emotion_instructions.get(emotion, "")
        if emotion_hint:
            system_prompt += f"\n\n## 當前情況\n{emotion_hint}"
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加歷史消息
        for msg in history[-self.config.context_window:]:
            role = "assistant" if msg.get("is_ai") else "user"
            content = f"{msg.get('name', '用戶')}: {msg.get('text', '')}"
            messages.append({"role": role, "content": content})
        
        # 當前消息
        messages.append({
            "role": "user",
            "content": f"{user_name}: {user_message}"
        })
        
        return messages
    
    async def _call_openai(self, messages: List[dict]) -> str:
        """調用 OpenAI API"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        api_base = self.config.api_base or "https://api.openai.com/v1"
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        
        response = await self.http_client.post(
            f"{api_base}/chat/completions",
            headers=headers,
            json=payload
        )
        
        response.raise_for_status()
        data = response.json()
        
        return data["choices"][0]["message"]["content"]
    
    async def _call_claude(self, messages: List[dict], persona: RolePersona) -> str:
        """調用 Claude API"""
        headers = {
            "x-api-key": self.config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        api_base = self.config.api_base or "https://api.anthropic.com/v1"
        
        # 轉換消息格式
        system = messages[0]["content"] if messages else ""
        claude_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in messages[1:]
        ]
        
        payload = {
            "model": self.config.model or "claude-3-sonnet-20240229",
            "max_tokens": self.config.max_tokens,
            "system": system,
            "messages": claude_messages
        }
        
        response = await self.http_client.post(
            f"{api_base}/messages",
            headers=headers,
            json=payload
        )
        
        response.raise_for_status()
        data = response.json()
        
        return data["content"][0]["text"]
    
    def _generate_fallback(
        self,
        persona: RolePersona,
        user_message: str,
        emotion: Emotion
    ) -> str:
        """生成備用回復（無 LLM 時）"""
        
        # 根據角色和情緒選擇回復
        fallback_responses = {
            "xiaoqi": {
                Emotion.NEUTRAL: ["哈哈，有道理！", "對呀對呀～", "這個話題有意思 😄"],
                Emotion.HAPPY: ["太開心了！🎉", "哈哈哈一起嗨！", "心情真好呀～"],
                Emotion.CURIOUS: ["這個我也想知道！", "確實挺好奇的", "有人知道嗎？"],
            },
            "mimi": {
                Emotion.NEUTRAL: ["是呀是呀～", "我也覺得呢 ✨", "嗯嗯！"],
                Emotion.HAPPY: ["好開心呀～ 😊", "太棒啦！", "開心開心 ✨"],
                Emotion.CURIOUS: ["我也想知道呢～", "好奇！", "是什麼呀？"],
            },
            "haoge": {
                Emotion.NEUTRAL: ["說得有道理。", "確實如此。", "這個觀點不錯。"],
                Emotion.CONFUSED: ["我來解釋一下。", "這樣理解就對了。", "其實很簡單。"],
            },
        }
        
        role_responses = fallback_responses.get(
            persona.id,
            {Emotion.NEUTRAL: ["嗯嗯", "是啊", "有道理"]}
        )
        
        responses = role_responses.get(emotion, role_responses.get(Emotion.NEUTRAL, ["嗯嗯"]))
        return random.choice(responses)
    
    def _post_process(self, response: str, persona: RolePersona) -> str:
        """後處理生成的回復"""
        # 移除角色名前綴（如果 LLM 加了的話）
        response = re.sub(rf'^{persona.name}[：:]\s*', '', response)
        
        # 限制長度
        if len(response) > 200:
            sentences = re.split(r'[。！？.!?]', response)
            response = '。'.join(sentences[:3]) + '。' if sentences else response[:200]
        
        return response.strip()
    
    def _get_conversation_history(self, group_id: int) -> List[dict]:
        """獲取群組對話歷史"""
        return self.conversation_history.get(group_id, [])
    
    def _add_to_history(self, group_id: int, name: str, text: str):
        """添加到對話歷史"""
        if group_id not in self.conversation_history:
            self.conversation_history[group_id] = []
        
        self.conversation_history[group_id].append({
            "name": name,
            "text": text,
            "time": datetime.now().isoformat(),
            "is_ai": name in [p.name for p in self.personas.values()]
        })
        
        # 保留最近 50 條
        if len(self.conversation_history[group_id]) > 50:
            self.conversation_history[group_id] = self.conversation_history[group_id][-50:]
    
    def add_persona(self, persona: RolePersona):
        """添加自定義角色"""
        self.personas[persona.id] = persona
    
    async def close(self):
        """關閉資源"""
        if self.http_client:
            await self.http_client.aclose()


# ==================== 智能對話管理器 ====================

class SmartDialogueManager:
    """智能對話管理器 - 協調多角色對話"""
    
    def __init__(self, config: LLMConfig = None):
        self.generator = LLMDialogueGenerator(config)
        self.active_roles: Dict[int, List[str]] = {}  # group_id -> [role_ids]
        self.last_speakers: Dict[int, List[str]] = {}  # 避免同一角色連續說話
        
        # 回復概率配置
        self.response_probability = 0.3  # 基礎回復概率
        self.mention_boost = 0.5  # 被 @ 時增加的概率
    
    def assign_roles_to_group(self, group_id: int, role_ids: List[str]):
        """為群組分配角色"""
        self.active_roles[group_id] = role_ids
        self.last_speakers[group_id] = []
    
    async def should_respond(
        self,
        group_id: int,
        message_text: str,
        is_mentioned: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        判斷是否應該回復，以及由誰回復
        
        Returns:
            (是否回復, 角色ID)
        """
        # 計算回復概率
        probability = self.response_probability
        if is_mentioned:
            probability += self.mention_boost
        
        # 關鍵詞觸發
        trigger_keywords = ["紅包", "遊戲", "玩", "新人", "大家好"]
        if any(kw in message_text for kw in trigger_keywords):
            probability += 0.3
        
        if random.random() > probability:
            return False, None
        
        # 選擇角色
        available_roles = self.active_roles.get(group_id, list(self.generator.personas.keys()))
        last_speakers = self.last_speakers.get(group_id, [])
        
        # 避免同一角色連續說話
        candidates = [r for r in available_roles if r not in last_speakers[-2:]]
        if not candidates:
            candidates = available_roles
        
        selected_role = random.choice(candidates)
        
        # 更新最近發言者
        if group_id not in self.last_speakers:
            self.last_speakers[group_id] = []
        self.last_speakers[group_id].append(selected_role)
        if len(self.last_speakers[group_id]) > 5:
            self.last_speakers[group_id] = self.last_speakers[group_id][-5:]
        
        return True, selected_role
    
    async def generate_group_response(
        self,
        group_id: int,
        user_message: str,
        user_id: int,
        user_name: str,
        context_messages: List[dict] = None
    ) -> Optional[Tuple[str, str]]:
        """
        為群組消息生成回復
        
        Returns:
            (角色名, 回復文本) 或 None
        """
        should_reply, role_id = await self.should_respond(
            group_id, user_message
        )
        
        if not should_reply or not role_id:
            return None
        
        response = await self.generator.generate_response(
            group_id=group_id,
            user_message=user_message,
            user_id=user_id,
            user_name=user_name,
            role_id=role_id,
            context_messages=context_messages
        )
        
        if response:
            persona = self.generator.personas.get(role_id)
            role_name = persona.name if persona else role_id
            return role_name, response
        
        return None
    
    async def close(self):
        """關閉資源"""
        await self.generator.close()


# 導出
__all__ = [
    "LLMConfig",
    "LLMProvider",
    "Emotion",
    "EmotionDetector",
    "RolePersona",
    "DEFAULT_PERSONAS",
    "LLMDialogueGenerator",
    "SmartDialogueManager"
]
