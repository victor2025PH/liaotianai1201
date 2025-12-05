"""
📈 數據分析報表模組
支持：
- 數據收集和聚合
- 轉化漏斗分析
- 用戶行為分析
- 報表生成
- 趨勢預測
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


# ==================== 數據模型 ====================

class MetricType(Enum):
    """指標類型"""
    # 計數類
    COUNT = "count"
    SUM = "sum"
    
    # 統計類
    AVERAGE = "average"
    MEDIAN = "median"
    PERCENTILE = "percentile"
    
    # 比率類
    RATE = "rate"
    RATIO = "ratio"


class TimeGranularity(Enum):
    """時間粒度"""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class DataPoint:
    """數據點"""
    timestamp: datetime
    value: float
    dimensions: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "dimensions": self.dimensions
        }


@dataclass
class TimeSeriesData:
    """時間序列數據"""
    metric_name: str
    data_points: List[DataPoint] = field(default_factory=list)
    
    def add_point(self, timestamp: datetime, value: float, dimensions: dict = None):
        self.data_points.append(DataPoint(
            timestamp=timestamp,
            value=value,
            dimensions=dimensions or {}
        ))
    
    def get_values(self) -> List[float]:
        return [p.value for p in self.data_points]
    
    def get_sum(self) -> float:
        return sum(self.get_values())
    
    def get_average(self) -> float:
        values = self.get_values()
        return statistics.mean(values) if values else 0
    
    def get_max(self) -> float:
        values = self.get_values()
        return max(values) if values else 0
    
    def get_min(self) -> float:
        values = self.get_values()
        return min(values) if values else 0
    
    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "data_points": [p.to_dict() for p in self.data_points],
            "summary": {
                "sum": self.get_sum(),
                "average": round(self.get_average(), 2),
                "max": self.get_max(),
                "min": self.get_min(),
                "count": len(self.data_points)
            }
        }


# ==================== 轉化漏斗 ====================

@dataclass
class FunnelStage:
    """漏斗階段"""
    name: str
    count: int = 0
    
    @property
    def conversion_rate(self) -> float:
        return 0.0  # 需要和上一階段比較


@dataclass
class ConversionFunnel:
    """轉化漏斗"""
    name: str
    stages: List[FunnelStage] = field(default_factory=list)
    
    def add_stage(self, name: str, count: int):
        self.stages.append(FunnelStage(name=name, count=count))
    
    def get_conversion_rates(self) -> List[Tuple[str, float]]:
        """計算各階段轉化率"""
        rates = []
        for i, stage in enumerate(self.stages):
            if i == 0:
                rates.append((stage.name, 100.0))
            else:
                prev_count = self.stages[i-1].count
                rate = (stage.count / prev_count * 100) if prev_count > 0 else 0
                rates.append((stage.name, round(rate, 2)))
        return rates
    
    def get_overall_rate(self) -> float:
        """計算整體轉化率"""
        if not self.stages or self.stages[0].count == 0:
            return 0.0
        return round(self.stages[-1].count / self.stages[0].count * 100, 2)
    
    def to_dict(self) -> dict:
        rates = self.get_conversion_rates()
        return {
            "name": self.name,
            "stages": [
                {
                    "name": stage.name,
                    "count": stage.count,
                    "conversion_rate": rates[i][1]
                }
                for i, stage in enumerate(self.stages)
            ],
            "overall_rate": self.get_overall_rate()
        }


# ==================== 用戶行為分析 ====================

@dataclass
class UserBehaviorProfile:
    """用戶行為畫像"""
    user_id: int
    
    # 活動統計
    total_messages: int = 0
    total_redpackets_claimed: int = 0
    total_redpackets_sent: int = 0
    total_amount_won: float = 0.0
    total_amount_spent: float = 0.0
    
    # 時間統計
    first_seen: Optional[datetime] = None
    last_active: Optional[datetime] = None
    active_days: int = 0
    
    # 參與度
    engagement_score: float = 0.0
    
    # 行為模式
    avg_messages_per_day: float = 0.0
    peak_activity_hour: Optional[int] = None
    favorite_topics: List[str] = field(default_factory=list)
    
    def calculate_engagement_score(self):
        """計算參與度分數（0-100）"""
        score = 0
        
        # 消息活躍度（最高 30 分）
        score += min(self.total_messages / 10, 30)
        
        # 紅包參與度（最高 30 分）
        redpacket_activity = self.total_redpackets_claimed + self.total_redpackets_sent * 2
        score += min(redpacket_activity * 5, 30)
        
        # 活躍天數（最高 20 分）
        score += min(self.active_days * 2, 20)
        
        # 消費金額（最高 20 分）
        score += min(self.total_amount_spent * 2, 20)
        
        self.engagement_score = round(score, 2)
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "activity": {
                "total_messages": self.total_messages,
                "redpackets_claimed": self.total_redpackets_claimed,
                "redpackets_sent": self.total_redpackets_sent,
                "amount_won": round(self.total_amount_won, 2),
                "amount_spent": round(self.total_amount_spent, 2)
            },
            "time": {
                "first_seen": self.first_seen.isoformat() if self.first_seen else None,
                "last_active": self.last_active.isoformat() if self.last_active else None,
                "active_days": self.active_days
            },
            "engagement": {
                "score": self.engagement_score,
                "avg_messages_per_day": round(self.avg_messages_per_day, 2),
                "peak_hour": self.peak_activity_hour
            }
        }


# ==================== 數據收集器 ====================

class DataCollector:
    """數據收集器"""
    
    def __init__(self):
        # 原始數據存儲
        self.raw_events: List[dict] = []
        
        # 聚合數據
        self.hourly_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.daily_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # 用戶數據
        self.user_profiles: Dict[int, UserBehaviorProfile] = {}
        
        # 群組數據
        self.group_stats: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
            "messages": 0,
            "users_joined": 0,
            "users_active": set(),
            "redpackets_sent": 0,
            "redpackets_claimed": 0,
            "total_amount": 0.0
        })
    
    def record_event(
        self,
        event_type: str,
        user_id: int = None,
        group_id: int = None,
        data: dict = None
    ):
        """記錄事件"""
        now = datetime.now()
        hour_key = now.strftime("%Y-%m-%d-%H")
        day_key = now.strftime("%Y-%m-%d")
        
        # 存儲原始事件
        event = {
            "type": event_type,
            "timestamp": now.isoformat(),
            "user_id": user_id,
            "group_id": group_id,
            "data": data or {}
        }
        self.raw_events.append(event)
        
        # 限制原始事件數量
        if len(self.raw_events) > 100000:
            self.raw_events = self.raw_events[-50000:]
        
        # 更新聚合統計
        self.hourly_stats[hour_key][event_type] += 1
        self.daily_stats[day_key][event_type] += 1
        
        # 更新用戶畫像
        if user_id:
            self._update_user_profile(user_id, event_type, data, now)
        
        # 更新群組統計
        if group_id:
            self._update_group_stats(group_id, event_type, user_id, data)
    
    def _update_user_profile(
        self,
        user_id: int,
        event_type: str,
        data: dict,
        timestamp: datetime
    ):
        """更新用戶畫像"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserBehaviorProfile(user_id=user_id)
        
        profile = self.user_profiles[user_id]
        
        # 更新時間
        if profile.first_seen is None:
            profile.first_seen = timestamp
        profile.last_active = timestamp
        
        # 更新統計
        if event_type == "message":
            profile.total_messages += 1
        elif event_type == "redpacket_claimed":
            profile.total_redpackets_claimed += 1
            profile.total_amount_won += data.get("amount", 0)
        elif event_type == "redpacket_sent":
            profile.total_redpackets_sent += 1
            profile.total_amount_spent += data.get("amount", 0)
        
        # 重新計算參與度
        profile.calculate_engagement_score()
    
    def _update_group_stats(
        self,
        group_id: int,
        event_type: str,
        user_id: int,
        data: dict
    ):
        """更新群組統計"""
        stats = self.group_stats[group_id]
        
        if event_type == "message":
            stats["messages"] += 1
            if user_id:
                stats["users_active"].add(user_id)
        elif event_type == "user_joined":
            stats["users_joined"] += 1
        elif event_type == "redpacket_sent":
            stats["redpackets_sent"] += 1
            stats["total_amount"] += data.get("amount", 0)
        elif event_type == "redpacket_claimed":
            stats["redpackets_claimed"] += 1


# ==================== 報表生成器 ====================

class ReportGenerator:
    """報表生成器"""
    
    def __init__(self, collector: DataCollector):
        self.collector = collector
    
    def generate_daily_report(self, date_str: str = None) -> dict:
        """生成每日報表"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        stats = self.collector.daily_stats.get(date_str, {})
        
        return {
            "report_type": "daily",
            "date": date_str,
            "generated_at": datetime.now().isoformat(),
            "metrics": {
                "messages": stats.get("message", 0),
                "user_joins": stats.get("user_joined", 0),
                "redpackets_sent": stats.get("redpacket_sent", 0),
                "redpackets_claimed": stats.get("redpacket_claimed", 0),
            },
            "summary": self._generate_daily_summary(stats)
        }
    
    def _generate_daily_summary(self, stats: dict) -> str:
        """生成每日摘要"""
        messages = stats.get("message", 0)
        joins = stats.get("user_joined", 0)
        
        summary = f"今日共有 {joins} 名新用戶加入，"
        summary += f"產生 {messages} 條消息。"
        
        return summary
    
    def generate_group_report(self, group_id: int) -> dict:
        """生成群組報表"""
        stats = self.collector.group_stats.get(group_id, {})
        
        return {
            "report_type": "group",
            "group_id": group_id,
            "generated_at": datetime.now().isoformat(),
            "metrics": {
                "total_messages": stats.get("messages", 0),
                "users_joined": stats.get("users_joined", 0),
                "active_users": len(stats.get("users_active", set())),
                "redpackets_sent": stats.get("redpackets_sent", 0),
                "redpackets_claimed": stats.get("redpackets_claimed", 0),
                "total_amount": round(stats.get("total_amount", 0), 2)
            }
        }
    
    def generate_conversion_funnel(self) -> dict:
        """生成轉化漏斗報表"""
        funnel = ConversionFunnel(name="用戶轉化漏斗")
        
        # 計算各階段用戶數
        total_users = len(self.collector.user_profiles)
        
        # 階段 1：加入群組
        funnel.add_stage("加入群組", total_users)
        
        # 階段 2：發送消息
        active_users = sum(
            1 for p in self.collector.user_profiles.values()
            if p.total_messages > 0
        )
        funnel.add_stage("發送消息", active_users)
        
        # 階段 3：領取紅包
        redpacket_users = sum(
            1 for p in self.collector.user_profiles.values()
            if p.total_redpackets_claimed > 0
        )
        funnel.add_stage("領取紅包", redpacket_users)
        
        # 階段 4：發送紅包
        sender_users = sum(
            1 for p in self.collector.user_profiles.values()
            if p.total_redpackets_sent > 0
        )
        funnel.add_stage("發送紅包", sender_users)
        
        return funnel.to_dict()
    
    def generate_user_segments(self) -> dict:
        """生成用戶分層報表"""
        profiles = list(self.collector.user_profiles.values())
        
        # 按參與度分層
        segments = {
            "high_value": [],      # 高價值用戶（分數 > 70）
            "engaged": [],         # 活躍用戶（分數 40-70）
            "casual": [],          # 普通用戶（分數 10-40）
            "inactive": []         # 不活躍用戶（分數 < 10）
        }
        
        for profile in profiles:
            score = profile.engagement_score
            if score >= 70:
                segments["high_value"].append(profile.user_id)
            elif score >= 40:
                segments["engaged"].append(profile.user_id)
            elif score >= 10:
                segments["casual"].append(profile.user_id)
            else:
                segments["inactive"].append(profile.user_id)
        
        return {
            "report_type": "user_segments",
            "generated_at": datetime.now().isoformat(),
            "segments": {
                name: {
                    "count": len(users),
                    "percentage": round(len(users) / len(profiles) * 100, 2) if profiles else 0
                }
                for name, users in segments.items()
            },
            "total_users": len(profiles)
        }
    
    def generate_trend_report(
        self,
        metric: str,
        days: int = 7
    ) -> dict:
        """生成趨勢報表"""
        time_series = TimeSeriesData(metric_name=metric)
        
        today = date.today()
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            
            stats = self.collector.daily_stats.get(day_str, {})
            value = stats.get(metric, 0)
            
            time_series.add_point(
                timestamp=datetime.combine(day, datetime.min.time()),
                value=value
            )
        
        # 計算趨勢
        values = time_series.get_values()
        if len(values) >= 2:
            trend = "up" if values[-1] > values[0] else "down" if values[-1] < values[0] else "stable"
            change_rate = ((values[-1] - values[0]) / values[0] * 100) if values[0] > 0 else 0
        else:
            trend = "stable"
            change_rate = 0
        
        return {
            "report_type": "trend",
            "metric": metric,
            "period_days": days,
            "generated_at": datetime.now().isoformat(),
            "data": time_series.to_dict(),
            "trend": {
                "direction": trend,
                "change_rate": round(change_rate, 2)
            }
        }
    
    def generate_comprehensive_report(self) -> dict:
        """生成綜合報表"""
        return {
            "report_type": "comprehensive",
            "generated_at": datetime.now().isoformat(),
            "daily": self.generate_daily_report(),
            "funnel": self.generate_conversion_funnel(),
            "segments": self.generate_user_segments(),
            "trends": {
                "messages": self.generate_trend_report("message"),
                "user_joins": self.generate_trend_report("user_joined"),
                "redpackets": self.generate_trend_report("redpacket_claimed")
            }
        }


# ==================== 分析服務 ====================

class AnalyticsService:
    """分析服務 - 整合所有分析功能"""
    
    def __init__(self):
        self.collector = DataCollector()
        self.report_generator = ReportGenerator(self.collector)
    
    # 數據記錄接口
    def record_message(self, user_id: int, group_id: int, text: str = ""):
        self.collector.record_event(
            "message",
            user_id=user_id,
            group_id=group_id,
            data={"text_length": len(text)}
        )
    
    def record_user_join(self, user_id: int, group_id: int):
        self.collector.record_event(
            "user_joined",
            user_id=user_id,
            group_id=group_id
        )
    
    def record_redpacket_sent(
        self,
        user_id: int,
        group_id: int,
        amount: float,
        count: int
    ):
        self.collector.record_event(
            "redpacket_sent",
            user_id=user_id,
            group_id=group_id,
            data={"amount": amount, "count": count}
        )
    
    def record_redpacket_claimed(
        self,
        user_id: int,
        group_id: int,
        amount: float
    ):
        self.collector.record_event(
            "redpacket_claimed",
            user_id=user_id,
            group_id=group_id,
            data={"amount": amount}
        )
    
    # 報表接口
    def get_daily_report(self, date_str: str = None) -> dict:
        return self.report_generator.generate_daily_report(date_str)
    
    def get_group_report(self, group_id: int) -> dict:
        return self.report_generator.generate_group_report(group_id)
    
    def get_funnel_report(self) -> dict:
        return self.report_generator.generate_conversion_funnel()
    
    def get_user_segments(self) -> dict:
        return self.report_generator.generate_user_segments()
    
    def get_trend_report(self, metric: str, days: int = 7) -> dict:
        return self.report_generator.generate_trend_report(metric, days)
    
    def get_comprehensive_report(self) -> dict:
        return self.report_generator.generate_comprehensive_report()
    
    def get_user_profile(self, user_id: int) -> Optional[dict]:
        profile = self.collector.user_profiles.get(user_id)
        return profile.to_dict() if profile else None
    
    def get_top_users(self, limit: int = 10) -> List[dict]:
        """獲取活躍度最高的用戶"""
        profiles = list(self.collector.user_profiles.values())
        profiles.sort(key=lambda p: p.engagement_score, reverse=True)
        return [p.to_dict() for p in profiles[:limit]]


# ==================== FastAPI 路由（示例） ====================

def create_analytics_routes(service: AnalyticsService):
    """創建分析 API 路由（FastAPI）"""
    from fastapi import APIRouter, Query
    
    router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
    
    @router.get("/reports/daily")
    async def get_daily_report(date: str = None):
        """獲取每日報表"""
        return service.get_daily_report(date)
    
    @router.get("/reports/group/{group_id}")
    async def get_group_report(group_id: int):
        """獲取群組報表"""
        return service.get_group_report(group_id)
    
    @router.get("/reports/funnel")
    async def get_funnel():
        """獲取轉化漏斗"""
        return service.get_funnel_report()
    
    @router.get("/reports/segments")
    async def get_segments():
        """獲取用戶分層"""
        return service.get_user_segments()
    
    @router.get("/reports/trend/{metric}")
    async def get_trend(metric: str, days: int = Query(default=7, ge=1, le=30)):
        """獲取趨勢報表"""
        return service.get_trend_report(metric, days)
    
    @router.get("/reports/comprehensive")
    async def get_comprehensive():
        """獲取綜合報表"""
        return service.get_comprehensive_report()
    
    @router.get("/users/{user_id}")
    async def get_user(user_id: int):
        """獲取用戶畫像"""
        profile = service.get_user_profile(user_id)
        if not profile:
            return {"error": "User not found"}
        return profile
    
    @router.get("/users/top")
    async def get_top_users(limit: int = Query(default=10, ge=1, le=100)):
        """獲取活躍用戶排行"""
        return service.get_top_users(limit)
    
    return router


# 導出
__all__ = [
    "MetricType",
    "TimeGranularity",
    "DataPoint",
    "TimeSeriesData",
    "FunnelStage",
    "ConversionFunnel",
    "UserBehaviorProfile",
    "DataCollector",
    "ReportGenerator",
    "AnalyticsService",
    "create_analytics_routes"
]
