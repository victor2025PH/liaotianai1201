"""
速率限制服务
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.telegram_registration import UserRegistration, AntiDetectionLog

logger = logging.getLogger(__name__)


class RateLimiterService:
    """速率限制服务"""
    
    RATE_LIMITS = {
        'per_phone_per_hour': 3,      # 每个手机号每小时最多3次
        'per_phone_per_day': 10,       # 每个手机号每天最多10次
        'per_ip_per_hour': 5,          # 每个IP每小时最多5次
        'per_ip_per_day': 20,          # 每个IP每天最多20次
        'per_device_per_day': 15,      # 每个设备每天最多15次
        'global_per_minute': 30,       # 全局每分钟最多30次
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_rate_limit(self, registration_data: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        检查速率限制
        返回: (是否允许, 错误消息, 重试等待时间(秒))
        """
        phone = registration_data.get('phone')
        ip_address = registration_data.get('ip_address')
        device_fingerprint = registration_data.get('device_fingerprint')
        
        # 检查手机号限制
        if phone:
            phone_hourly = self._get_count_by_phone(phone, hours=1)
            if phone_hourly >= self.RATE_LIMITS['per_phone_per_hour']:
                return False, f"手机号已达到每小时限制 ({self.RATE_LIMITS['per_phone_per_hour']}次)", 3600
            
            phone_daily = self._get_count_by_phone(phone, hours=24)
            if phone_daily >= self.RATE_LIMITS['per_phone_per_day']:
                return False, f"手机号已达到每天限制 ({self.RATE_LIMITS['per_phone_per_day']}次)", 86400
        
        # 检查IP限制
        if ip_address:
            ip_hourly = self._get_count_by_ip(ip_address, hours=1)
            if ip_hourly >= self.RATE_LIMITS['per_ip_per_hour']:
                return False, f"IP地址已达到每小时限制 ({self.RATE_LIMITS['per_ip_per_hour']}次)", 3600
            
            ip_daily = self._get_count_by_ip(ip_address, hours=24)
            if ip_daily >= self.RATE_LIMITS['per_ip_per_day']:
                return False, f"IP地址已达到每天限制 ({self.RATE_LIMITS['per_ip_per_day']}次)", 86400
        
        # 检查设备限制
        if device_fingerprint:
            device_daily = self._get_count_by_device(device_fingerprint, hours=24)
            if device_daily >= self.RATE_LIMITS['per_device_per_day']:
                return False, f"设备已达到每天限制 ({self.RATE_LIMITS['per_device_per_day']}次)", 86400
        
        # 检查全局限制
        global_minute = self._get_global_count(minutes=1)
        if global_minute >= self.RATE_LIMITS['global_per_minute']:
            return False, "系统繁忙，请稍后重试", 60
        
        return True, "", 0
    
    def _get_count_by_phone(self, phone: str, hours: int) -> int:
        """获取手机号的注册次数"""
        since = datetime.utcnow() - timedelta(hours=hours)
        count = self.db.query(UserRegistration).filter(
            UserRegistration.phone == phone,
            UserRegistration.created_at >= since
        ).count()
        return count
    
    def _get_count_by_ip(self, ip_address: str, hours: int) -> int:
        """获取IP的注册次数"""
        since = datetime.utcnow() - timedelta(hours=hours)
        count = self.db.query(UserRegistration).filter(
            UserRegistration.ip_address == ip_address,
            UserRegistration.created_at >= since
        ).count()
        return count
    
    def _get_count_by_device(self, device_fingerprint: str, hours: int) -> int:
        """获取设备的注册次数"""
        since = datetime.utcnow() - timedelta(hours=hours)
        count = self.db.query(AntiDetectionLog).filter(
            AntiDetectionLog.device_fingerprint == device_fingerprint,
            AntiDetectionLog.created_at >= since
        ).count()
        return count
    
    def _get_global_count(self, minutes: int) -> int:
        """获取全局注册次数"""
        since = datetime.utcnow() - timedelta(minutes=minutes)
        count = self.db.query(UserRegistration).filter(
            UserRegistration.created_at >= since
        ).count()
        return count

