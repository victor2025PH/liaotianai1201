"""
劇本引擎 - 執行劇本邏輯
"""
import logging
import random
from typing import Optional, Dict, Any, List
from datetime import datetime

from pyrogram.types import Message

from group_ai_service.script_parser import Script, Scene, Trigger, Response
from group_ai_service.models.account import AccountStatusEnum
from group_ai_service.variable_resolver import VariableResolver
from group_ai_service.ai_generator import get_ai_generator

logger = logging.getLogger(__name__)


class ScriptState:
    """劇本執行狀態"""
    
    def __init__(self, account_id: str, script: Script):
        self.account_id = account_id
        self.script = script
        self.current_scene: Optional[str] = None
        self.scene_history: List[str] = []
        self.variables: Dict[str, Any] = {}
        self.last_activity: Optional[datetime] = None
        self.scene_start_time: Optional[datetime] = None
    
    def transition_to_scene(self, scene_id: str):
        """切換到指定場景"""
        if scene_id not in self.script.scenes:
            logger.warning(f"場景 {scene_id} 不存在，保持當前場景")
            return False
        
        if self.current_scene:
            self.scene_history.append(self.current_scene)
        
        self.current_scene = scene_id
        self.scene_start_time = datetime.now()
        logger.info(f"賬號 {self.account_id} 切換到場景: {scene_id}")
        return True
    
    def get_current_scene(self) -> Optional[Scene]:
        """獲取當前場景"""
        if not self.current_scene:
            return None
        return self.script.scenes.get(self.current_scene)


class ScriptEngine:
    """劇本引擎"""
    
    def __init__(self):
        self.running_states: Dict[str, ScriptState] = {}
        self.variable_resolver = VariableResolver()
        logger.info("ScriptEngine 初始化完成")
    
    def initialize_account(self, account_id: str, script: Script, initial_scene: Optional[str] = None):
        """初始化賬號的劇本狀態"""
        state = ScriptState(account_id, script)
        
        # 設置初始場景
        if initial_scene:
            state.transition_to_scene(initial_scene)
        elif script.scenes:
            # 使用第一個場景作為初始場景
            first_scene_id = list(script.scenes.keys())[0]
            state.transition_to_scene(first_scene_id)
        
        self.running_states[account_id] = state
        logger.info(f"賬號 {account_id} 劇本狀態已初始化，當前場景: {state.current_scene}")
    
    async def process_message(
        self,
        account_id: str,
        message: Message,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """處理消息，返回回復"""
        state = self.running_states.get(account_id)
        if not state:
            logger.warning(f"賬號 {account_id} 沒有初始化劇本狀態")
            return None
        
        current_scene = state.get_current_scene()
        if not current_scene:
            logger.warning(f"賬號 {account_id} 當前沒有活動場景")
            return None
        
        # 檢查觸發條件
        matched_trigger = self._match_triggers(current_scene, message, context)
        if not matched_trigger:
            logger.debug(f"消息未匹配任何觸發條件")
            return None
        
        # 選擇回復
        response = self._select_response(current_scene.responses)
        if not response:
            logger.warning(f"場景 {current_scene.id} 沒有可用的回復")
            return None
        
        # 生成回復內容
        reply_text = await self._generate_reply(response, message, context, state)
        
        # 切換場景（如果有）
        if current_scene.next_scene:
            state.transition_to_scene(current_scene.next_scene)
        
        state.last_activity = datetime.now()
        return reply_text
    
    def _match_triggers(self, scene: Scene, message: Message, context: Optional[Dict[str, Any]]) -> Optional[Trigger]:
        """匹配觸發條件"""
        message_text = message.text or ""
        
        for trigger in scene.triggers:
            if trigger.type == "keyword" and trigger.keywords:
                # 關鍵詞匹配
                if any(keyword.lower() in message_text.lower() for keyword in trigger.keywords):
                    return trigger
            
            elif trigger.type == "message":
                # 消息長度匹配
                length = len(message_text)
                if trigger.min_length and length < trigger.min_length:
                    continue
                if trigger.max_length and length > trigger.max_length:
                    continue
                return trigger
            
            elif trigger.type == "new_member":
                # 新成員加入（需要從 context 判斷）
                if context and context.get("is_new_member"):
                    return trigger
            
            elif trigger.type == "redpacket":
                # 紅包消息（需要從 context 判斷）
                if context and context.get("is_redpacket"):
                    return trigger
        
        return None
    
    def _select_response(self, responses: list[Response]) -> Optional[Response]:
        """選擇回復模板"""
        if not responses:
            return None
        
        # 簡單隨機選擇（後續可以實現更複雜的策略）
        return random.choice(responses)
    
    async def _generate_reply(
        self,
        response: Response,
        message: Message,
        context: Optional[Dict[str, Any]],
        state: ScriptState
    ) -> str:
        """生成回復內容"""
        template = response.template
        
        # 如果需要 AI 生成
        if response.ai_generate:
            # 構建上下文消息
            context_messages = self._build_context_messages(
                message, context, state, response.context_window
            )
            
            # 調用 AI 生成
            ai_generator = get_ai_generator()
            ai_reply = await ai_generator.generate_reply(
                message=message,
                context_messages=context_messages,
                temperature=response.temperature or 0.7,
                max_tokens=150,
                system_prompt=template  # 使用模板作為系統提示詞
            )
            
            if ai_reply:
                # 對 AI 生成的回復進行變量替換
                return self._replace_variables(ai_reply, message, context, state)
            else:
                logger.warning("AI 生成失敗，返回模板")
        
        # 變量替換
        return self._replace_variables(template, message, context, state)
    
    def _build_context_messages(
        self,
        message: Message,
        context: Optional[Dict[str, Any]],
        state: ScriptState,
        context_window: int
    ) -> List[Dict[str, str]]:
        """構建上下文消息列表"""
        context_messages = []
        
        # 從 context 中獲取歷史消息（如果有的話）
        if context and "history" in context:
            history = context["history"]
            if isinstance(history, list):
                # 只取最近的 N 條消息
                recent_history = history[-context_window:]
                for msg in recent_history:
                    if isinstance(msg, dict):
                        context_messages.append({
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", "")
                        })
        
        return context_messages
    
    def _replace_variables(
        self,
        template: str,
        message: Message,
        context: Optional[Dict[str, Any]],
        state: ScriptState
    ) -> str:
        """替換模板中的變量"""
        context = context or {}
        state_dict = {
            "current_scene": state.current_scene,
            "variables": state.variables,
        }
        
        return self.variable_resolver.resolve(template, message, context, state_dict)
    
    def get_current_scene(self, account_id: str) -> Optional[str]:
        """獲取當前場景 ID"""
        state = self.running_states.get(account_id)
        return state.current_scene if state else None
    
    def transition_scene(self, account_id: str, scene_id: str) -> bool:
        """切換場景"""
        state = self.running_states.get(account_id)
        if not state:
            return False
        return state.transition_to_scene(scene_id)
    
    def remove_account(self, account_id: str):
        """移除賬號的劇本狀態"""
        if account_id in self.running_states:
            del self.running_states[account_id]
            logger.info(f"賬號 {account_id} 的劇本狀態已移除")

