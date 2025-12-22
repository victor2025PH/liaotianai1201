"""
Session 管理器 - Phase 4: 设备指纹与 Session 绑定
管理 Telegram Session 与设备指纹的对应关系
"""

import logging
from pathlib import Path
from typing import Optional
from agent.utils.device_fingerprint import (
    get_or_create_device_fingerprint,
    DeviceFingerprint
)

logger = logging.getLogger(__name__)


def get_phone_from_session(session_path: str) -> Optional[str]:
    """
    从 Session 文件路径或内容中提取手机号
    
    Args:
        session_path: Session 文件路径（.session 文件）
    
    Returns:
        手机号字符串，如果无法提取则返回 None
    """
    session_file = Path(session_path)
    
    # 方法1: 从文件名提取（如果文件名包含手机号）
    # 例如: +1234567890.session 或 1234567890.session
    filename = session_file.stem
    if filename.startswith("+") or filename.isdigit():
        # 尝试从文件名提取
        phone = filename.replace("_", "").replace("-", "")
        if phone.startswith("+") or phone.isdigit():
            return phone
    
    # 方法2: 从 Session 文件内容读取（需要解析 .session 文件）
    # Telethon 的 .session 文件是 SQLite 数据库
    # 可以查询 sessions 表获取 phone 字段
    try:
        import sqlite3
        if session_file.exists():
            conn = sqlite3.connect(str(session_file))
            cursor = conn.cursor()
            try:
                # Telethon Session 文件结构
                cursor.execute("SELECT phone FROM sessions LIMIT 1")
                result = cursor.fetchone()
                if result and result[0]:
                    return result[0]
            except sqlite3.OperationalError:
                # 表不存在或结构不同，尝试其他方法
                pass
            finally:
                conn.close()
    except Exception as e:
        logger.debug(f"无法从 Session 文件读取手机号: {e}")
    
    # 方法3: 使用文件名（去除扩展名）作为标识符
    # 如果无法提取真实手机号，使用文件名作为唯一标识
    return filename if filename else None


def get_device_fingerprint_for_session(
    session_path: str,
    phone_number: Optional[str] = None
) -> DeviceFingerprint:
    """
    获取或创建指定 Session 对应的设备指纹
    
    Args:
        session_path: Session 文件路径
        phone_number: 手机号（可选，如果不提供则尝试从 Session 文件提取）
    
    Returns:
        设备指纹对象
    
    注意:
        - 每个 Session 对应唯一的设备指纹
        - 指纹保存在 data/fingerprints/{phone_number}.json
        - 一旦生成，绝对不能修改
    """
    # 如果没有提供手机号，尝试从 Session 文件提取
    if not phone_number:
        phone_number = get_phone_from_session(session_path)
    
    # 如果仍然无法获取，使用 Session 文件名作为标识符
    if not phone_number:
        session_file = Path(session_path)
        phone_number = session_file.stem or "default"
        logger.warning(
            f"无法从 Session 文件提取手机号，使用文件名作为标识符: {phone_number}"
        )
    
    # 获取或创建设备指纹（按手机号存储）
    fingerprint = get_or_create_device_fingerprint(phone_number=phone_number)
    
    logger.info(
        f"Session ({phone_number}) 对应的设备指纹: "
        f"{fingerprint.device_model} ({fingerprint.platform})"
    )
    
    return fingerprint
