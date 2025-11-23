"""
AI 生成器 - 使用 AI 模型生成對話回復
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from pyrogram.types import Message

logger = logging.getLogger(__name__)


class AIGenerator:
    """AI 生成器（基礎實現，可擴展）"""
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key
        self._client = None
        logger.info(f"AIGenerator 初始化 (provider: {provider})")
    
    async def generate_reply(
        self,
        message: Message,
        context_messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 150,
        system_prompt: Optional[str] = None
    ) -> Optional[str]:
        """生成回復"""
        try:
            if self.provider == "openai":
                return await self._generate_openai(
                    message, context_messages, temperature, max_tokens, system_prompt
                )
            elif self.provider == "mock":
                return await self._generate_mock(message, context_messages)
            else:
                logger.warning(f"未知的 AI 提供商: {self.provider}")
                return None
        except Exception as e:
            logger.error(f"AI 生成失敗: {e}")
            return None
    
    async def _generate_openai(
        self,
        message: Message,
        context_messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str]
    ) -> Optional[str]:
        """使用 OpenAI API 生成回復"""
        try:
            import openai
            
            if not self.api_key:
                logger.warning("OpenAI API key 未設置，使用模擬模式")
                return await self._generate_mock(message, context_messages)
            
            if not self._client:
                self._client = openai.AsyncOpenAI(api_key=self.api_key)
            
            messages = []
            
            # 系統提示詞
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            else:
                messages.append({
                    "role": "system",
                    "content": "你是一個友好的 Telegram 群組助手，會用自然、友好的方式回復消息。"
                })
            
            # 上下文消息
            for ctx_msg in context_messages:
                messages.append({
                    "role": ctx_msg.get("role", "user"),
                    "content": ctx_msg.get("content", "")
                })
            
            # 當前消息
            messages.append({
                "role": "user",
                "content": message.text or ""
            })
            
            response = await self._client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            reply = response.choices[0].message.content
            logger.info(f"AI 生成回復成功 (長度: {len(reply)})")
            return reply
        
        except ImportError:
            logger.warning("openai 庫未安裝，使用模擬模式")
            return await self._generate_mock(message, context_messages)
        except Exception as e:
            logger.error(f"OpenAI API 調用失敗: {e}")
            return await self._generate_mock(message, context_messages)
    
    async def _generate_mock(
        self,
        message: Message,
        context_messages: List[Dict[str, str]]
    ) -> str:
        """模擬 AI 生成（用於測試）"""
        text = message.text or ""
        
        # 簡單的關鍵詞匹配回復
        responses = {
            "你好": ["你好！很高興認識你 😊", "Hi! Nice to meet you!", "嗨呀，最近過得如何？"],
            "謝謝": ["不客氣！", "不用謝 😊", "隨時為你服務！"],
            "再見": ["再見！保持聯繫哦", "拜拜 👋", "期待下次聊天！"],
        }
        
        for keyword, replies in responses.items():
            if keyword in text:
                import random
                return random.choice(replies)
        
        # 默認回復
        default_replies = [
            "這是一個很好的話題！",
            "我理解你的意思。",
            "說得對！",
            "很有趣的想法。",
        ]
        import random
        return random.choice(default_replies)
    
    def set_provider(self, provider: str, api_key: Optional[str] = None):
        """設置 AI 提供商"""
        self.provider = provider
        self.api_key = api_key
        self._client = None
        logger.info(f"AI 提供商已切換為: {provider}")


# 全局實例（可配置）
_global_generator: Optional[AIGenerator] = None


def get_ai_generator() -> AIGenerator:
    """獲取全局 AI 生成器實例"""
    global _global_generator
    if _global_generator is None:
        # 從配置文件讀取
        try:
            from group_ai_service.config import get_group_ai_config
            config = get_group_ai_config()
            provider = config.ai_provider
            api_key = config.ai_api_key
            
            # 如果配置文件中沒有設置，嘗試從環境變量讀取（向後兼容）
            if not provider or provider == "mock":
                import os
                env_provider = os.getenv("AI_PROVIDER")
                if env_provider:
                    provider = env_provider
            
            if not api_key:
                import os
                env_api_key = os.getenv("AI_API_KEY")
                if env_api_key:
                    api_key = env_api_key
            
            _global_generator = AIGenerator(provider=provider, api_key=api_key)
            logger.info(f"AI 生成器已從配置文件初始化 (provider: {provider})")
        except Exception as e:
            logger.warning(f"從配置文件讀取 AI 配置失敗: {e}，使用默認配置")
            # 降級到環境變量
            import os
            provider = os.getenv("AI_PROVIDER", "mock")
            api_key = os.getenv("AI_API_KEY")
            _global_generator = AIGenerator(provider=provider, api_key=api_key)
    return _global_generator

