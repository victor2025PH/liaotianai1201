"""
AIGenerator 單元測試
"""
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from group_ai_service.ai_generator import AIGenerator, get_ai_generator


@pytest.fixture
def ai_generator():
    """創建 AIGenerator 實例"""
    return AIGenerator(provider="mock")


@pytest.fixture
def mock_message():
    """創建模擬消息對象"""
    mock = Mock()
    mock.text = "你好"
    mock.id = 1
    mock.from_user = Mock()
    mock.from_user.id = 123456789
    return mock


class TestAIGenerator:
    """AIGenerator 測試"""
    
    def test_generator_initialization(self, ai_generator):
        """測試生成器初始化"""
        assert ai_generator is not None
        assert ai_generator.provider == "mock"
        assert ai_generator.api_key is None
    
    def test_generator_initialization_with_provider(self):
        """測試使用指定提供商初始化"""
        generator = AIGenerator(provider="openai", api_key="test_key")
        assert generator.provider == "openai"
        assert generator.api_key == "test_key"
    
    @pytest.mark.asyncio
    async def test_generate_reply_mock(self, ai_generator, mock_message):
        """測試模擬模式生成回復"""
        context_messages = [
            {"role": "user", "content": "之前的消息"}
        ]
        
        reply = await ai_generator.generate_reply(
            mock_message,
            context_messages
        )
        
        assert reply is not None
        assert isinstance(reply, str)
        assert len(reply) > 0
    
    @pytest.mark.asyncio
    async def test_generate_reply_with_keyword(self, ai_generator, mock_message):
        """測試關鍵詞匹配回復"""
        mock_message.text = "你好"
        context_messages = []
        
        reply = await ai_generator.generate_reply(
            mock_message,
            context_messages
        )
        
        assert reply is not None
        assert isinstance(reply, str)
        # 應該包含關鍵詞相關的回復
        assert len(reply) > 0
    
    @pytest.mark.asyncio
    async def test_generate_reply_default(self, ai_generator):
        """測試默認回復"""
        mock_message = Mock()
        mock_message.text = "這是一個普通消息"
        context_messages = []
        
        reply = await ai_generator.generate_reply(
            mock_message,
            context_messages
        )
        
        assert reply is not None
        assert isinstance(reply, str)
        assert len(reply) > 0
    
    @pytest.mark.asyncio
    async def test_generate_reply_with_system_prompt(self, ai_generator, mock_message):
        """測試使用系統提示詞生成回復"""
        context_messages = []
        system_prompt = "你是一個專業的助手"
        
        reply = await ai_generator.generate_reply(
            mock_message,
            context_messages,
            system_prompt=system_prompt
        )
        
        assert reply is not None
        assert isinstance(reply, str)
    
    @pytest.mark.asyncio
    async def test_generate_reply_with_context(self, ai_generator, mock_message):
        """測試使用上下文生成回復"""
        context_messages = [
            {"role": "user", "content": "第一條消息"},
            {"role": "assistant", "content": "第一條回復"},
            {"role": "user", "content": "第二條消息"}
        ]
        
        reply = await ai_generator.generate_reply(
            mock_message,
            context_messages
        )
        
        assert reply is not None
        assert isinstance(reply, str)
    
    @pytest.mark.asyncio
    async def test_generate_reply_unknown_provider(self):
        """測試未知提供商"""
        generator = AIGenerator(provider="unknown")
        mock_message = Mock()
        mock_message.text = "測試"
        
        reply = await generator.generate_reply(
            mock_message,
            []
        )
        
        # 應該返回 None
        assert reply is None
    
    def test_set_provider(self, ai_generator):
        """測試設置提供商"""
        ai_generator.set_provider("openai", "new_key")
        
        assert ai_generator.provider == "openai"
        assert ai_generator.api_key == "new_key"
        assert ai_generator._client is None  # 應該重置客戶端


    @pytest.mark.asyncio
    async def test_generate_reply_exception_handling(self, ai_generator, mock_message):
        """測試生成回復時的異常處理"""
        # 模擬 generate_reply 內部異常
        with patch.object(ai_generator, '_generate_mock', side_effect=Exception("測試異常")):
            reply = await ai_generator.generate_reply(mock_message, [])
            # 應該返回 None
            assert reply is None
    
    @pytest.mark.asyncio
    async def test_generate_openai_success(self, mock_message):
        """測試 OpenAI API 成功調用"""
        generator = AIGenerator(provider="openai", api_key="test_key")
        
        # 模擬 OpenAI 客戶端和響應
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "AI 生成的回復"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        generator._client = mock_client
        
        # 直接調用 _generate_openai 方法（因為已經設置了 _client，不會觸發 import）
        reply = await generator._generate_openai(
            mock_message,
            [{"role": "user", "content": "測試"}],
            temperature=0.7,
            max_tokens=100,
            system_prompt="測試提示詞"
        )
        
        assert reply == "AI 生成的回復"
        mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_openai_no_api_key(self, mock_message):
        """測試沒有 API key 時回退到模擬模式"""
        generator = AIGenerator(provider="openai", api_key=None)
        
        reply = await generator.generate_reply(mock_message, [])
        
        # 應該使用模擬模式生成回復
        assert reply is not None
        assert isinstance(reply, str)
        assert len(reply) > 0
    
    @pytest.mark.asyncio
    async def test_generate_openai_import_error(self, mock_message):
        """測試 openai 庫未安裝時回退到模擬模式"""
        generator = AIGenerator(provider="openai", api_key="test_key")
        
        # 只針對 openai 模塊的導入失敗
        original_import = __import__
        def mock_import(name, *args, **kwargs):
            if name == 'openai':
                raise ImportError("No module named 'openai'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            reply = await generator._generate_openai(
                mock_message,
                [],
                temperature=0.7,
                max_tokens=100,
                system_prompt=None
            )
            
            # 應該回退到模擬模式
            assert reply is not None
            assert isinstance(reply, str)
    
    @pytest.mark.asyncio
    async def test_generate_openai_api_error(self, mock_message):
        """測試 OpenAI API 調用失敗時回退到模擬模式"""
        generator = AIGenerator(provider="openai", api_key="test_key")
        
        # 模擬 OpenAI 客戶端異常
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API 錯誤"))
        generator._client = mock_client
        
        # 直接調用 _generate_openai，應該捕獲異常並回退到模擬模式
        reply = await generator._generate_openai(
            mock_message,
            [],
            temperature=0.7,
            max_tokens=100,
            system_prompt=None
        )
        
        # 應該回退到模擬模式
        assert reply is not None
        assert isinstance(reply, str)
    
    @pytest.mark.asyncio
    async def test_generate_openai_with_existing_client(self, mock_message):
        """測試使用已存在的 OpenAI 客戶端"""
        generator = AIGenerator(provider="openai", api_key="test_key")
        
        # 創建已存在的客戶端
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "使用現有客戶端的回復"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        generator._client = mock_client
        
        reply = await generator._generate_openai(
            mock_message,
            [],
            temperature=0.7,
            max_tokens=100,
            system_prompt=None
        )
        
        assert reply == "使用現有客戶端的回復"
        # 不應該創建新客戶端
        assert generator._client is mock_client
    
    @pytest.mark.asyncio
    async def test_generate_openai_default_system_prompt(self, mock_message):
        """測試使用默認系統提示詞"""
        generator = AIGenerator(provider="openai", api_key="test_key")
        
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "回復"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        generator._client = mock_client
        
        await generator._generate_openai(
            mock_message,
            [],
            temperature=0.7,
            max_tokens=100,
            system_prompt=None  # 使用默認系統提示詞
        )
        
        # 檢查是否使用了默認系統提示詞
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        assert messages[0]['role'] == 'system'
        assert "友好的 Telegram 群組助手" in messages[0]['content']
    
    @pytest.mark.asyncio
    async def test_generate_openai_empty_message_text(self, mock_message):
        """測試消息文本為空時的情況"""
        generator = AIGenerator(provider="openai", api_key="test_key")
        mock_message.text = None
        
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "回復"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        generator._client = mock_client
        
        reply = await generator._generate_openai(
            mock_message,
            [],
            temperature=0.7,
            max_tokens=100,
            system_prompt=None
        )
        
        # 應該正常處理空文本
        assert reply is not None
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        # 最後一條消息應該是當前消息
        assert messages[-1]['content'] == ""


class TestGetAIGenerator:
    """get_ai_generator 函數測試"""
    
    def test_get_ai_generator_singleton(self):
        """測試全局實例單例模式"""
        # 清除全局實例
        import group_ai_service.ai_generator as ai_module
        ai_module._global_generator = None
        
        generator1 = get_ai_generator()
        generator2 = get_ai_generator()
        
        # 應該返回同一個實例
        assert generator1 is generator2

