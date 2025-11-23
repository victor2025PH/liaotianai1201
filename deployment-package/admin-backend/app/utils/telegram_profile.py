"""
Telegram 帳號資料信息獲取工具
從 session 文件讀取帳號的頭像、用戶名等信息
"""
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import os
import sys

logger = logging.getLogger(__name__)

try:
    from pyrogram import Client
    from pyrogram.errors import AuthKeyUnregistered, SessionPasswordNeeded
    PYROGRAM_AVAILABLE = True
except ImportError:
    PYROGRAM_AVAILABLE = False
    logger.warning("Pyrogram 未安裝，無法獲取帳號資料信息")


async def get_telegram_profile(session_file: str, api_id: Optional[int] = None, api_hash: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    從 session 文件讀取 Telegram 帳號資料信息
    
    Args:
        session_file: Session 文件路徑
        api_id: Telegram API ID（從環境變量或配置獲取）
        api_hash: Telegram API Hash（從環境變量或配置獲取）
    
    Returns:
        帳號資料信息字典，包含：
        - phone_number: 手機號
        - username: 用戶名
        - first_name: 名字
        - last_name: 姓氏
        - display_name: 顯示名稱
        - avatar_url: 頭像URL
        - bio: 個人簡介
        - user_id: Telegram用戶ID
    """
    if not PYROGRAM_AVAILABLE:
        logger.warning("Pyrogram 未安裝，跳過獲取帳號資料信息")
        return None
    
    session_path = Path(session_file)
    if not session_path.exists():
        logger.error(f"Session 文件不存在: {session_file}")
        return None
    
    # 從環境變量獲取 API ID 和 Hash
    if not api_id:
        api_id_str = os.getenv("TELEGRAM_API_ID") or os.getenv("API_ID")
        if api_id_str:
            try:
                api_id = int(api_id_str)
            except (ValueError, TypeError):
                logger.error(f"API_ID 無效: {api_id_str}")
                return None
        else:
            logger.warning("未提供 API_ID 或 TELEGRAM_API_ID，無法獲取帳號資料信息")
            return None
    
    if not api_hash:
        api_hash = os.getenv("TELEGRAM_API_HASH") or os.getenv("API_HASH")
        if not api_hash:
            logger.warning("未提供 API_HASH 或 TELEGRAM_API_HASH，無法獲取帳號資料信息")
            return None
    
    # 獲取 session 名稱（不包含 .session 擴展名）
    session_name = session_path.stem
    
    # 創建臨時 Client（不連接）
    try:
        client = Client(
            session_name,
            api_id=api_id,
            api_hash=api_hash,
            workdir=str(session_path.parent),
            no_updates=True  # 不接收更新
        )
        
        # 嘗試連接以獲取用戶信息
        await client.connect()
        
        if not await client.is_connected:
            logger.warning(f"無法連接到 Telegram: {session_file}")
            await client.disconnect()
            return None
        
        # 獲取當前用戶信息
        me = await client.get_me()
        
        # 獲取用戶資料
        profile = {
            "phone_number": me.phone_number,
            "username": me.username,
            "first_name": me.first_name,
            "last_name": me.last_name,
            "display_name": me.first_name,  # 默認使用 first_name
            "user_id": me.id,
            "bio": None,  # 需要額外API調用來獲取
            "avatar_url": None  # 需要額外API調用來獲取
        }
        
        # 獲取完整的用戶資料（包含 bio 和頭像）
        try:
            # 嘗試獲取完整的用戶資料
            full_user = await client.get_users(me.id)
            if full_user:
                profile["bio"] = getattr(full_user, "bio", None)
                
                # 獲取頭像照片
                photos = await client.get_profile_photos(me.id, limit=1)
                if photos and len(photos) > 0:
                    # 獲取頭像文件ID，構建URL或文件路徑
                    photo = photos[0]
                    # 下載頭像（可選，這裡只保存文件ID或路徑）
                    # 實際使用時可能需要下載到服務器並提供URL
                    try:
                        avatar_file = await client.download_media(photo.file_id, file_name=f"avatars/{me.id}.jpg")
                        if avatar_file:
                            profile["avatar_url"] = str(avatar_file)
                    except Exception as e:
                        logger.warning(f"下載頭像失敗: {e}")
                        # 使用 Telegram 的 CDN URL（如果可用）
                        if hasattr(photo, "file_id"):
                            profile["avatar_url"] = f"telegram_file_id://{photo.file_id}"
        except Exception as e:
            logger.warning(f"獲取完整用戶資料失敗: {e}，使用基本信息")
        
        await client.disconnect()
        logger.info(f"成功獲取帳號資料信息: {session_file}, user_id: {me.id}")
        return profile
        
    except AuthKeyUnregistered:
        logger.error(f"Session 文件已失效: {session_file}")
        return None
    except SessionPasswordNeeded:
        logger.error(f"Session 需要兩步驗證密碼: {session_file}")
        return None
    except Exception as e:
        logger.error(f"獲取帳號資料信息失敗: {session_file}, 錯誤: {e}", exc_info=True)
        try:
            await client.disconnect()
        except:
            pass
        return None


def get_telegram_profile_sync(session_file: str, api_id: Optional[int] = None, api_hash: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    同步版本的獲取帳號資料信息（用於非異步環境）
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循環正在運行，使用線程執行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(get_telegram_profile(session_file, api_id, api_hash))
                )
                return future.result()
        else:
            return loop.run_until_complete(get_telegram_profile(session_file, api_id, api_hash))
    except RuntimeError:
        # 沒有事件循環，創建新的
        return asyncio.run(get_telegram_profile(session_file, api_id, api_hash))

