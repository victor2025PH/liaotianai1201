"""
设备指纹生成器 - Phase 4: 风控与指纹管理
生成真实的设备参数，伪装成官方 Telegram App
"""

import json
import random
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# 设备指纹文件路径
DEVICE_FILE = Path(__file__).parent.parent / "device.json"

# 预置的流行设备列表（Android）
ANDROID_DEVICES = [
    {
        "manufacturer": "Xiaomi",
        "model": "Xiaomi 13",
        "sdk_version": 33,  # Android 13
        "app_version": "10.5.0",
        "lang_code": "zh-cn"
    },
    {
        "manufacturer": "Samsung",
        "model": "SM-S918B",  # Samsung Galaxy S23
        "sdk_version": 33,
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "Google",
        "model": "Pixel 7",
        "sdk_version": 33,
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "Huawei",
        "model": "LIO-AL00",  # Huawei Mate 30 Pro
        "sdk_version": 29,  # Android 10
        "app_version": "10.4.0",
        "lang_code": "zh-cn"
    },
    {
        "manufacturer": "OnePlus",
        "model": "ONEPLUS A6000",  # OnePlus 6
        "sdk_version": 31,  # Android 12
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "OPPO",
        "model": "CPH2173",  # OPPO Find X3 Pro
        "sdk_version": 31,
        "app_version": "10.4.0",
        "lang_code": "zh-cn"
    },
    {
        "manufacturer": "vivo",
        "model": "V2145A",  # vivo X70 Pro+
        "sdk_version": 31,
        "app_version": "10.4.0",
        "lang_code": "zh-cn"
    },
    {
        "manufacturer": "Realme",
        "model": "RMX3371",  # Realme GT 2 Pro
        "sdk_version": 32,  # Android 12L
        "app_version": "10.5.0",
        "lang_code": "en-us"
    }
]

# iOS 设备列表
IOS_DEVICES = [
    {
        "manufacturer": "Apple",
        "model": "iPhone14,2",  # iPhone 13 Pro
        "system_version": "16.6",
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "Apple",
        "model": "iPhone15,2",  # iPhone 14 Pro
        "system_version": "17.0",
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "Apple",
        "model": "iPhone14,5",  # iPhone 13 mini
        "system_version": "16.5",
        "app_version": "10.4.0",
        "lang_code": "zh-cn"
    },
    {
        "manufacturer": "Apple",
        "model": "iPhone15,3",  # iPhone 14 Pro Max
        "system_version": "17.1",
        "app_version": "10.5.0",
        "lang_code": "en-us"
    }
]

# 语言代码列表
LANG_CODES = [
    "en-us", "zh-cn", "zh-tw", "ja-jp", "ko-kr",
    "es-es", "fr-fr", "de-de", "it-it", "pt-br",
    "ru-ru", "ar-sa", "hi-in", "th-th", "vi-vn"
]


@dataclass
class DeviceFingerprint:
    """设备指纹数据类"""
    platform: str  # "android" 或 "ios"
    device_model: str  # 设备型号
    system_version: str  # 系统版本
    app_version: str  # Telegram App 版本
    lang_code: str  # 语言代码
    manufacturer: Optional[str] = None  # 制造商（Android）
    sdk_version: Optional[int] = None  # SDK 版本（Android）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceFingerprint":
        """从字典创建"""
        return cls(**data)
    
    def to_telethon_params(self) -> Dict[str, Any]:
        """
        转换为 Telethon 客户端参数
        
        Returns:
            用于 TelegramClient 初始化的参数字典
        """
        params = {
            "device_model": self.device_model,
            "system_version": self.system_version,
            "app_version": self.app_version,
            "lang_code": self.lang_code
        }
        
        # Android 特有参数
        if self.platform == "android" and self.manufacturer:
            params["system_lang_code"] = self.lang_code
            # Telethon 使用这些参数来伪装设备
        
        return params


def generate_new(platform: Optional[str] = None) -> DeviceFingerprint:
    """
    生成新的设备指纹
    
    Args:
        platform: 平台类型 ("android" 或 "ios")，如果为 None 则随机选择
    
    Returns:
        设备指纹对象
    """
    if platform is None:
        platform = random.choice(["android", "ios"])
    
    if platform == "android":
        device_template = random.choice(ANDROID_DEVICES)
        lang_code = random.choice(LANG_CODES)
        
        # 随机选择 Telegram App 版本（保持合理范围）
        app_versions = ["10.4.0", "10.4.1", "10.5.0", "10.5.1", "10.6.0"]
        app_version = random.choice(app_versions)
        
        # 生成系统版本字符串（基于 SDK 版本）
        sdk_version = device_template["sdk_version"]
        system_version = f"Android {sdk_version // 10}.{sdk_version % 10}"
        
        return DeviceFingerprint(
            platform="android",
            device_model=device_template["model"],
            system_version=system_version,
            app_version=app_version,
            lang_code=lang_code,
            manufacturer=device_template["manufacturer"],
            sdk_version=sdk_version
        )
    
    else:  # iOS
        device_template = random.choice(IOS_DEVICES)
        lang_code = random.choice(LANG_CODES)
        
        app_versions = ["10.4.0", "10.4.1", "10.5.0", "10.5.1", "10.6.0"]
        app_version = random.choice(app_versions)
        
        return DeviceFingerprint(
            platform="ios",
            device_model=device_template["model"],
            system_version=device_template["system_version"],
            app_version=app_version,
            lang_code=lang_code
        )


def load_device_fingerprint() -> Optional[DeviceFingerprint]:
    """
    从文件加载设备指纹
    
    Returns:
        设备指纹对象，如果文件不存在则返回 None
    """
    if not DEVICE_FILE.exists():
        return None
    
    try:
        with open(DEVICE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return DeviceFingerprint.from_dict(data)
    except Exception as e:
        logger.error(f"加载设备指纹失败: {e}")
        return None


def save_device_fingerprint(fingerprint: DeviceFingerprint):
    """
    保存设备指纹到文件
    
    Args:
        fingerprint: 设备指纹对象
    """
    try:
        with open(DEVICE_FILE, "w", encoding="utf-8") as f:
            json.dump(fingerprint.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"设备指纹已保存: {fingerprint.device_model} ({fingerprint.platform})")
    except Exception as e:
        logger.error(f"保存设备指纹失败: {e}")
        raise


def get_or_create_device_fingerprint(platform: Optional[str] = None) -> DeviceFingerprint:
    """
    获取或创建设备指纹（确保持久化）
    
    Args:
        platform: 平台类型，如果为 None 则随机选择
    
    Returns:
        设备指纹对象
    
    注意:
        - 如果设备指纹文件已存在，直接返回（严禁修改）
        - 如果不存在，生成新的并保存
    """
    # 尝试加载现有指纹
    existing = load_device_fingerprint()
    if existing:
        logger.info(
            f"使用现有设备指纹: {existing.device_model} "
            f"({existing.platform}, {existing.system_version})"
        )
        return existing
    
    # 生成新指纹
    logger.info("未找到设备指纹，生成新指纹...")
    new_fingerprint = generate_new(platform)
    
    # 保存到文件
    save_device_fingerprint(new_fingerprint)
    
    logger.info(
        f"已生成并保存设备指纹: {new_fingerprint.device_model} "
        f"({new_fingerprint.platform}, {new_fingerprint.system_version})"
    )
    
    return new_fingerprint
