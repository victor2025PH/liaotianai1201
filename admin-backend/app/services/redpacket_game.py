"""
紅包遊戲陪玩服務

讓 AI 帳號陪用戶玩紅包遊戲：
- 自動搶紅包
- 發送紅包引導
- 根據結果互動聊天
"""

import asyncio
import random
import logging
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from app.lib.lucky_red_sdk import LuckyRedAIClient

logger = logging.getLogger(__name__)


class GameAction(str, Enum):
    """遊戲動作"""
    SEND_RANDOM = "send_random"      # 發手氣紅包
    SEND_BOMB = "send_bomb"          # 發炸彈紅包
    CLAIM = "claim"                  # 搶紅包
    CHAT = "chat"                    # 聊天互動


@dataclass
class AIPlayer:
    """AI 玩家"""
    telegram_id: int
    name: str
    balance: float = 0
    personality: str = "friendly"  # friendly, competitive, cautious
    active: bool = True
    last_action: Optional[datetime] = None
    
    # 統計
    packets_sent: int = 0
    packets_claimed: int = 0
    total_won: float = 0
    total_lost: float = 0
    bombs_hit: int = 0


@dataclass  
class GameSession:
    """遊戲會話"""
    target_user_id: int  # 陪玩對象
    ai_players: List[AIPlayer] = field(default_factory=list)
    active: bool = True
    start_time: datetime = field(default_factory=datetime.now)
    
    # 遊戲配置
    auto_claim_delay_min: float = 1.0   # 搶紅包最小延遲（秒）
    auto_claim_delay_max: float = 5.0   # 搶紅包最大延遲
    send_interval_min: int = 60          # 發紅包最小間隔（秒）
    send_interval_max: int = 300         # 發紅包最大間隔
    
    # 紅包配置
    amount_min: float = 1.0
    amount_max: float = 10.0
    count_min: int = 3
    count_max: int = 10


class RedpacketGameService:
    """紅包遊戲陪玩服務"""
    
    def __init__(self, api_key: str, api_url: str):
        self.client = LuckyRedAIClient(
            api_key=api_key,
            base_url=api_url,
            ai_system_id="liaotian-game-service"
        )
        self.sessions: Dict[int, GameSession] = {}
        
        # 聊天模板
        self.chat_templates = {
            "claim_success": [
                "哈哈，手氣不錯！🎉",
                "謝謝紅包！祝你發大財！💰",
                "運氣真好！再來一個？",
                "收到！今天運氣爆棚！✨",
            ],
            "claim_lucky": [
                "哇！手氣王！🏆",
                "這運氣也太好了吧！",
                "最佳手氣！今天買彩票去！🎰",
            ],
            "claim_bomb": [
                "💣 啊！踩雷了！",
                "炸到我了...下次小心！",
                "雷區警報！我中招了 😭",
                "踩雷賠錢，心態崩了...",
            ],
            "send_random": [
                "來個紅包，大家搶！🧧",
                "發個紅包活躍氣氛！",
                "手氣紅包來了，看看誰運氣好！",
                "紅包雨來襲！快搶！💰",
            ],
            "send_bomb": [
                "💣 炸彈紅包！誰敢來？",
                "膽大的來！炸彈紅包！",
                "刺激一下！炸彈紅包發出！",
                "考驗運氣的時候到了！💣",
            ],
            "encourage_play": [
                "一起來玩紅包遊戲吧！",
                "紅包遊戲超好玩，要不要試試？",
                "發個紅包互動一下？",
            ],
        }
    
    async def start_session(
        self,
        target_user_id: int,
        ai_player_ids: List[int]
    ) -> GameSession:
        """開始遊戲會話"""
        
        # 獲取 AI 玩家信息
        ai_players = []
        for tg_id in ai_player_ids:
            result = await self.client.async_get_profile(tg_id)
            if result.success:
                player = AIPlayer(
                    telegram_id=tg_id,
                    name=result.data.get("first_name", f"AI-{tg_id}"),
                    balance=0
                )
                # 獲取餘額
                balance_result = await self.client.async_get_balance(tg_id)
                if balance_result.success:
                    player.balance = balance_result.data.get("balances", {}).get("usdt", 0)
                ai_players.append(player)
            else:
                logger.warning(f"無法獲取 AI 玩家信息: {tg_id}")
        
        session = GameSession(
            target_user_id=target_user_id,
            ai_players=ai_players
        )
        
        self.sessions[target_user_id] = session
        logger.info(f"遊戲會話已開始: 用戶 {target_user_id}, AI 玩家: {len(ai_players)}")
        
        return session
    
    async def claim_packet(
        self,
        session: GameSession,
        packet_uuid: str,
        claimer_id: Optional[int] = None
    ) -> Dict:
        """AI 搶紅包"""
        
        # 選擇一個 AI 玩家搶紅包
        if claimer_id:
            player = next((p for p in session.ai_players if p.telegram_id == claimer_id), None)
        else:
            # 隨機選擇一個活躍的玩家
            active_players = [p for p in session.ai_players if p.active]
            if not active_players:
                return {"success": False, "error": "沒有可用的 AI 玩家"}
            player = random.choice(active_players)
        
        if not player:
            return {"success": False, "error": "找不到指定的 AI 玩家"}
        
        # 隨機延遲，模擬真人
        delay = random.uniform(session.auto_claim_delay_min, session.auto_claim_delay_max)
        await asyncio.sleep(delay)
        
        # 搶紅包
        result = await self.client.async_claim_packet(
            telegram_user_id=player.telegram_id,
            packet_uuid=packet_uuid
        )
        
        response = {
            "success": result.success,
            "player": player.name,
            "player_id": player.telegram_id,
            "delay": delay
        }
        
        if result.success:
            data = result.data
            player.packets_claimed += 1
            player.last_action = datetime.now()
            
            amount = data.get("claimed_amount", 0)
            is_bomb = data.get("is_bomb", False)
            is_lucky = data.get("is_luckiest", False)
            
            response.update({
                "amount": amount,
                "is_bomb": is_bomb,
                "is_lucky": is_lucky,
                "new_balance": data.get("new_balance"),
                "chat_message": self._get_chat_message(
                    "claim_bomb" if is_bomb else ("claim_lucky" if is_lucky else "claim_success")
                )
            })
            
            if is_bomb:
                player.bombs_hit += 1
                player.total_lost += data.get("penalty_amount", 0)
            else:
                player.total_won += amount
                
            logger.info(f"AI {player.name} 搶到紅包: {amount} USDT, 踩雷: {is_bomb}")
        else:
            response["error"] = result.error_message
            
        return response
    
    async def send_packet(
        self,
        session: GameSession,
        sender_id: Optional[int] = None,
        packet_type: str = "random",
        amount: Optional[float] = None,
        count: Optional[int] = None,
        bomb_number: Optional[int] = None
    ) -> Dict:
        """AI 發送紅包"""
        
        # 選擇發送者
        if sender_id:
            player = next((p for p in session.ai_players if p.telegram_id == sender_id), None)
        else:
            # 選擇餘額最多的玩家
            active_players = [p for p in session.ai_players if p.active and p.balance > 1]
            if not active_players:
                return {"success": False, "error": "沒有餘額足夠的 AI 玩家"}
            player = max(active_players, key=lambda p: p.balance)
        
        if not player:
            return {"success": False, "error": "找不到指定的 AI 玩家"}
        
        # 隨機金額和份數
        if amount is None:
            amount = round(random.uniform(session.amount_min, session.amount_max), 2)
        if count is None:
            count = random.randint(session.count_min, session.count_max)
        
        # 確保餘額足夠
        if player.balance < amount:
            amount = player.balance * 0.5  # 用一半餘額
        
        # 炸彈紅包
        if packet_type == "equal":
            count = random.choice([5, 10])  # 雙雷或單雷
            if bomb_number is None:
                bomb_number = random.randint(0, 9)
            message = self._get_chat_message("send_bomb")
        else:
            message = self._get_chat_message("send_random")
        
        # 發送紅包
        result = await self.client.async_send_packet(
            telegram_user_id=player.telegram_id,
            total_amount=amount,
            total_count=count,
            packet_type=packet_type,
            message=message,
            bomb_number=bomb_number if packet_type == "equal" else None
        )
        
        response = {
            "success": result.success,
            "player": player.name,
            "player_id": player.telegram_id,
            "amount": amount,
            "count": count,
            "packet_type": packet_type
        }
        
        if result.success:
            data = result.data
            player.packets_sent += 1
            player.last_action = datetime.now()
            player.balance = data.get("remaining_balance", player.balance - amount)
            
            response.update({
                "packet_id": data.get("packet_id"),
                "share_url": data.get("share_url"),
                "expires_at": data.get("expires_at"),
                "chat_message": message
            })
            
            if packet_type == "equal":
                response["bomb_number"] = bomb_number
                
            logger.info(f"AI {player.name} 發送紅包: {amount} USDT, {count} 份")
        else:
            response["error"] = result.error_message
            
        return response
    
    async def auto_play_round(self, session: GameSession) -> List[Dict]:
        """自動玩一輪遊戲"""
        actions = []
        
        # 隨機決定動作
        action_type = random.choices(
            [GameAction.SEND_RANDOM, GameAction.SEND_BOMB, GameAction.CHAT],
            weights=[0.6, 0.2, 0.2]  # 60% 發手氣, 20% 發炸彈, 20% 聊天
        )[0]
        
        if action_type == GameAction.SEND_RANDOM:
            result = await self.send_packet(session, packet_type="random")
            actions.append({"action": "send_random", **result})
            
        elif action_type == GameAction.SEND_BOMB:
            result = await self.send_packet(session, packet_type="equal")
            actions.append({"action": "send_bomb", **result})
            
        elif action_type == GameAction.CHAT:
            message = self._get_chat_message("encourage_play")
            actions.append({
                "action": "chat",
                "message": message
            })
        
        return actions
    
    def _get_chat_message(self, category: str) -> str:
        """獲取聊天消息"""
        templates = self.chat_templates.get(category, [""])
        return random.choice(templates)
    
    def get_session(self, target_user_id: int) -> Optional[GameSession]:
        """獲取遊戲會話"""
        return self.sessions.get(target_user_id)
    
    def stop_session(self, target_user_id: int) -> bool:
        """停止遊戲會話"""
        if target_user_id in self.sessions:
            self.sessions[target_user_id].active = False
            logger.info(f"遊戲會話已停止: 用戶 {target_user_id}")
            return True
        return False
    
    def get_session_stats(self, target_user_id: int) -> Optional[Dict]:
        """獲取會話統計"""
        session = self.sessions.get(target_user_id)
        if not session:
            return None
        
        return {
            "target_user_id": target_user_id,
            "active": session.active,
            "start_time": session.start_time.isoformat(),
            "ai_players": [
                {
                    "id": p.telegram_id,
                    "name": p.name,
                    "balance": p.balance,
                    "packets_sent": p.packets_sent,
                    "packets_claimed": p.packets_claimed,
                    "total_won": p.total_won,
                    "total_lost": p.total_lost,
                    "bombs_hit": p.bombs_hit
                }
                for p in session.ai_players
            ]
        }


# 全局服務實例
_game_service: Optional[RedpacketGameService] = None


def get_game_service(api_key: str = None, api_url: str = None) -> RedpacketGameService:
    """獲取遊戲服務實例"""
    global _game_service
    
    if _game_service is None or api_key or api_url:
        _game_service = RedpacketGameService(
            api_key=api_key or "",
            api_url=api_url or "http://localhost:8080"
        )
    
    return _game_service
