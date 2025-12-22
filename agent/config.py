"""
Agent 配置管理
"""

import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).parent / "config.json"
DEFAULT_CONFIG = {
    "agent_id": None,
    "server_url": "ws://localhost:8000/api/v1/agents/ws",
    "heartbeat_interval": 30,
    "reconnect_interval": 30,
    "reconnect_max_attempts": -1,  # -1 表示无限重试
    "metadata": {
        "version": "1.0.0",
        "platform": None,
        "hostname": None
    },
    # Phase 5: Telegram 配置
    "telegram": {
        "api_id": None,
        "api_hash": None,
        "session_string": None,
        "session_path": None
    },
    # Phase 6: API 配置
    "api": {
        "base_url": "http://127.0.0.1:8000",
        "api_key": None,
        "poll_interval": 5.0,  # 轮询间隔（秒）
        "heartbeat_interval": 30.0  # 心跳间隔（秒）
    }
}


def get_agent_id() -> str:
    """
    获取或生成 Agent ID
    
    Returns:
        Agent ID (UUID 字符串)
    """
    config = load_config()
    
    agent_id = config.get("agent_id")
    if not agent_id:
        # 生成新的 Agent ID
        agent_id = str(uuid.uuid4())
        config["agent_id"] = agent_id
        save_config(config)
        logger.info(f"生成新的 Agent ID: {agent_id}")
    else:
        logger.info(f"使用现有 Agent ID: {agent_id}")
    
    return agent_id


def load_config() -> Dict[str, Any]:
    """
    加载配置文件
    
    Returns:
        配置字典
    """
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # 合并默认配置
                merged_config = {**DEFAULT_CONFIG, **config}
                # 确保 metadata 也被合并
                if "metadata" in config:
                    merged_config["metadata"] = {**DEFAULT_CONFIG["metadata"], **config["metadata"]}
                return merged_config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return DEFAULT_CONFIG.copy()
    else:
        logger.info("配置文件不存在，使用默认配置")
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]):
    """
    保存配置文件
    
    Args:
        config: 配置字典
    """
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.debug("配置文件已保存")
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")


def get_server_url() -> str:
    """
    获取 Server WebSocket URL
    
    Returns:
        WebSocket URL
    """
    config = load_config()
    base_url = config.get("server_url", DEFAULT_CONFIG["server_url"])
    agent_id = get_agent_id()
    
    # 如果 URL 不包含 agent_id，则添加到路径中
    if "{agent_id}" in base_url:
        url = base_url.format(agent_id=agent_id)
    elif base_url.endswith("/ws"):
        url = f"{base_url}/{agent_id}"
    else:
        url = f"{base_url}/ws/{agent_id}"
    
    return url


def get_heartbeat_interval() -> int:
    """获取心跳间隔（秒）"""
    config = load_config()
    return config.get("heartbeat_interval", DEFAULT_CONFIG["heartbeat_interval"])


def get_reconnect_interval() -> int:
    """获取重连间隔（秒）"""
    config = load_config()
    return config.get("reconnect_interval", DEFAULT_CONFIG["reconnect_interval"])


def get_reconnect_max_attempts() -> int:
    """获取最大重连次数（-1 表示无限）"""
    config = load_config()
    return config.get("reconnect_max_attempts", DEFAULT_CONFIG["reconnect_max_attempts"])


def update_metadata(metadata: Dict[str, Any]):
    """
    更新 Agent 元数据
    
    Args:
        metadata: 元数据字典
    """
    config = load_config()
    if "metadata" not in config:
        config["metadata"] = {}
    config["metadata"].update(metadata)
    save_config(config)


def get_metadata() -> Dict[str, Any]:
    """获取 Agent 元数据"""
    config = load_config()
    metadata = config.get("metadata", DEFAULT_CONFIG["metadata"].copy())
    
    # 自动填充平台和主机名
    import platform
    import socket
    
    if metadata.get("platform") is None:
        metadata["platform"] = platform.system()
    
    if metadata.get("hostname") is None:
        try:
            metadata["hostname"] = socket.gethostname()
        except:
            metadata["hostname"] = "unknown"
    
    return metadata


def get_proxy() -> Optional[str]:
    """
    获取 Proxy URL
    
    Returns:
        Proxy URL 或 None
    """
    config = load_config()
    return config.get("proxy")


def get_expected_ip() -> Optional[str]:
    """
    获取期望的出口 IP
    
    Returns:
        期望的 IP 地址或 None
    """
    config = load_config()
    return config.get("expected_ip")


def get_telegram_api_id() -> Optional[int]:
    """
    获取 Telegram API ID
    
    Returns:
        API ID 或 None
    """
    import os
    config = load_config()
    telegram_config = config.get("telegram", {})
    api_id = telegram_config.get("api_id") or os.getenv("TELEGRAM_API_ID")
    return int(api_id) if api_id else None


def get_telegram_api_hash() -> Optional[str]:
    """
    获取 Telegram API Hash
    
    Returns:
        API Hash 或 None
    """
    import os
    config = load_config()
    telegram_config = config.get("telegram", {})
    return telegram_config.get("api_hash") or os.getenv("TELEGRAM_API_HASH")


def get_telegram_session_string() -> Optional[str]:
    """
    获取 Telegram Session String
    
    Returns:
        Session String 或 None
    """
    import os
    config = load_config()
    telegram_config = config.get("telegram", {})
    return telegram_config.get("session_string") or os.getenv("TELEGRAM_SESSION_STRING")


def get_telegram_session_path() -> Optional[str]:
    """
    获取 Telegram Session 文件路径
    
    Returns:
        Session 文件路径或 None
    """
    import os
    config = load_config()
    telegram_config = config.get("telegram", {})
    return telegram_config.get("session_path") or os.getenv("TELEGRAM_SESSION_PATH")


def get_api_base_url() -> str:
    """
    获取 API 基础 URL
    
    Returns:
        API 基础 URL
    """
    import os
    config = load_config()
    api_config = config.get("api", {})
    return api_config.get("base_url") or os.getenv("API_BASE_URL") or DEFAULT_CONFIG["api"]["base_url"]


def get_api_key() -> Optional[str]:
    """
    获取 API 密钥
    
    Returns:
        API 密钥或 None
    """
    import os
    config = load_config()
    api_config = config.get("api", {})
    return api_config.get("api_key") or os.getenv("API_KEY")


def get_poll_interval() -> float:
    """
    获取轮询间隔（秒）
    
    Returns:
        轮询间隔
    """
    config = load_config()
    api_config = config.get("api", {})
    return api_config.get("poll_interval", DEFAULT_CONFIG["api"]["poll_interval"])


def get_heartbeat_interval() -> float:
    """
    获取心跳间隔（秒）
    
    Returns:
        心跳间隔
    """
    config = load_config()
    api_config = config.get("api", {})
    return api_config.get("heartbeat_interval", DEFAULT_CONFIG["api"]["heartbeat_interval"])
