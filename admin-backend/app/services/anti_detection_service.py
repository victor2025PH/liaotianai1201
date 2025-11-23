"""
防风控服务
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.telegram_registration import AntiDetectionLog, UserRegistration

logger = logging.getLogger(__name__)


class AntiDetectionService:
    """防风控服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_risk_score(self, registration_data: Dict[str, Any]) -> int:
        """
        计算风险评分 (0-100)
        0-25: 低风险
        26-50: 中风险
        51-75: 高风险
        76-100: 极高风险
        """
        score = 0
        
        phone = registration_data.get('phone')
        ip_address = registration_data.get('ip_address')
        device_fingerprint = registration_data.get('device_fingerprint')
        
        # 1. 频率检查 (0-30分)
        if phone:
            recent_count = self._get_recent_registrations_by_phone(phone, hours=24)
            score += min(30, recent_count * 10)
        
        # 2. IP检查 (0-25分)
        if ip_address:
            ip_count = self._get_recent_registrations_by_ip(ip_address, hours=1)
            score += min(25, ip_count * 8)
        
        # 3. 设备指纹检查 (0-20分)
        if device_fingerprint:
            device_count = self._get_recent_registrations_by_device(device_fingerprint, hours=24)
            score += min(20, device_count * 5)
        
        # 4. 行为模式检查 (0-15分)
        behavior_score = self._analyze_behavior_pattern(registration_data)
        score += behavior_score
        
        # 5. 代理检查 (0-10分)
        if not registration_data.get('use_proxy'):
            score += 5  # 未使用代理增加风险
        
        return min(100, score)
    
    def should_block(self, risk_score: int) -> bool:
        """判断是否应该阻止注册"""
        return risk_score >= 75
    
    def get_risk_level(self, risk_score: int) -> str:
        """获取风险等级"""
        if risk_score <= 25:
            return 'low'
        elif risk_score <= 50:
            return 'medium'
        elif risk_score <= 75:
            return 'high'
        else:
            return 'critical'
    
    def log_event(
        self,
        event_type: str,
        risk_level: Optional[str] = None,
        risk_score: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        behavior_pattern: Optional[Dict[str, Any]] = None,
        action_taken: Optional[str] = None,
        registration_id: Optional[str] = None,
    ):
        """记录风控事件"""
        log_entry = AntiDetectionLog(
            registration_id=registration_id,
            event_type=event_type,
            risk_level=risk_level,
            risk_score=risk_score,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            behavior_pattern=behavior_pattern,
            action_taken=action_taken,
        )
        self.db.add(log_entry)
        self.db.commit()
    
    def _get_recent_registrations_by_phone(self, phone: str, hours: int = 24) -> int:
        """获取手机号最近的注册次数"""
        since = datetime.utcnow() - timedelta(hours=hours)
        count = self.db.query(UserRegistration).filter(
            UserRegistration.phone == phone,
            UserRegistration.created_at >= since
        ).count()
        return count
    
    def _get_recent_registrations_by_ip(self, ip_address: str, hours: int = 1) -> int:
        """获取IP地址最近的注册次数"""
        since = datetime.utcnow() - timedelta(hours=hours)
        count = self.db.query(UserRegistration).filter(
            UserRegistration.ip_address == ip_address,
            UserRegistration.created_at >= since
        ).count()
        return count
    
    def _get_recent_registrations_by_device(self, device_fingerprint: str, hours: int = 24) -> int:
        """获取设备最近的注册次数"""
        since = datetime.utcnow() - timedelta(hours=hours)
        count = self.db.query(AntiDetectionLog).filter(
            AntiDetectionLog.device_fingerprint == device_fingerprint,
            AntiDetectionLog.created_at >= since
        ).count()
        return count
    
    def _analyze_behavior_pattern(self, registration_data: Dict[str, Any]) -> int:
        """分析行为模式"""
        score = 0
        
        # 检查输入时间（如果有）
        input_times = registration_data.get('input_times', [])
        if len(input_times) > 1:
            avg_time = sum(
                input_times[i+1] - input_times[i] 
                for i in range(len(input_times)-1)
            ) / (len(input_times)-1)
            if avg_time < 0.5:  # 平均输入间隔小于0.5秒
                score += 10
        
        # 检查鼠标轨迹（如果有）
        mouse_trajectory = registration_data.get('mouse_trajectory', [])
        if mouse_trajectory and self._is_linear_trajectory(mouse_trajectory):
            score += 5
        
        return min(15, score)
    
    def _is_linear_trajectory(self, trajectory: list) -> bool:
        """检查鼠标轨迹是否过于线性"""
        if len(trajectory) < 3:
            return False
        
        # 简单的线性度检查
        # 实际实现可以使用更复杂的算法
        return False  # 简化实现

