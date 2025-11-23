"""
游戏引导服务 - 在红包游戏过程中提供实时聊天引导
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from group_ai_service.game_api_client import GameEvent, GameStatus
from group_ai_service.account_manager import AccountManager
from group_ai_service.models.account import AccountConfig

logger = logging.getLogger(__name__)


class GameGuideService:
    """游戏引导服务 - 提供实时游戏引导消息"""
    
    def __init__(self, dialogue_manager=None, account_manager: Optional[AccountManager] = None):
        """
        初始化游戏引导服务
        
        Args:
            dialogue_manager: 对话管理器（用于发送消息）
            account_manager: 账号管理器（用于获取账号和客户端）
        """
        self.dialogue_manager = dialogue_manager
        self.account_manager = account_manager or AccountManager()
        self.guide_templates = self._load_templates()
        logger.info("GameGuideService 初始化完成")
    
    def _load_templates(self) -> Dict[str, str]:
        """加载引导消息模板（优化版 - 更吸引人、更有教学性）"""
        return {
            "game_start": (
                "🎮 红包游戏开始啦！\n\n"
                "👋 欢迎所有玩家参与！\n\n"
                "📖 游戏规则很简单：\n"
                "• 点击红包按钮即可参与\n"
                "• 红包金额随机分配，公平公正\n"
                "• 先到先得，抢完为止\n"
                "• 手速越快，机会越大！\n\n"
                "💡 小贴士：准备好你的手指，红包随时可能出现！\n\n"
                "祝大家好运！💰✨"
            ),
            "redpacket_sent": (
                "🎁 超级红包来啦！\n\n"
                "💰 总金额: {amount} {token}\n"
                "📦 总份数: {count} 份\n"
                "⏰ 剩余: {remaining} 份\n\n"
                "💡 小贴士: 先到先得，手速要快哦！\n"
                "🚀 点击下方按钮立即参与！\n\n"
                "⏳ 机会稍纵即逝，不要犹豫！"
            ),
            "redpacket_claimed": (
                "🎉 恭喜！你抢到了 {amount} {token}！\n\n"
                "📊 红包剩余: {remaining} 份\n"
                "💪 继续加油，还有机会！\n\n"
                "💡 提示：如果还有剩余，可以继续参与哦！"
            ),
            "redpacket_almost_gone": (
                "⚡ 紧急提醒！红包快被抢完了！\n\n"
                "🔥 剩余仅: {remaining} 份\n"
                "⏰ 时间紧迫，抓紧最后机会！\n\n"
                "💡 这是最后的机会了，不要错过！\n"
                "🚀 立即点击按钮参与！"
            ),
            "game_end": (
                "🎊 游戏圆满结束！\n\n"
                "🙏 感谢所有玩家的热情参与！\n\n"
                "📊 本次游戏统计：\n"
                "• 总金额: {total_amount} {token}\n"
                "• 参与人数: {participants} 人\n"
                "• 发放红包: {redpacket_count} 个\n\n"
                "🎉 恭喜所有获奖的玩家！\n"
                "💪 没获奖的玩家也不要灰心，下次还有机会！\n\n"
                "⏰ 期待下次游戏，我们不见不散！"
            ),
            "result_announced": (
                "📊 游戏结果正式公布\n\n"
                "{summary}\n\n"
                "🏆 恭喜所有获奖玩家！\n"
                "👏 感谢所有参与者的支持！\n\n"
                "💡 想查看完整排行榜？点击下方按钮！\n"
                "📈 想了解详细统计？查看游戏报告！\n\n"
                "🎮 期待下次游戏，再创佳绩！"
            )
        }
    
    async def handle_game_event(self, event: GameEvent):
        """
        处理游戏事件并发送引导消息
        
        Args:
            event: 游戏事件
        """
        try:
            if event.event_type == "GAME_START":
                await self.on_game_start(event)
            elif event.event_type == "REDPACKET_SENT":
                await self.on_redpacket_sent(event)
            elif event.event_type == "REDPACKET_CLAIMED":
                await self.on_redpacket_claimed(event)
            elif event.event_type == "GAME_END":
                await self.on_game_end(event)
            elif event.event_type == "RESULT_ANNOUNCED":
                await self.on_result_announced(event)
            else:
                logger.debug(f"未处理的游戏事件类型: {event.event_type}")
        except Exception as e:
            logger.error(f"处理游戏事件失败: {e}", exc_info=True)
    
    async def on_game_start(self, event: GameEvent):
        """游戏开始时的引导"""
        try:
            group_id = event.group_id
            message = self.guide_templates["game_start"]
            
            # 如果事件中有游戏ID，添加到消息中
            if event.game_id:
                message = f"🎮 游戏 #{event.game_id} 开始啦！\n\n" + message.split("\n\n", 1)[1] if "\n\n" in message else message
            
            # 获取监听该群组的账号
            accounts = self._get_accounts_for_group(group_id)
            
            if not accounts:
                logger.warning(f"群组 {group_id} 没有可用的账号发送引导消息")
                return
            
            # 发送引导消息
            for account in accounts:
                try:
                    if account.status.value == "online" and account.client:
                        await self._send_message(
                            client=account.client,
                            chat_id=group_id,
                            text=message
                        )
                        logger.info(f"已发送游戏开始引导（账号: {account.account_id}, 群组: {group_id}）")
                except Exception as e:
                    logger.error(f"发送游戏开始引导失败（账号: {account.account_id}）: {e}")
        except Exception as e:
            logger.error(f"处理游戏开始事件失败: {e}", exc_info=True)
    
    async def on_redpacket_sent(self, event: GameEvent):
        """红包发送时的引导"""
        try:
            group_id = event.group_id
            payload = event.payload
            
            # 从事件中获取红包信息
            amount = payload.get("amount", 0)
            count = payload.get("count", 0)
            token = payload.get("token", "USDT")
            remaining = payload.get("remaining_count", count)
            
            message = self.guide_templates["redpacket_sent"].format(
                amount=amount,
                token=token,
                count=count,
                remaining=remaining
            )
            
            # 获取监听该群组的账号
            accounts = self._get_accounts_for_group(group_id)
            
            for account in accounts:
                try:
                    if account.status.value == "online" and account.client:
                        await self._send_message(
                            client=account.client,
                            chat_id=group_id,
                            text=message
                        )
                        logger.info(f"已发送红包发送引导（账号: {account.account_id}, 群组: {group_id}）")
                except Exception as e:
                    logger.error(f"发送红包发送引导失败（账号: {account.account_id}）: {e}")
        except Exception as e:
            logger.error(f"处理红包发送事件失败: {e}", exc_info=True)
    
    async def on_redpacket_claimed(self, event: GameEvent):
        """红包被领取时的引导"""
        try:
            group_id = event.group_id
            payload = event.payload
            
            # 检查是否是自己领取的
            account_id = payload.get("account_id")
            if not account_id:
                return
            
            amount = payload.get("amount", 0)
            token = payload.get("token", "USDT")
            remaining = payload.get("remaining_count", 0)
            
            # 如果剩余数量很少，发送提醒
            if remaining <= 3 and remaining > 0:
                message = self.guide_templates["redpacket_almost_gone"].format(
                    remaining=remaining
                )
                
                accounts = self._get_accounts_for_group(group_id)
                for account in accounts:
                    try:
                        if account.status.value == "online" and account.client:
                            await self._send_message(
                                client=account.client,
                                chat_id=group_id,
                                text=message
                            )
                            logger.info(f"已发送红包快抢完提醒（账号: {account.account_id}, 群组: {group_id}）")
                    except Exception as e:
                        logger.error(f"发送红包快抢完提醒失败（账号: {account.account_id}）: {e}")
        except Exception as e:
            logger.error(f"处理红包被领取事件失败: {e}", exc_info=True)
    
    async def on_game_end(self, event: GameEvent):
        """游戏结束时的引导"""
        try:
            group_id = event.group_id
            payload = event.payload
            
            total_amount = payload.get("total_amount", 0)
            token = payload.get("token", "USDT")
            participants = payload.get("participants", 0)
            redpacket_count = payload.get("redpacket_count", 1)  # 红包数量
            
            message = self.guide_templates["game_end"].format(
                total_amount=total_amount,
                token=token,
                participants=participants,
                redpacket_count=redpacket_count
            )
            
            # 获取监听该群组的账号
            accounts = self._get_accounts_for_group(group_id)
            
            for account in accounts:
                try:
                    if account.status.value == "online" and account.client:
                        await self._send_message(
                            client=account.client,
                            chat_id=group_id,
                            text=message
                        )
                        logger.info(f"已发送游戏结束引导（账号: {account.account_id}, 群组: {group_id}）")
                except Exception as e:
                    logger.error(f"发送游戏结束引导失败（账号: {account.account_id}）: {e}")
        except Exception as e:
            logger.error(f"处理游戏结束事件失败: {e}", exc_info=True)
    
    async def on_result_announced(self, event: GameEvent):
        """结果公布时的引导"""
        try:
            group_id = event.group_id
            payload = event.payload
            
            summary = payload.get("summary", "游戏结果已公布")
            
            message = self.guide_templates["result_announced"].format(
                summary=summary
            )
            
            # 获取监听该群组的账号
            accounts = self._get_accounts_for_group(group_id)
            
            for account in accounts:
                try:
                    if account.status.value == "online" and account.client:
                        await self._send_message(
                            client=account.client,
                            chat_id=group_id,
                            text=message
                        )
                        logger.info(f"已发送结果公布引导（账号: {account.account_id}, 群组: {group_id}）")
                except Exception as e:
                    logger.error(f"发送结果公布引导失败（账号: {account.account_id}）: {e}")
        except Exception as e:
            logger.error(f"处理结果公布事件失败: {e}", exc_info=True)
    
    def _get_accounts_for_group(self, group_id: int) -> List:
        """获取监听指定群组的账号列表"""
        accounts = []
        for account_id, account in self.account_manager.accounts.items():
            # 检查账号是否监听该群组
            if not account.config.group_ids or group_id in account.config.group_ids:
                accounts.append(account)
        return accounts
    
    async def _send_message(
        self,
        client,
        chat_id: int,
        text: str
    ):
        """发送消息到群组"""
        try:
            from pyrogram.types import Message
            await client.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            logger.error(f"发送消息失败（群组: {chat_id}）: {e}")
            raise
    
    async def send_custom_guide(
        self,
        group_id: int,
        message: str,
        account_id: Optional[str] = None
    ):
        """
        发送自定义引导消息
        
        Args:
            group_id: 群组ID
            message: 消息内容
            account_id: 指定账号ID（如果为None，则使用所有监听该群组的账号）
        """
        try:
            if account_id:
                # 使用指定账号发送
                if account_id in self.account_manager.accounts:
                    account = self.account_manager.accounts[account_id]
                    if account.status.value == "online" and account.client:
                        await self._send_message(
                            client=account.client,
                            chat_id=group_id,
                            text=message
                        )
            else:
                # 使用所有监听该群组的账号发送
                accounts = self._get_accounts_for_group(group_id)
                for account in accounts:
                    try:
                        if account.status.value == "online" and account.client:
                            await self._send_message(
                                client=account.client,
                                chat_id=group_id,
                                text=message
                            )
                    except Exception as e:
                        logger.error(f"发送自定义引导失败（账号: {account.account_id}）: {e}")
        except Exception as e:
            logger.error(f"发送自定义引导消息失败: {e}", exc_info=True)

