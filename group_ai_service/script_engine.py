"""
劇本引擎 - 執行劇本邏輯
"""
import logging
import random
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from group_ai_service.reply_quality_manager import ReplyQualityManager

from pyrogram.types import Message

from group_ai_service.script_parser import Script, Scene, Trigger, Response
from group_ai_service.models.account import AccountStatusEnum
from group_ai_service.variable_resolver import VariableResolver
from group_ai_service.ai_generator import get_ai_generator

# 避免循環導入
try:
    from group_ai_service.reply_quality_manager import ReplyQualityManager
except ImportError:
    ReplyQualityManager = None

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
    
    def __init__(self, reply_quality_manager: Optional['ReplyQualityManager'] = None):
        self.running_states: Dict[str, ScriptState] = {}
        self.variable_resolver = VariableResolver()
        self.reply_quality_manager = reply_quality_manager
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
        
        # 選擇回復（傳遞賬號和群組ID用於質量管理）
        group_id = context.get("group_id") if context else None
        response = self._select_response(
            current_scene.responses,
            account_id=account_id,
            group_id=group_id
        )
        if not response:
            logger.warning(f"場景 {current_scene.id} 沒有可用的回復")
            return None
        
        # 生成回復內容
        reply_text = await self._generate_reply(response, message, context, state)
        
        # 記錄回復到質量管理器（如果啟用）
        if reply_text and self.reply_quality_manager:
            group_id = context.get("group_id") if context else None
            if group_id:
                template_id = getattr(response, 'template_id', None) or getattr(response, 'id', None)
                self.reply_quality_manager.record_reply(
                    account_id=account_id,
                    group_id=group_id,
                    reply_text=reply_text,
                    template_id=template_id
                )
        
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
    
    def _select_response(
        self,
        responses: list[Response],
        account_id: Optional[str] = None,
        group_id: Optional[int] = None
    ) -> Optional[Response]:
        """
        選擇回復模板（優化：使用回復質量管理器避免重複）
        
        Args:
            responses: 回復模板列表
            account_id: 賬號ID（用於質量管理）
            group_id: 群組ID（用於質量管理）
        
        Returns:
            選中的回復模板
        """
        if not responses:
            return None
        
        # 如果啟用了回復質量管理器，使用智能選擇
        if self.reply_quality_manager and account_id and group_id:
            selected = self.reply_quality_manager.select_best_response(
                account_id=account_id,
                group_id=group_id,
                responses=responses,
                get_template_id=lambda r: getattr(r, 'template_id', None) or getattr(r, 'id', None)
            )
            if selected:
                return selected
            # 如果所有回復都重複，降級為隨機選擇
        
        # 簡單隨機選擇（備用策略）
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
    
    def update_script(
        self,
        account_id: str,
        new_script: Script,
        preserve_state: bool = True
    ) -> bool:
        """
        熱更新賬號的劇本（不重啟賬號）
        
        Args:
            account_id: 賬號ID
            new_script: 新劇本
            preserve_state: 是否保留當前場景狀態（默認True）
        
        Returns:
            是否更新成功
        """
        if account_id not in self.running_states:
            logger.warning(f"賬號 {account_id} 沒有初始化劇本狀態，將初始化新劇本")
            self.initialize_account(account_id, new_script)
            return True
        
        old_state = self.running_states[account_id]
        old_current_scene = old_state.current_scene
        
        try:
            # 保存當前狀態信息
            preserved_variables = old_state.variables.copy() if preserve_state else {}
            preserved_scene_history = old_state.scene_history.copy() if preserve_state else []
            
            # 創建新狀態
            new_state = ScriptState(account_id, new_script)
            
            # 恢復變量
            new_state.variables = preserved_variables
            
            # 嘗試恢復當前場景（如果新劇本中有相同的場景）
            if preserve_state and old_current_scene and old_current_scene in new_script.scenes:
                new_state.transition_to_scene(old_current_scene)
                new_state.scene_history = preserved_scene_history
                logger.info(f"賬號 {account_id} 劇本已熱更新，保留場景: {old_current_scene}")
            elif new_script.scenes:
                # 如果無法保留場景，使用第一個場景
                first_scene_id = list(new_script.scenes.keys())[0]
                new_state.transition_to_scene(first_scene_id)
                logger.info(f"賬號 {account_id} 劇本已熱更新，切換到場景: {first_scene_id}")
            
            # 更新狀態
            self.running_states[account_id] = new_state
            new_state.last_activity = datetime.now()
            
            logger.info(f"賬號 {account_id} 劇本熱更新成功")
            return True
            
        except Exception as e:
            logger.error(f"賬號 {account_id} 劇本熱更新失敗: {e}", exc_info=True)
            return False
    
    def remove_account(self, account_id: str):
        """移除賬號的劇本狀態"""
        if account_id in self.running_states:
            del self.running_states[account_id]
            logger.info(f"賬號 {account_id} 的劇本狀態已移除")

