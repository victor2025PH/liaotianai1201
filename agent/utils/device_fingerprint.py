"""
设备指纹生成器 - Phase 4: 风控与指纹管理
生成真实的设备参数，伪装成官方 Telegram App
每个 Session（手机号）对应唯一的设备指纹，持久化存储
"""

import json
import random
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# 指纹存储目录
FINGERPRINTS_DIR = Path(__file__).parent.parent.parent / "data" / "fingerprints"
FINGERPRINTS_DIR.mkdir(parents=True, exist_ok=True)

# 兼容旧版本：全局设备指纹文件路径（已废弃，保留用于兼容）
DEVICE_FILE = Path(__file__).parent.parent / "device.json"

# 预置的流行设备列表（Android）- 扩展版
ANDROID_DEVICES = [
    # 小米系列
    {
        "manufacturer": "Xiaomi",
        "model": "Xiaomi 13",
        "sdk_version": 33,  # Android 13
        "app_version": "10.5.0",
        "lang_code": "zh-cn"
    },
    {
        "manufacturer": "Xiaomi",
        "model": "Xiaomi 12 Pro",
        "sdk_version": 32,  # Android 12L
        "app_version": "10.4.0",
        "lang_code": "zh-cn"
    },
    {
        "manufacturer": "Xiaomi",
        "model": "Redmi Note 12 Pro",
        "sdk_version": 33,
        "app_version": "10.5.0",
        "lang_code": "zh-cn"
    },
    # 三星系列
    {
        "manufacturer": "Samsung",
        "model": "SM-S918B",  # Samsung Galaxy S23
        "sdk_version": 33,
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "Samsung",
        "model": "SM-S908B",  # Samsung Galaxy S22
        "sdk_version": 33,
        "app_version": "10.4.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "Samsung",
        "model": "SM-A536B",  # Samsung Galaxy A53
        "sdk_version": 32,
        "app_version": "10.4.0",
        "lang_code": "en-us"
    },
    # Google Pixel 系列
    {
        "manufacturer": "Google",
        "model": "Pixel 7",
        "sdk_version": 33,
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "Google",
        "model": "Pixel 6 Pro",
        "sdk_version": 33,
        "app_version": "10.4.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "Google",
        "model": "Pixel 7 Pro",
        "sdk_version": 33,
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    # 华为系列
    {
        "manufacturer": "Huawei",
        "model": "LIO-AL00",  # Huawei Mate 30 Pro
        "sdk_version": 29,  # Android 10
        "app_version": "10.4.0",
        "lang_code": "zh-cn"
    },
    {
        "manufacturer": "Huawei",
        "model": "ELS-AN00",  # Huawei P40 Pro
        "sdk_version": 30,  # Android 11
        "app_version": "10.4.0",
        "lang_code": "zh-cn"
    },
    # OnePlus 系列
    {
        "manufacturer": "OnePlus",
        "model": "ONEPLUS A6000",  # OnePlus 6
        "sdk_version": 31,  # Android 12
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "OnePlus",
        "model": "ONEPLUS GM1913",  # OnePlus 7 Pro
        "sdk_version": 31,
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    # OPPO 系列
    {
        "manufacturer": "OPPO",
        "model": "CPH2173",  # OPPO Find X3 Pro
        "sdk_version": 31,
        "app_version": "10.4.0",
        "lang_code": "zh-cn"
    },
    {
        "manufacturer": "OPPO",
        "model": "CPH2207",  # OPPO Find X5 Pro
        "sdk_version": 32,
        "app_version": "10.5.0",
        "lang_code": "zh-cn"
    },
    # vivo 系列
    {
        "manufacturer": "vivo",
        "model": "V2145A",  # vivo X70 Pro+
        "sdk_version": 31,
        "app_version": "10.4.0",
        "lang_code": "zh-cn"
    },
    {
        "manufacturer": "vivo",
        "model": "V2218A",  # vivo X90 Pro
        "sdk_version": 33,
        "app_version": "10.5.0",
        "lang_code": "zh-cn"
    },
    # Realme 系列
    {
        "manufacturer": "Realme",
        "model": "RMX3371",  # Realme GT 2 Pro
        "sdk_version": 32,  # Android 12L
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "Realme",
        "model": "RMX3301",  # Realme GT 3
        "sdk_version": 33,
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    # 其他品牌
    {
        "manufacturer": "Honor",
        "model": "LGE-AN00",  # Honor Magic 4 Pro
        "sdk_version": 32,
        "app_version": "10.4.0",
        "lang_code": "zh-cn"
    },
    {
        "manufacturer": "Motorola",
        "model": "XT2301-4",  # Motorola Edge 40
        "sdk_version": 33,
        "app_version": "10.5.0",
        "lang_code": "en-us"
    }
]

# iOS 设备列表 - 扩展版
IOS_DEVICES = [
    # iPhone 13 系列
    {
        "manufacturer": "Apple",
        "model": "iPhone14,2",  # iPhone 13 Pro
        "system_version": "16.6",
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
        "model": "iPhone14,4",  # iPhone 13
        "system_version": "16.7",
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    # iPhone 14 系列
    {
        "manufacturer": "Apple",
        "model": "iPhone15,2",  # iPhone 14 Pro
        "system_version": "17.0",
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "Apple",
        "model": "iPhone15,3",  # iPhone 14 Pro Max
        "system_version": "17.1",
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "Apple",
        "model": "iPhone14,7",  # iPhone 14
        "system_version": "17.0",
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "Apple",
        "model": "iPhone14,8",  # iPhone 14 Plus
        "system_version": "17.0",
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    # iPhone 15 系列
    {
        "manufacturer": "Apple",
        "model": "iPhone16,1",  # iPhone 15 Pro
        "system_version": "17.1",
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "Apple",
        "model": "iPhone16,2",  # iPhone 15 Pro Max
        "system_version": "17.1",
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "Apple",
        "model": "iPhone15,4",  # iPhone 15
        "system_version": "17.1",
        "app_version": "10.5.0",
        "lang_code": "en-us"
    },
    # iPhone 12 系列（较旧但仍有用户）
    {
        "manufacturer": "Apple",
        "model": "iPhone13,2",  # iPhone 12 Pro
        "system_version": "16.5",
        "app_version": "10.4.0",
        "lang_code": "en-us"
    },
    {
        "manufacturer": "Apple",
        "model": "iPhone13,1",  # iPhone 12 mini
        "system_version": "16.4",
        "app_version": "10.4.0",
        "lang_code": "zh-cn"
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
        
        # 随机选择 Telegram App 版本（保持合理范围，模拟真实用户）
        # 使用更真实的版本分布（较新版本更常见）
        app_versions = [
            "10.4.0", "10.4.1", "10.4.2",
            "10.5.0", "10.5.1", "10.5.2",  # 更常见
            "10.6.0", "10.6.1"  # 较新版本
        ]
        # 权重选择：较新版本权重更高
        weights = [0.1, 0.1, 0.1, 0.2, 0.2, 0.15, 0.1, 0.05]
        app_version = random.choices(app_versions, weights=weights)[0]
        
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
        
        # iOS 版本选择（同样使用权重）
        app_versions = [
            "10.4.0", "10.4.1", "10.4.2",
            "10.5.0", "10.5.1", "10.5.2",  # 更常见
            "10.6.0", "10.6.1"  # 较新版本
        ]
        weights = [0.1, 0.1, 0.1, 0.2, 0.2, 0.15, 0.1, 0.05]
        app_version = random.choices(app_versions, weights=weights)[0]
        
        return DeviceFingerprint(
            platform="ios",
            device_model=device_template["model"],
            system_version=device_template["system_version"],
            app_version=app_version,
            lang_code=lang_code
        )


def get_fingerprint_file_path(phone_number: str) -> Path:
    """
    获取指定手机号的指纹文件路径
    
    Args:
        phone_number: 手机号（用于标识 Session）
    
    Returns:
        指纹文件路径
    """
    # 清理手机号（移除特殊字符，只保留数字）
    clean_phone = "".join(filter(str.isdigit, phone_number))
    if not clean_phone:
        # 如果清理后为空，使用原始值（可能是其他标识符）
        clean_phone = phone_number.replace("/", "_").replace("\\", "_")
    
    return FINGERPRINTS_DIR / f"{clean_phone}.json"


def load_device_fingerprint(phone_number: Optional[str] = None) -> Optional[DeviceFingerprint]:
    """
    从文件加载设备指纹
    
    Args:
        phone_number: 手机号（用于标识 Session），如果为 None 则使用全局文件（兼容旧版本）
    
    Returns:
        设备指纹对象，如果文件不存在则返回 None
    """
    if phone_number:
        # 新版本：按手机号存储
        fingerprint_file = get_fingerprint_file_path(phone_number)
    else:
        # 兼容旧版本：全局文件
        fingerprint_file = DEVICE_FILE
    
    if not fingerprint_file.exists():
        return None
    
    try:
        with open(fingerprint_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return DeviceFingerprint.from_dict(data)
    except Exception as e:
        logger.error(f"加载设备指纹失败 ({fingerprint_file}): {e}")
        return None


def save_device_fingerprint(fingerprint: DeviceFingerprint, phone_number: Optional[str] = None):
    """
    保存设备指纹到文件
    
    Args:
        fingerprint: 设备指纹对象
        phone_number: 手机号（用于标识 Session），如果为 None 则使用全局文件（兼容旧版本）
    """
    if phone_number:
        # 新版本：按手机号存储
        fingerprint_file = get_fingerprint_file_path(phone_number)
    else:
        # 兼容旧版本：全局文件
        fingerprint_file = DEVICE_FILE
    
    try:
        with open(fingerprint_file, "w", encoding="utf-8") as f:
            json.dump(fingerprint.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(
            f"设备指纹已保存 ({fingerprint_file.name}): "
            f"{fingerprint.device_model} ({fingerprint.platform})"
        )
    except Exception as e:
        logger.error(f"保存设备指纹失败 ({fingerprint_file}): {e}")
        raise


def get_or_create_device_fingerprint(
    phone_number: Optional[str] = None,
    platform: Optional[str] = None
) -> DeviceFingerprint:
    """
    获取或创建设备指纹（确保持久化）
    
    Args:
        phone_number: 手机号（用于标识 Session），如果为 None 则使用全局文件（兼容旧版本）
        platform: 平台类型，如果为 None 则随机选择
    
    Returns:
        设备指纹对象
    
    注意:
        - 如果设备指纹文件已存在，直接返回（严禁修改，否则触发风控）
        - 如果不存在，生成新的并保存
        - 每个手机号对应唯一的设备指纹，不会变来变去
    """
    # 尝试加载现有指纹
    existing = load_device_fingerprint(phone_number)
    if existing:
        logger.info(
            f"使用现有设备指纹 ({phone_number or 'global'}): "
            f"{existing.device_model} ({existing.platform}, {existing.system_version})"
        )
        return existing
    
    # 生成新指纹
    logger.info(f"未找到设备指纹 ({phone_number or 'global'})，生成新指纹...")
    new_fingerprint = generate_new(platform)
    
    # 保存到文件
    save_device_fingerprint(new_fingerprint, phone_number)
    
    logger.info(
        f"已生成并保存设备指纹 ({phone_number or 'global'}): "
        f"{new_fingerprint.device_model} ({new_fingerprint.platform}, {new_fingerprint.system_version})"
    )
    
    return new_fingerprint
