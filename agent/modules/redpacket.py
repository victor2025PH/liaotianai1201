"""
紅包搶包模塊 - Phase 2: 擬人化版
實現擬人化搶包邏輯（匹配、過濾、延遲、執行、上報）
"""

import asyncio
import logging
import random
import re
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class RedPacketStrategy:
    """紅包策略配置"""
    
    def __init__(
        self,
        strategy_id: str,
        name: str,
        keywords: List[str],
        delay_min: int,
        delay_max: int,
        target_groups: List[int],
        probability: Optional[int] = 100
    ):
        self.strategy_id = strategy_id
        self.name = name
        self.keywords = keywords
        self.delay_min = delay_min  # 毫秒
        self.delay_max = delay_max  # 毫秒
        self.target_groups = target_groups
        self.probability = probability or 100
    
    def matches_keywords(self, text: str) -> Optional[str]:
        """
        檢查文本是否包含關鍵詞（支持模糊匹配）
        
        Returns:
            匹配到的關鍵詞，如果沒有匹配則返回 None
        """
        if not text:
            return None
        
        text_lower = text.lower()
        for keyword in self.keywords:
            keyword_lower = keyword.lower()
            # 支持完全匹配和包含匹配
            if keyword_lower in text_lower or text_lower in keyword_lower:
                return keyword
        return None
    
    def is_target_group(self, group_id: int) -> bool:
        """檢查是否在目標群組列表中"""
        if not self.target_groups:
            return True  # 如果沒有指定目標群組，則所有群組都匹配
        return group_id in self.target_groups
    
    def should_grab(self) -> bool:
        """根據概率決定是否搶包（模擬偶爾沒看到的情況）"""
        if self.probability >= 100:
            return True
        return random.randint(1, 100) <= self.probability


class RedPacketHandler:
    """紅包處理器"""
    
    def __init__(self, client, websocket_client):
        """
        初始化紅包處理器
        
        Args:
            client: Telethon 客戶端（用於操作 Telegram）
            websocket_client: WebSocket 客戶端（用於上報結果）
        """
        self.client = client
        self.websocket_client = websocket_client
        self.strategies: Dict[str, RedPacketStrategy] = {}
        self.active = True
    
    def add_strategy(self, strategy: RedPacketStrategy):
        """添加策略"""
        self.strategies[strategy.strategy_id] = strategy
        logger.info(f"[REDPACKET] 已添加策略: {strategy.name} (ID: {strategy.strategy_id})")
    
    def update_strategy(self, strategy: RedPacketStrategy):
        """更新策略"""
        self.strategies[strategy.strategy_id] = strategy
        logger.info(f"[REDPACKET] 已更新策略: {strategy.name} (ID: {strategy.strategy_id})")
    
    def remove_strategy(self, strategy_id: str):
        """移除策略"""
        if strategy_id in self.strategies:
            strategy = self.strategies.pop(strategy_id)
            logger.info(f"[REDPACKET] 已移除策略: {strategy.name} (ID: {strategy_id})")
    
    async def handle_message(self, event):
        """
        處理 Telegram 消息事件（擬人化搶包邏輯）
        
        Args:
            event: Telethon 消息事件
        """
        if not self.active:
            return
        
        try:
            # 1. 檢查是否為群組消息
            if not hasattr(event, 'chat') or not event.chat:
                return
            
            group_id = event.chat.id
            message_text = event.message.text or ""
            message_id = event.message.id
            
            # 2. 遍歷所有策略，找到匹配的策略
            matched_strategy = None
            matched_keyword = None
            
            for strategy in self.strategies.values():
                # 檢查關鍵詞匹配
                keyword = strategy.matches_keywords(message_text)
                if keyword:
                    # 檢查目標群組
                    if strategy.is_target_group(group_id):
                        matched_strategy = strategy
                        matched_keyword = keyword
                        break
            
            if not matched_strategy:
                return  # 沒有匹配的策略
            
            # 3. 檢查概率（模擬偶爾沒看到的情況）
            if not matched_strategy.should_grab():
                logger.info(
                    f"[REDPACKET] 匹配到紅包 [{matched_keyword}]，但概率未命中，跳過"
                )
                return
            
            # 4. 擬人化延遲（關鍵步驟）
            wait_time = random.uniform(
                matched_strategy.delay_min / 1000.0,
                matched_strategy.delay_max / 1000.0
            )
            
            logger.info(
                f"[REDPACKET] 匹配到紅包 [{matched_keyword}]，模擬思考中... 等待 {wait_time:.2f}秒"
            )
            
            # 執行延遲
            await asyncio.sleep(wait_time)
            
            # 5. 執行搶包操作
            result = await self._grab_redpacket(event, matched_strategy, matched_keyword)
            
            # 6. 上報結果
            await self._report_result(result, matched_strategy)
            
        except Exception as e:
            logger.error(f"[REDPACKET] 處理消息失敗: {e}", exc_info=True)
    
    async def _grab_redpacket(
        self,
        event,
        strategy: RedPacketStrategy,
        matched_keyword: str
    ) -> Dict[str, Any]:
        """
        執行搶包操作
        
        Returns:
            搶包結果字典
        """
        start_time = datetime.now()
        result = {
            "success": False,
            "amount": None,
            "currency": None,
            "error": None,
            "duration_ms": 0,
            "strategy_id": strategy.strategy_id,
            "strategy_name": strategy.name,
            "matched_keyword": matched_keyword,
            "group_id": event.chat.id,
            "message_id": event.message.id
        }
        
        try:
            # TODO: 實現實際的搶包邏輯
            # 這裡需要根據實際的 Telegram 紅包 API 來實現
            # 示例：
            # 1. 點擊紅包按鈕
            # 2. 等待結果
            # 3. 解析金額和幣種
            
            # 臨時實現：模擬搶包
            logger.info(f"[REDPACKET] 正在搶包... (群組: {event.chat.id}, 消息: {event.message.id})")
            
            # 這裡應該調用 Telethon 的 API 來點擊紅包
            # 例如：await event.click(button_index=0)
            # 或者：await event.message.click(data="redpacket_button")
            
            # 模擬結果
            success = random.random() > 0.1  # 90% 成功率
            if success:
                result["success"] = True
                result["amount"] = round(random.uniform(0.01, 10.0), 2)
                result["currency"] = matched_keyword  # 使用匹配到的關鍵詞作為幣種
            else:
                result["error"] = "紅包已被搶完"
            
        except Exception as e:
            logger.error(f"[REDPACKET] 搶包操作失敗: {e}", exc_info=True)
            result["error"] = str(e)
        finally:
            end_time = datetime.now()
            result["duration_ms"] = int((end_time - start_time).total_seconds() * 1000)
        
        return result
    
    async def _report_result(
        self,
        result: Dict[str, Any],
        strategy: RedPacketStrategy
    ):
        """上報搶包結果到 Server"""
        try:
            from agent.websocket.message_handler import MessageHandler, MessageType
            
            message = MessageHandler.create_message(
                MessageType.RESULT,
                {
                    "action": "redpacket_grab",
                    "result": result
                }
            )
            
            if self.websocket_client and self.websocket_client.is_connected():
                await self.websocket_client.send_message(message)
                logger.info(
                    f"[REDPACKET] 已上報結果: "
                    f"成功={result['success']}, "
                    f"金額={result.get('amount')}, "
                    f"幣種={result.get('currency')}, "
                    f"耗時={result['duration_ms']}ms"
                )
            else:
                logger.warning("[REDPACKET] WebSocket 未連接，無法上報結果")
        
        except Exception as e:
            logger.error(f"[REDPACKET] 上報結果失敗: {e}", exc_info=True)
    
    def load_strategy_from_config(self, config: Dict[str, Any]) -> RedPacketStrategy:
        """從配置字典創建策略對象"""
        return RedPacketStrategy(
            strategy_id=config["id"],
            name=config["name"],
            keywords=config["keywords"],
            delay_min=config["delay_min"],
            delay_max=config["delay_max"],
            target_groups=config.get("target_groups", []),
            probability=config.get("probability", 100)
        )
