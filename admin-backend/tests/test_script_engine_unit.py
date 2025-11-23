"""
ScriptEngine 單元測試
"""
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from group_ai_service.script_engine import ScriptEngine, ScriptState
from group_ai_service.script_parser import Script, Scene, Trigger, Response


@pytest.fixture
def sample_script():
    """創建示例劇本"""
    from group_ai_service.script_parser import Trigger, Response
    
    script = Script(
        script_id="test_script",
        version="1.0.0",
        description="測試用劇本",
        scenes={
            "scene1": Scene(
                id="scene1",
                triggers=[
                    Trigger(type="keyword", keywords=["觸發詞1"])
                ],
                responses=[
                    Response(template="回復1"),
                    Response(template="回復2")
                ]
            ),
            "scene2": Scene(
                id="scene2",
                triggers=[
                    Trigger(type="keyword", keywords=["觸發詞2"])
                ],
                responses=[
                    Response(template="回復3")
                ]
            )
        }
    )
    return script


@pytest.fixture
def script_engine():
    """創建 ScriptEngine 實例"""
    return ScriptEngine()


@pytest.fixture
def initialized_engine(script_engine, sample_script):
    """創建已初始化的 ScriptEngine 實例"""
    script_engine.initialize_account("test_account", sample_script, "scene1")
    return script_engine


class TestScriptState:
    """ScriptState 測試"""
    
    def test_state_creation(self, sample_script):
        """測試狀態創建"""
        state = ScriptState("test_account", sample_script)
        
        assert state.script == sample_script
        assert state.account_id == "test_account"
        assert state.current_scene is None  # 初始狀態沒有場景
        assert len(state.scene_history) == 0
    
    def test_get_current_scene(self, sample_script):
        """測試獲取當前場景"""
        state = ScriptState("test_account", sample_script)
        state.transition_to_scene("scene1")
        scene = state.get_current_scene()
        
        assert scene is not None
        assert scene.id == "scene1"


class TestScriptEngine:
    """ScriptEngine 測試"""
    
    def test_engine_initialization(self, script_engine):
        """測試引擎初始化"""
        assert script_engine is not None
        assert hasattr(script_engine, 'running_states')
        assert hasattr(script_engine, 'variable_resolver')
    
    def test_initialize_account(self, script_engine, sample_script):
        """測試初始化賬號"""
        script_engine.initialize_account("test_account", sample_script, "scene1")
        
        assert "test_account" in script_engine.running_states
        state = script_engine.running_states["test_account"]
        assert state.current_scene == "scene1"
    
    def test_initialize_account_default_scene(self, script_engine, sample_script):
        """測試初始化賬號（使用默認場景）"""
        script_engine.initialize_account("test_account", sample_script)
        
        state = script_engine.running_states["test_account"]
        # 應該使用第一個場景
        assert state.current_scene is not None
        assert state.current_scene in sample_script.scenes
    
    def test_get_state(self, initialized_engine):
        """測試獲取狀態"""
        state = initialized_engine.running_states.get("test_account")
        assert state is not None
        assert state.current_scene == "scene1"
    
    def test_transition_scene(self, initialized_engine):
        """測試切換場景"""
        state = initialized_engine.running_states["test_account"]
        initial_scene = state.current_scene
        
        # 切換到場景2
        result = state.transition_to_scene("scene2")
        assert result is True
        assert state.current_scene == "scene2"
        assert initial_scene in state.scene_history
    
    def test_transition_invalid_scene(self, initialized_engine):
        """測試切換到無效場景"""
        state = initialized_engine.running_states["test_account"]
        initial_scene = state.current_scene
        
        # 切換到不存在的場景
        result = state.transition_to_scene("nonexistent_scene")
        assert result is False
        assert state.current_scene == initial_scene  # 保持當前場景
    
    @pytest.mark.asyncio
    async def test_process_message_with_trigger(self, initialized_engine):
        """測試處理消息（有觸發詞）"""
        # 創建模擬消息
        mock_message = Mock()
        mock_message.text = "觸發詞1"
        mock_message.from_user = Mock()
        mock_message.from_user.id = 123456789
        
        # Mock 變量解析器
        initialized_engine.variable_resolver.resolve = Mock(return_value="回復1")
        
        reply = await initialized_engine.process_message("test_account", mock_message)
        
        assert reply is not None
        assert isinstance(reply, str)
    
    @pytest.mark.asyncio
    async def test_process_message_no_trigger(self, initialized_engine):
        """測試處理消息（無觸發詞）"""
        # 創建模擬消息
        mock_message = Mock()
        mock_message.text = "沒有觸發詞的消息"
        mock_message.from_user = Mock()
        mock_message.from_user.id = 123456789
        
        reply = await initialized_engine.process_message("test_account", mock_message)
        
        # 沒有觸發詞，應該返回 None
        assert reply is None
    
    def test_get_current_scene(self, initialized_engine):
        """測試獲取當前場景"""
        scene = initialized_engine.get_current_scene("test_account")
        
        assert scene == "scene1"
    
    def test_get_current_scene_not_found(self, initialized_engine):
        """測試獲取不存在的賬號場景"""
        scene = initialized_engine.get_current_scene("nonexistent_account")
        
        assert scene is None
    
    def test_transition_scene(self, initialized_engine):
        """測試切換場景"""
        result = initialized_engine.transition_scene("test_account", "scene2")
        
        assert result is True
        state = initialized_engine.running_states["test_account"]
        assert state.current_scene == "scene2"
    
    def test_transition_scene_invalid(self, initialized_engine):
        """測試切換到無效場景"""
        result = initialized_engine.transition_scene("test_account", "nonexistent_scene")
        
        assert result is False
    
    def test_remove_account(self, initialized_engine):
        """測試移除賬號"""
        initialized_engine.remove_account("test_account")
        
        assert "test_account" not in initialized_engine.running_states
    
    def test_remove_account_not_found(self, initialized_engine):
        """測試移除不存在的賬號"""
        # 不應該報錯
        initialized_engine.remove_account("nonexistent_account")
    
    def test_match_triggers(self, initialized_engine):
        """測試匹配觸發詞"""
        state = initialized_engine.running_states["test_account"]
        scene = state.get_current_scene()
        
        # 創建模擬消息
        mock_message = Mock()
        mock_message.text = "觸發詞1"
        mock_message.from_user = Mock()
        mock_message.from_user.id = 123456789
        
        trigger = initialized_engine._match_triggers(scene, mock_message, {})
        
        assert trigger is not None
        assert trigger.type == "keyword"
    
    def test_select_response(self, initialized_engine):
        """測試選擇回復"""
        state = initialized_engine.running_states["test_account"]
        scene = state.get_current_scene()
        
        response = initialized_engine._select_response(scene.responses)
        
        assert response is not None
        assert isinstance(response, type(scene.responses[0]))
    
    def test_get_current_scene_none(self, sample_script):
        """測試獲取當前場景（沒有場景）"""
        state = ScriptState("test_account", sample_script)
        # 不設置場景
        scene = state.get_current_scene()
        
        assert scene is None
    
    @pytest.mark.asyncio
    async def test_process_message_no_state(self, script_engine):
        """測試處理消息（沒有初始化狀態）"""
        mock_message = Mock()
        mock_message.text = "測試消息"
        
        reply = await script_engine.process_message("nonexistent_account", mock_message)
        
        assert reply is None
    
    @pytest.mark.asyncio
    async def test_process_message_no_scene(self, script_engine, sample_script):
        """測試處理消息（沒有活動場景）"""
        # 創建狀態但不設置場景
        state = ScriptState("test_account", sample_script)
        script_engine.running_states["test_account"] = state
        
        mock_message = Mock()
        mock_message.text = "測試消息"
        
        reply = await script_engine.process_message("test_account", mock_message)
        
        assert reply is None
    
    @pytest.mark.asyncio
    async def test_process_message_no_responses(self, initialized_engine):
        """測試處理消息（場景沒有回復）"""
        state = initialized_engine.running_states["test_account"]
        scene = state.get_current_scene()
        # 清空回復列表
        scene.responses = []
        
        mock_message = Mock()
        mock_message.text = "觸發詞1"
        
        reply = await initialized_engine.process_message("test_account", mock_message)
        
        assert reply is None
    
    @pytest.mark.asyncio
    async def test_process_message_scene_transition(self, initialized_engine, sample_script):
        """測試處理消息（場景切換）"""
        # 設置 scene1 的 next_scene 為 scene2
        scene1 = sample_script.scenes["scene1"]
        scene1.next_scene = "scene2"
        
        mock_message = Mock()
        mock_message.text = "觸發詞1"
        mock_message.from_user = Mock()
        mock_message.from_user.id = 123456789
        
        initialized_engine.variable_resolver.resolve = Mock(return_value="回復1")
        
        reply = await initialized_engine.process_message("test_account", mock_message)
        
        # 驗證場景已切換
        state = initialized_engine.running_states["test_account"]
        assert state.current_scene == "scene2"
        assert reply is not None
    
    def test_match_triggers_message_type(self, initialized_engine):
        """測試匹配觸發條件（message 類型）"""
        from group_ai_service.script_parser import Trigger
        
        state = initialized_engine.running_states["test_account"]
        scene = state.get_current_scene()
        
        # 添加 message 類型的觸發器
        message_trigger = Trigger(
            type="message",
            min_length=5,
            max_length=20
        )
        scene.triggers.append(message_trigger)
        
        # 創建模擬消息（符合長度要求）
        mock_message = Mock()
        mock_message.text = "這是一條符合長度的消息"
        
        trigger = initialized_engine._match_triggers(scene, mock_message, {})
        
        assert trigger is not None
        assert trigger.type == "message"
    
    def test_match_triggers_message_too_short(self, initialized_engine):
        """測試匹配觸發條件（message 類型，太短）"""
        from group_ai_service.script_parser import Trigger
        
        state = initialized_engine.running_states["test_account"]
        scene = state.get_current_scene()
        
        # 添加 message 類型的觸發器
        message_trigger = Trigger(
            type="message",
            min_length=10,
            max_length=20
        )
        scene.triggers.append(message_trigger)
        
        # 創建模擬消息（太短）
        mock_message = Mock()
        mock_message.text = "短"
        
        trigger = initialized_engine._match_triggers(scene, mock_message, {})
        
        # 太短，不應該匹配
        assert trigger is None or trigger.type != "message"
    
    def test_match_triggers_message_too_long(self, initialized_engine):
        """測試匹配觸發條件（message 類型，太長）"""
        from group_ai_service.script_parser import Trigger
        
        state = initialized_engine.running_states["test_account"]
        scene = state.get_current_scene()
        
        # 添加 message 類型的觸發器
        message_trigger = Trigger(
            type="message",
            min_length=5,
            max_length=10
        )
        scene.triggers.append(message_trigger)
        
        # 創建模擬消息（太長）
        mock_message = Mock()
        mock_message.text = "這是一條非常長的消息，超過了最大長度限制"
        
        trigger = initialized_engine._match_triggers(scene, mock_message, {})
        
        # 太長，不應該匹配
        assert trigger is None or trigger.type != "message"
    
    def test_match_triggers_new_member(self, initialized_engine):
        """測試匹配觸發條件（new_member 類型）"""
        from group_ai_service.script_parser import Trigger
        
        state = initialized_engine.running_states["test_account"]
        scene = state.get_current_scene()
        
        # 添加 new_member 類型的觸發器
        new_member_trigger = Trigger(type="new_member")
        scene.triggers.append(new_member_trigger)
        
        # 創建模擬消息
        mock_message = Mock()
        mock_message.text = "歡迎新成員"
        
        # 設置 context 標記為新成員
        context = {"is_new_member": True}
        
        trigger = initialized_engine._match_triggers(scene, mock_message, context)
        
        assert trigger is not None
        assert trigger.type == "new_member"
    
    def test_match_triggers_new_member_no_context(self, initialized_engine):
        """測試匹配觸發條件（new_member 類型，沒有 context）"""
        from group_ai_service.script_parser import Trigger
        
        state = initialized_engine.running_states["test_account"]
        scene = state.get_current_scene()
        
        # 添加 new_member 類型的觸發器
        new_member_trigger = Trigger(type="new_member")
        scene.triggers.append(new_member_trigger)
        
        # 創建模擬消息
        mock_message = Mock()
        mock_message.text = "歡迎新成員"
        
        # 沒有 context
        trigger = initialized_engine._match_triggers(scene, mock_message, None)
        
        # 沒有 context，不應該匹配
        assert trigger is None or trigger.type != "new_member"
    
    def test_match_triggers_redpacket(self, initialized_engine):
        """測試匹配觸發條件（redpacket 類型）"""
        from group_ai_service.script_parser import Trigger
        
        state = initialized_engine.running_states["test_account"]
        scene = state.get_current_scene()
        
        # 添加 redpacket 類型的觸發器
        redpacket_trigger = Trigger(type="redpacket")
        scene.triggers.append(redpacket_trigger)
        
        # 創建模擬消息
        mock_message = Mock()
        mock_message.text = "發紅包"
        
        # 設置 context 標記為紅包
        context = {"is_redpacket": True}
        
        trigger = initialized_engine._match_triggers(scene, mock_message, context)
        
        assert trigger is not None
        assert trigger.type == "redpacket"
    
    def test_match_triggers_redpacket_no_context(self, initialized_engine):
        """測試匹配觸發條件（redpacket 類型，沒有 context）"""
        from group_ai_service.script_parser import Trigger
        
        state = initialized_engine.running_states["test_account"]
        scene = state.get_current_scene()
        
        # 添加 redpacket 類型的觸發器
        redpacket_trigger = Trigger(type="redpacket")
        scene.triggers.append(redpacket_trigger)
        
        # 創建模擬消息
        mock_message = Mock()
        mock_message.text = "發紅包"
        
        # 沒有 context
        trigger = initialized_engine._match_triggers(scene, mock_message, None)
        
        # 沒有 context，不應該匹配
        assert trigger is None or trigger.type != "redpacket"
    
    def test_select_response_empty(self, initialized_engine):
        """測試選擇回復（空列表）"""
        response = initialized_engine._select_response([])
        
        assert response is None
    
    @pytest.mark.asyncio
    async def test_generate_reply_with_ai(self, initialized_engine):
        """測試生成回復（使用 AI）"""
        from group_ai_service.script_parser import Response
        
        # 創建需要 AI 生成的回復
        ai_response = Response(
            template="生成一個回復",
            ai_generate=True,
            temperature=0.8,
            context_window=5
        )
        
        mock_message = Mock()
        mock_message.text = "測試消息"
        mock_message.from_user = Mock()
        mock_message.from_user.id = 123456789
        
        state = initialized_engine.running_states["test_account"]
        
        # Mock AI 生成器
        mock_ai_generator = AsyncMock()
        mock_ai_generator.generate_reply = AsyncMock(return_value="AI 生成的回復")
        
        with patch('group_ai_service.script_engine.get_ai_generator', return_value=mock_ai_generator):
            # Mock 變量解析器
            initialized_engine.variable_resolver.resolve = Mock(return_value="AI 生成的回復（已替換變量）")
            
            reply = await initialized_engine._generate_reply(ai_response, mock_message, {}, state)
            
            assert reply is not None
            assert "AI 生成的回復" in reply
            mock_ai_generator.generate_reply.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_reply_ai_failed(self, initialized_engine):
        """測試生成回復（AI 生成失敗）"""
        from group_ai_service.script_parser import Response
        
        # 創建需要 AI 生成的回復
        ai_response = Response(
            template="生成一個回復",
            ai_generate=True
        )
        
        mock_message = Mock()
        mock_message.text = "測試消息"
        
        state = initialized_engine.running_states["test_account"]
        
        # Mock AI 生成器（返回 None，表示失敗）
        mock_ai_generator = AsyncMock()
        mock_ai_generator.generate_reply = AsyncMock(return_value=None)
        
        with patch('group_ai_service.script_engine.get_ai_generator', return_value=mock_ai_generator):
            # Mock 變量解析器（應該使用模板）
            initialized_engine.variable_resolver.resolve = Mock(return_value="生成一個回復（已替換變量）")
            
            reply = await initialized_engine._generate_reply(ai_response, mock_message, {}, state)
            
            # AI 生成失敗，應該返回模板（經過變量替換）
            assert reply is not None
            assert "生成一個回復" in reply
    
    @pytest.mark.asyncio
    async def test_generate_reply_without_ai(self, initialized_engine):
        """測試生成回復（不使用 AI）"""
        from group_ai_service.script_parser import Response
        
        # 創建不需要 AI 生成的回復
        response = Response(
            template="直接回復：{{message.text}}",
            ai_generate=False
        )
        
        mock_message = Mock()
        mock_message.text = "測試消息"
        
        state = initialized_engine.running_states["test_account"]
        
        # Mock 變量解析器
        initialized_engine.variable_resolver.resolve = Mock(return_value="直接回復：測試消息")
        
        reply = await initialized_engine._generate_reply(response, mock_message, {}, state)
        
        assert reply is not None
        assert "直接回復：測試消息" == reply
    
    def test_build_context_messages(self, initialized_engine):
        """測試構建上下文消息"""
        mock_message = Mock()
        mock_message.text = "當前消息"
        
        state = initialized_engine.running_states["test_account"]
        
        # 創建包含歷史消息的 context
        context = {
            "history": [
                {"role": "user", "content": "消息1"},
                {"role": "assistant", "content": "回復1"},
                {"role": "user", "content": "消息2"},
                {"role": "assistant", "content": "回復2"},
                {"role": "user", "content": "消息3"},
            ]
        }
        
        context_messages = initialized_engine._build_context_messages(
            mock_message, context, state, context_window=3
        )
        
        # 應該只取最近的 3 條消息
        assert len(context_messages) == 3
        assert context_messages[0]["content"] == "消息2"
        assert context_messages[1]["content"] == "回復2"
        assert context_messages[2]["content"] == "消息3"
    
    def test_build_context_messages_no_history(self, initialized_engine):
        """測試構建上下文消息（沒有歷史）"""
        mock_message = Mock()
        mock_message.text = "當前消息"
        
        state = initialized_engine.running_states["test_account"]
        
        # 沒有歷史消息的 context
        context = {}
        
        context_messages = initialized_engine._build_context_messages(
            mock_message, context, state, context_window=5
        )
        
        # 應該返回空列表
        assert len(context_messages) == 0
    
    def test_build_context_messages_invalid_history(self, initialized_engine):
        """測試構建上下文消息（無效的歷史）"""
        mock_message = Mock()
        mock_message.text = "當前消息"
        
        state = initialized_engine.running_states["test_account"]
        
        # 無效的歷史（不是列表）
        context = {"history": "invalid"}
        
        context_messages = initialized_engine._build_context_messages(
            mock_message, context, state, context_window=5
        )
        
        # 應該返回空列表
        assert len(context_messages) == 0
    
    def test_build_context_messages_invalid_message(self, initialized_engine):
        """測試構建上下文消息（無效的消息格式）"""
        mock_message = Mock()
        mock_message.text = "當前消息"
        
        state = initialized_engine.running_states["test_account"]
        
        # 包含無效消息格式的歷史
        context = {
            "history": [
                "invalid_message",  # 不是字典
                {"role": "user", "content": "消息1"},
            ]
        }
        
        context_messages = initialized_engine._build_context_messages(
            mock_message, context, state, context_window=5
        )
        
        # 應該只包含有效的消息
        assert len(context_messages) == 1
        assert context_messages[0]["content"] == "消息1"
    
    def test_replace_variables(self, initialized_engine):
        """測試替換變量"""
        template = "當前場景：{{current_scene}}"
        
        mock_message = Mock()
        mock_message.text = "測試消息"
        
        state = initialized_engine.running_states["test_account"]
        
        # Mock 變量解析器
        initialized_engine.variable_resolver.resolve = Mock(return_value="當前場景：scene1")
        
        result = initialized_engine._replace_variables(template, mock_message, {}, state)
        
        assert result == "當前場景：scene1"
        initialized_engine.variable_resolver.resolve.assert_called_once()
    
    def test_transition_scene_no_state(self, script_engine):
        """測試切換場景（沒有狀態）"""
        result = script_engine.transition_scene("nonexistent_account", "scene1")
        
        assert result is False

