"""
Lucky Red 紅包遊戲 - AI 系統對接 SDK

從紅包遊戲後端提供的 SDK 複製
版本：2.0
日期：2025-12-02
"""

import httpx
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum


class Currency(str, Enum):
    """支持的幣種"""
    USDT = "usdt"
    TON = "ton"
    STARS = "stars"
    POINTS = "points"


class PacketType(str, Enum):
    """紅包類型"""
    RANDOM = "random"  # 手氣紅包（隨機金額）
    EQUAL = "equal"    # 炸彈紅包（平分金額，帶炸彈數字）


@dataclass
class APIResponse:
    """API 響應"""
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[Dict[str, Any]]
    raw_response: Optional[httpx.Response] = None
    
    @property
    def error_message(self) -> str:
        """獲取錯誤信息"""
        if self.error:
            return self.error.get("detail", str(self.error))
        return ""


class LuckyRedAIError(Exception):
    """Lucky Red API 錯誤"""
    def __init__(self, message: str, response: APIResponse = None):
        self.message = message
        self.response = response
        super().__init__(message)


class LuckyRedAIClient:
    """
    Lucky Red 紅包遊戲 AI API 客戶端
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8080",
        ai_system_id: str = "ai-chat-system",
        timeout: float = 30.0,
        raise_on_error: bool = False
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.ai_system_id = ai_system_id
        self.timeout = timeout
        self.raise_on_error = raise_on_error
    
    def _get_headers(self, telegram_user_id: int) -> Dict[str, str]:
        """生成請求 headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Telegram-User-Id": str(telegram_user_id),
            "X-AI-System-Id": self.ai_system_id,
            "Content-Type": "application/json"
        }
    
    def _handle_response(self, response: httpx.Response) -> APIResponse:
        """處理 API 響應"""
        try:
            data = response.json()
        except Exception:
            data = {"success": False, "error": {"detail": response.text}}
        
        result = APIResponse(
            success=data.get("success", response.status_code == 200),
            data=data.get("data"),
            error=data.get("error") or ({"detail": data.get("detail")} if "detail" in data else None),
            raw_response=response
        )
        
        if response.status_code >= 400:
            result.success = False
            if not result.error:
                result.error = {"detail": f"HTTP {response.status_code}"}
        
        if self.raise_on_error and not result.success:
            raise LuckyRedAIError(result.error_message, result)
        
        return result
    
    # ==================== 同步 API ====================
    
    def check_health(self) -> APIResponse:
        """檢查 API 健康狀態"""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/api/v2/ai/status")
            return self._handle_response(response)
    
    def get_balance(self, telegram_user_id: int) -> APIResponse:
        """查詢用戶餘額"""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/v2/ai/wallet/balance",
                headers=self._get_headers(telegram_user_id)
            )
            return self._handle_response(response)
    
    def get_profile(self, telegram_user_id: int) -> APIResponse:
        """獲取用戶資料"""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/v2/ai/user/profile",
                headers=self._get_headers(telegram_user_id)
            )
            return self._handle_response(response)
    
    def send_packet(
        self,
        telegram_user_id: int,
        total_amount: float,
        total_count: int,
        currency: Union[str, Currency] = Currency.USDT,
        packet_type: Union[str, PacketType] = PacketType.RANDOM,
        message: str = "🤖 AI 紅包",
        chat_id: Optional[int] = None,
        bomb_number: Optional[int] = None
    ) -> APIResponse:
        """發送紅包"""
        if isinstance(currency, Currency):
            currency = currency.value
        if isinstance(packet_type, PacketType):
            packet_type = packet_type.value
        
        payload = {
            "currency": currency,
            "packet_type": packet_type,
            "total_amount": total_amount,
            "total_count": total_count,
            "message": message
        }
        
        if chat_id is not None:
            payload["chat_id"] = chat_id
        if bomb_number is not None:
            payload["bomb_number"] = bomb_number
        
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/v2/ai/packets/send",
                headers=self._get_headers(telegram_user_id),
                json=payload
            )
            return self._handle_response(response)
    
    def send_random_packet(
        self,
        telegram_user_id: int,
        total_amount: float,
        total_count: int,
        currency: str = "usdt",
        message: str = "🎲 手氣紅包"
    ) -> APIResponse:
        """發送手氣紅包（便捷方法）"""
        return self.send_packet(
            telegram_user_id=telegram_user_id,
            total_amount=total_amount,
            total_count=total_count,
            currency=currency,
            packet_type=PacketType.RANDOM,
            message=message
        )
    
    def send_bomb_packet(
        self,
        telegram_user_id: int,
        total_amount: float,
        total_count: int,
        bomb_number: int,
        currency: str = "usdt",
        message: str = "💣 炸彈紅包"
    ) -> APIResponse:
        """發送炸彈紅包（便捷方法）"""
        if total_count not in [5, 10]:
            return APIResponse(
                success=False,
                data=None,
                error={"detail": "炸彈紅包份數必須是 5（雙雷）或 10（單雷）"}
            )
        
        return self.send_packet(
            telegram_user_id=telegram_user_id,
            total_amount=total_amount,
            total_count=total_count,
            currency=currency,
            packet_type=PacketType.EQUAL,
            message=message,
            bomb_number=bomb_number
        )
    
    def claim_packet(
        self,
        telegram_user_id: int,
        packet_uuid: str
    ) -> APIResponse:
        """領取紅包"""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/v2/ai/packets/claim",
                headers=self._get_headers(telegram_user_id),
                json={"packet_uuid": packet_uuid}
            )
            return self._handle_response(response)
    
    def transfer(
        self,
        from_user_id: int,
        to_user_id: int,
        amount: float,
        currency: str = "usdt",
        note: str = ""
    ) -> APIResponse:
        """內部轉帳（零手續費）"""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/v2/ai/wallet/transfer",
                headers=self._get_headers(from_user_id),
                json={
                    "to_user_id": to_user_id,
                    "currency": currency,
                    "amount": amount,
                    "note": note
                }
            )
            return self._handle_response(response)
    
    def get_packet_info(
        self,
        telegram_user_id: int,
        packet_uuid: str
    ) -> APIResponse:
        """獲取紅包詳情"""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/v2/ai/packets/{packet_uuid}",
                headers=self._get_headers(telegram_user_id)
            )
            return self._handle_response(response)
    
    # ==================== 異步 API ====================
    
    async def async_check_health(self) -> APIResponse:
        """異步檢查 API 健康狀態"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/v2/ai/status")
            return self._handle_response(response)
    
    async def async_get_balance(self, telegram_user_id: int) -> APIResponse:
        """異步查詢用戶餘額"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v2/ai/wallet/balance",
                headers=self._get_headers(telegram_user_id)
            )
            return self._handle_response(response)
    
    async def async_get_profile(self, telegram_user_id: int) -> APIResponse:
        """異步獲取用戶資料"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v2/ai/user/profile",
                headers=self._get_headers(telegram_user_id)
            )
            return self._handle_response(response)
    
    async def async_send_packet(
        self,
        telegram_user_id: int,
        total_amount: float,
        total_count: int,
        **kwargs
    ) -> APIResponse:
        """異步發送紅包"""
        payload = {
            "currency": kwargs.get("currency", "usdt"),
            "packet_type": kwargs.get("packet_type", "random"),
            "total_amount": total_amount,
            "total_count": total_count,
            "message": kwargs.get("message", "🤖 AI 紅包")
        }
        if kwargs.get("chat_id"):
            payload["chat_id"] = kwargs["chat_id"]
        if kwargs.get("bomb_number") is not None:
            payload["bomb_number"] = kwargs["bomb_number"]
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v2/ai/packets/send",
                headers=self._get_headers(telegram_user_id),
                json=payload
            )
            return self._handle_response(response)
    
    async def async_claim_packet(
        self,
        telegram_user_id: int,
        packet_uuid: str
    ) -> APIResponse:
        """異步領取紅包"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v2/ai/packets/claim",
                headers=self._get_headers(telegram_user_id),
                json={"packet_uuid": packet_uuid}
            )
            return self._handle_response(response)
    
    async def async_transfer(
        self,
        from_user_id: int,
        to_user_id: int,
        amount: float,
        currency: str = "usdt",
        note: str = ""
    ) -> APIResponse:
        """異步內部轉帳"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v2/ai/wallet/transfer",
                headers=self._get_headers(from_user_id),
                json={
                    "to_user_id": to_user_id,
                    "currency": currency,
                    "amount": amount,
                    "note": note
                }
            )
            return self._handle_response(response)
    
    async def async_get_packet_info(
        self,
        telegram_user_id: int,
        packet_uuid: str
    ) -> APIResponse:
        """異步獲取紅包詳情"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v2/ai/packets/{packet_uuid}",
                headers=self._get_headers(telegram_user_id)
            )
            return self._handle_response(response)


# 創建全局客戶端實例的工廠函數
_client_instance: Optional[LuckyRedAIClient] = None

def get_lucky_red_client(
    api_key: str = None,
    base_url: str = None
) -> LuckyRedAIClient:
    """獲取或創建 Lucky Red 客戶端實例"""
    global _client_instance
    
    if _client_instance is None or api_key or base_url:
        from app.core.config import get_settings
        settings = get_settings()
        
        _client_instance = LuckyRedAIClient(
            api_key=api_key or getattr(settings, 'lucky_red_api_key', 'test-key'),
            base_url=base_url or getattr(settings, 'lucky_red_api_url', 'http://localhost:8080'),
            ai_system_id="liaotian-ai-system"
        )
    
    return _client_instance
