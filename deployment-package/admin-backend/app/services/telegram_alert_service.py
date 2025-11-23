"""
Telegram 告警通知服务
提供增强的 Telegram Bot 实时告警功能
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import deque
import httpx

logger = logging.getLogger(__name__)


class TelegramAlertService:
    """Telegram 告警通知服务"""
    
    def __init__(self, bot_token: Optional[str] = None, default_chat_id: Optional[str] = None):
        """
        初始化 Telegram 告警服务
        
        Args:
            bot_token: Telegram Bot Token
            default_chat_id: 默认 Chat ID
        """
        self.bot_token = bot_token
        self.default_chat_id = default_chat_id
        self.api_base_url = "https://api.telegram.org"
        self.enabled = bool(bot_token and default_chat_id)
        
        # 告警聚合（避免告警风暴）
        self.alert_buffer: deque = deque(maxlen=100)  # 最近100条告警
        self.alert_cooldown: Dict[str, datetime] = {}  # 告警冷却时间
        self.cooldown_seconds = 300  # 5分钟内相同告警只发送一次
        
        # 统计信息
        self.stats = {
            "sent": 0,
            "failed": 0,
            "suppressed": 0,  # 被抑制的告警（冷却期内）
        }
    
    def _get_alert_key(self, alert: Dict[str, Any]) -> str:
        """
        生成告警唯一键（用于去重和冷却）
        
        Args:
            alert: 告警字典
        
        Returns:
            告警唯一键
        """
        alert_type = alert.get("alert_type", "unknown")
        account_id = alert.get("account_id", "")
        message = alert.get("message", "")[:50]  # 只取前50个字符
        return f"{alert_type}:{account_id}:{hash(message)}"
    
    def _should_send_alert(self, alert: Dict[str, Any]) -> bool:
        """
        判断是否应该发送告警（冷却检查）
        
        Args:
            alert: 告警字典
        
        Returns:
            是否应该发送
        """
        alert_key = self._get_alert_key(alert)
        now = datetime.now()
        
        # 检查冷却时间
        if alert_key in self.alert_cooldown:
            last_sent = self.alert_cooldown[alert_key]
            if (now - last_sent).total_seconds() < self.cooldown_seconds:
                self.stats["suppressed"] += 1
                logger.debug(f"告警在冷却期内，跳过发送: {alert_key}")
                return False
        
        # 更新冷却时间
        self.alert_cooldown[alert_key] = now
        
        # 清理过期的冷却记录（保留最近1小时）
        expired_keys = [
            k for k, v in self.alert_cooldown.items()
            if (now - v).total_seconds() > 3600
        ]
        for k in expired_keys:
            del self.alert_cooldown[k]
        
        return True
    
    def _format_alert_message(self, alert: Dict[str, Any]) -> str:
        """
        格式化告警消息（HTML格式）
        
        Args:
            alert: 告警字典
        
        Returns:
            格式化的消息文本
        """
        alert_level = alert.get("alert_level", alert.get("alert_type", "info"))
        alert_type = alert.get("alert_type", "unknown")
        message = alert.get("message", "未知告警")
        account_id = alert.get("account_id")
        timestamp = alert.get("timestamp", datetime.now())
        
        # 格式化时间
        if isinstance(timestamp, str):
            time_str = timestamp
        elif isinstance(timestamp, datetime):
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            time_str = str(timestamp)
        
        # 选择表情符号
        emoji_map = {
            "error": "🔴",
            "critical": "🔴",
            "warning": "🟡",
            "info": "🔵",
            "success": "🟢",
        }
        emoji = emoji_map.get(alert_level.lower(), "⚪")
        
        # 构建消息
        msg_parts = [
            f"{emoji} <b>告警通知</b>",
            "",
            f"<b>級別：</b>{alert_level.upper()}",
            f"<b>類型：</b>{alert_type}",
            f"<b>時間：</b>{time_str}",
        ]
        
        if account_id:
            msg_parts.append(f"<b>賬號：</b>{account_id}")
        
        msg_parts.extend([
            "",
            f"<b>消息：</b>",
            message,
        ])
        
        # 添加详细信息（如果有）
        if "details" in alert:
            msg_parts.append("")
            msg_parts.append("<b>詳情：</b>")
            for key, value in alert["details"].items():
                msg_parts.append(f"  • {key}: {value}")
        
        return "\n".join(msg_parts)
    
    async def send_alert(
        self,
        alert: Dict[str, Any],
        chat_id: Optional[str] = None,
        retry_count: int = 3
    ) -> bool:
        """
        发送告警通知
        
        Args:
            alert: 告警字典
            chat_id: Chat ID（可选，默认使用配置的）
            retry_count: 重试次数
        
        Returns:
            是否发送成功
        """
        if not self.enabled:
            logger.debug("Telegram 告警服务未启用")
            return False
        
        # 检查是否应该发送（冷却检查）
        if not self._should_send_alert(alert):
            return False
        
        chat_id = chat_id or self.default_chat_id
        if not chat_id:
            logger.warning("Telegram Chat ID 未配置")
            return False
        
        # 格式化消息
        message = self._format_alert_message(alert)
        
        # 发送消息（带重试）
        for attempt in range(retry_count):
            try:
                url = f"{self.api_base_url}/bot{self.bot_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                }
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                
                self.stats["sent"] += 1
                logger.info(f"Telegram 告警已发送: {alert.get('alert_type', 'unknown')}")
                
                # 记录到告警缓冲区
                self.alert_buffer.append({
                    "alert": alert,
                    "sent_at": datetime.now(),
                    "success": True
                })
                
                return True
                
            except httpx.TimeoutException:
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    logger.warning(f"Telegram 请求超时，{wait_time}秒后重试 ({attempt + 1}/{retry_count})")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Telegram 请求超时，已达最大重试次数")
                    self.stats["failed"] += 1
                    return False
                    
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}"
                if e.response.status_code == 429:  # Rate limit
                    # 解析重试时间
                    retry_after = int(e.response.headers.get("Retry-After", 60))
                    logger.warning(f"Telegram 速率限制，{retry_after}秒后重试")
                    await asyncio.sleep(retry_after)
                    continue
                else:
                    logger.error(f"Telegram 请求失败: {error_msg}")
                    if attempt < retry_count - 1:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        self.stats["failed"] += 1
                        return False
                        
            except Exception as e:
                logger.error(f"发送 Telegram 告警失败: {e}", exc_info=True)
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    self.stats["failed"] += 1
                    return False
        
        return False
    
    async def send_batch_alerts(
        self,
        alerts: List[Dict[str, Any]],
        chat_id: Optional[str] = None,
        batch_size: int = 5
    ) -> Dict[str, int]:
        """
        批量发送告警（避免消息过多）
        
        Args:
            alerts: 告警列表
            chat_id: Chat ID
            batch_size: 每批发送数量
        
        Returns:
            发送统计
        """
        results = {
            "sent": 0,
            "failed": 0,
            "suppressed": 0
        }
        
        # 如果告警太多，发送摘要
        if len(alerts) > batch_size:
            summary_alert = {
                "alert_type": "summary",
                "alert_level": "info",
                "message": f"检测到 {len(alerts)} 个告警，以下是前 {batch_size} 个",
                "timestamp": datetime.now(),
                "details": {
                    "total_alerts": len(alerts),
                    "showing": batch_size
                }
            }
            if await self.send_alert(summary_alert, chat_id):
                results["sent"] += 1
            else:
                results["failed"] += 1
            
            # 只发送前几个
            alerts = alerts[:batch_size]
        
        # 发送每个告警
        for alert in alerts:
            if self._should_send_alert(alert):
                if await self.send_alert(alert, chat_id):
                    results["sent"] += 1
                else:
                    results["failed"] += 1
            else:
                results["suppressed"] += 1
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "enabled": self.enabled,
            "sent": self.stats["sent"],
            "failed": self.stats["failed"],
            "suppressed": self.stats["suppressed"],
            "buffer_size": len(self.alert_buffer),
            "cooldown_size": len(self.alert_cooldown),
        }


# 全局实例
_telegram_alert_service: Optional[TelegramAlertService] = None


def get_telegram_alert_service() -> TelegramAlertService:
    """获取全局 Telegram 告警服务实例"""
    global _telegram_alert_service
    if _telegram_alert_service is None:
        from app.core.config import get_settings
        settings = get_settings()
        
        bot_token = getattr(settings, 'telegram_bot_token', None) or ""
        # 优先使用 telegram_chat_id，如果没有则尝试从 group_ai 配置获取
        chat_id = getattr(settings, 'telegram_chat_id', None) or ""
        if not chat_id:
            try:
                from group_ai_service.config import get_group_ai_config
                group_ai_config = get_group_ai_config()
                chat_id = getattr(group_ai_config, 'alert_telegram_chat_id', None) or ""
            except Exception:
                pass
        
        _telegram_alert_service = TelegramAlertService(
            bot_token=bot_token,
            default_chat_id=chat_id
        )
    return _telegram_alert_service

