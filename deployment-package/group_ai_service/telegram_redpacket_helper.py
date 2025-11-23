"""
Telegram 紅包助手
用於通過 Telegram API 點擊紅包按鈕的輔助工具
"""
import logging
from typing import Optional, Dict, Any
from pyrogram import Client
from pyrogram.types import Message

logger = logging.getLogger(__name__)


async def click_redpacket_button(
    client: Client,
    chat_id: int,
    message_id: int,
    callback_data: str
) -> Dict[str, Any]:
    """
    點擊紅包按鈕
    
    注意：Pyrogram 沒有直接的 callback_query 方法
    需要使用 aiogram 的 Bot 或者通過其他方式
    
    這裡提供一個通過 aiogram Bot 的實現方案
    """
    try:
        # 方案1: 如果 client 是 aiogram Bot，直接使用
        if hasattr(client, 'answer_callback_query'):
            # 這是 aiogram Bot，可以直接使用
            # 但需要先獲取 CallbackQuery 對象
            # 這裡我們需要從消息中構造
            pass
        
        # 方案2: 使用 Pyrogram 的原始 API 調用
        # 注意：這需要知道 Telegram Bot API 的詳細實現
        # Pyrogram 的 Client 沒有直接的 callback_query 方法
        
        # 臨時方案：返回需要的信息，讓調用者使用 aiogram Bot 處理
        return {
            "success": False,
            "method": "telegram_button",
            "note": "需要使用 aiogram Bot 發送 CallbackQuery",
            "callback_data": callback_data,
            "chat_id": chat_id,
            "message_id": message_id
        }
    except Exception as e:
        logger.error(f"點擊紅包按鈕失敗: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def find_redpacket_message(
    client: Client,
    chat_id: int,
    envelope_id: str,
    limit: int = 50
) -> Optional[Message]:
    """
    查找包含指定紅包按鈕的消息
    
    Args:
        client: Pyrogram Client
        chat_id: 群組 ID
        envelope_id: 紅包 ID（envelope_id）
        limit: 搜索最近的消息數量
        
    Returns:
        包含紅包按鈕的消息，如果未找到則返回 None
    """
    try:
        callback_data_pattern = f"hb:grab:{envelope_id}"
        
        # 獲取最近的消息
        async for message in client.get_chat_history(chat_id, limit=limit):
            if not message.reply_markup:
                continue
            
            # 檢查是否包含紅包按鈕
            if hasattr(message.reply_markup, 'inline_keyboard'):
                for row in message.reply_markup.inline_keyboard:
                    for button in row:
                        if getattr(button, 'callback_data', '') == callback_data_pattern:
                            logger.info(
                                f"找到紅包消息: message_id={message.id}, "
                                f"envelope_id={envelope_id}"
                            )
                            return message
        
        logger.warning(f"未找到包含紅包 {envelope_id} 的消息")
        return None
    except Exception as e:
        logger.error(f"查找紅包消息失敗: {e}")
        return None

