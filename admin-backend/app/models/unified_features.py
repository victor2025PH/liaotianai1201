"""
統一功能數據庫模型
支持關鍵詞觸發、定時消息、群組管理等新功能
"""
from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import (
    Column, String, Integer, Boolean, Float, JSON, DateTime, 
    BigInteger, Text, ForeignKey, Index
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


def generate_uuid():
    """生成UUID字符串"""
    return str(uuid.uuid4())


class KeywordTriggerRule(Base):
    """關鍵詞觸發規則表"""
    __tablename__ = "keyword_trigger_rules"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    rule_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    
    # 關鍵詞配置
    keywords = Column(JSON, default=list, nullable=False)  # 關鍵詞列表
    pattern = Column(Text, nullable=True)  # 正則表達式模式
    match_type = Column(String(20), default="any", nullable=False)  # simple/regex/fuzzy/all/any/context
    case_sensitive = Column(Boolean, default=False, nullable=False)
    
    # 觸發條件
    sender_ids = Column(JSON, default=list)  # 發送者 ID 白名單
    sender_blacklist = Column(JSON, default=list)  # 發送者黑名單
    time_range_start = Column(String(10), nullable=True)  # 時間範圍開始，如 "09:00"
    time_range_end = Column(String(10), nullable=True)  # 時間範圍結束，如 "18:00"
    weekdays = Column(JSON, default=list)  # 星期幾，[1,2,3,4,5] 表示週一到週五
    group_ids = Column(JSON, default=list)  # 特定群組 ID 列表
    message_length_min = Column(Integer, nullable=True)
    message_length_max = Column(Integer, nullable=True)
    condition_logic = Column(String(10), default="AND")  # AND/OR
    
    # 觸發動作
    actions = Column(JSON, default=list, nullable=False)  # 動作列表
    
    # 優先級和上下文
    priority = Column(Integer, default=0, nullable=False, index=True)
    context_window = Column(Integer, default=0, nullable=False)  # 上下文窗口（前後 N 條消息）
    
    # 統計信息
    trigger_count = Column(Integer, default=0, nullable=False)  # 觸發次數
    last_triggered_at = Column(DateTime, nullable=True)
    
    # 元數據
    description = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # 索引
    __table_args__ = (
        Index('idx_keyword_trigger_enabled_priority', 'enabled', 'priority'),
    )


class ScheduledMessageTask(Base):
    """定時消息任務表"""
    __tablename__ = "scheduled_message_tasks"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    
    # 調度配置
    schedule_type = Column(String(20), default="cron", nullable=False)  # cron/interval/once/conditional
    cron_expression = Column(String(100), nullable=True)  # Cron 表達式
    interval_seconds = Column(Integer, nullable=True)  # 間隔秒數
    start_time = Column(String(10), nullable=True)  # 開始時間，如 "09:00"
    end_time = Column(String(10), nullable=True)  # 結束時間，如 "22:00"
    timezone = Column(String(50), default="Asia/Shanghai", nullable=False)
    
    # 條件觸發
    condition = Column(Text, nullable=True)  # 條件表達式
    check_interval = Column(Integer, default=300, nullable=False)  # 檢查間隔（秒）
    
    # 目標配置
    groups = Column(JSON, default=list, nullable=False)  # 目標群組列表
    accounts = Column(JSON, default=list, nullable=False)  # 目標賬號列表
    rotation = Column(Boolean, default=False, nullable=False)  # 是否輪流發送
    rotation_strategy = Column(String(20), default="round_robin", nullable=False)  # round_robin/random/priority
    
    # 消息配置
    message_template = Column(Text, nullable=False)  # 消息模板
    template_variables = Column(JSON, default=dict)  # 模板變量
    media_path = Column(String(500), nullable=True)  # 媒體文件路徑
    
    # 發送配置
    delay_min = Column(Integer, default=0, nullable=False)  # 隨機延遲最小值（秒）
    delay_max = Column(Integer, default=5, nullable=False)  # 隨機延遲最大值（秒）
    retry_times = Column(Integer, default=3, nullable=False)  # 重試次數
    retry_interval = Column(Integer, default=60, nullable=False)  # 重試間隔（秒）
    
    # 執行記錄
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True, index=True)
    run_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    
    # 元數據
    description = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # 索引
    __table_args__ = (
        Index('idx_scheduled_task_enabled_next_run', 'enabled', 'next_run_at'),
    )


class ScheduledMessageLog(Base):
    """定時消息執行日誌表"""
    __tablename__ = "scheduled_message_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(100), nullable=False, index=True)  # 關聯到 ScheduledMessageTask.task_id
    account_id = Column(String(100), nullable=False, index=True)
    group_id = Column(BigInteger, nullable=False, index=True)
    
    # 執行結果
    success = Column(Boolean, nullable=False, index=True)
    message_sent = Column(Text, nullable=True)  # 實際發送的消息
    error_message = Column(Text, nullable=True)
    
    # 執行時間
    executed_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # 索引
    __table_args__ = (
        Index('idx_scheduled_log_task_executed', 'task_id', 'executed_at'),
    )


class GroupJoinConfig(Base):
    """群組加入配置表"""
    __tablename__ = "group_join_configs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    config_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    
    # 加入配置
    join_type = Column(String(20), default="invite_link", nullable=False)  # invite_link/username/group_id/search
    invite_link = Column(String(500), nullable=True)
    username = Column(String(100), nullable=True)
    group_id = Column(BigInteger, nullable=True, index=True)
    search_keywords = Column(JSON, default=list)  # 搜索關鍵詞
    
    # 目標賬號
    account_ids = Column(JSON, default=list, nullable=False)  # 目標賬號列表
    
    # 加入條件
    min_members = Column(Integer, nullable=True)
    max_members = Column(Integer, nullable=True)
    group_types = Column(JSON, default=list)  # 群組類型，如 ["supergroup", "group"]
    
    # 加入後動作
    post_join_actions = Column(JSON, default=list)  # 加入後動作列表
    
    # 優先級
    priority = Column(Integer, default=0, nullable=False, index=True)
    
    # 執行記錄
    join_count = Column(Integer, default=0, nullable=False)  # 成功加入次數
    last_joined_at = Column(DateTime, nullable=True)
    
    # 元數據
    description = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # 索引
    __table_args__ = (
        Index('idx_group_join_enabled_priority', 'enabled', 'priority'),
    )


class GroupJoinLog(Base):
    """群組加入日誌表"""
    __tablename__ = "group_join_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    config_id = Column(String(100), nullable=False, index=True)  # 關聯到 GroupJoinConfig.config_id
    account_id = Column(String(100), nullable=False, index=True)
    group_id = Column(BigInteger, nullable=False, index=True)
    
    # 執行結果
    success = Column(Boolean, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    
    # 執行時間
    joined_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # 索引
    __table_args__ = (
        Index('idx_group_join_log_config_joined', 'config_id', 'joined_at'),
    )


class UnifiedConfig(Base):
    """統一配置表（分層配置管理）"""
    __tablename__ = "unified_configs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    config_id = Column(String(100), unique=True, nullable=False, index=True)
    config_level = Column(String(20), nullable=False, index=True)  # global/group/account/role/task
    level_id = Column(String(100), nullable=True, index=True)  # 層級 ID（群組 ID、賬號 ID、角色 ID、任務 ID）
    
    # 配置內容
    chat_config = Column(JSON, default=dict)  # 聊天配置
    redpacket_config = Column(JSON, default=dict)  # 紅包配置
    keyword_config = Column(JSON, default=dict)  # 關鍵詞配置
    metadata = Column(JSON, default=dict)  # 其他元數據
    
    # 元數據
    description = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # 索引：支持快速查詢特定層級的配置
    __table_args__ = (
        Index('idx_unified_config_level_id', 'config_level', 'level_id'),
    )


class GroupActivityMetrics(Base):
    """群組活動指標表"""
    __tablename__ = "group_activity_metrics"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    group_id = Column(BigInteger, nullable=False, index=True)
    
    # 指標數據
    message_count_24h = Column(Integer, default=0, nullable=False)
    active_members_24h = Column(Integer, default=0, nullable=False)
    new_members_24h = Column(Integer, default=0, nullable=False)
    redpacket_count_24h = Column(Integer, default=0, nullable=False)
    last_activity = Column(DateTime, nullable=True)
    health_score = Column(Float, default=0.0, nullable=False)  # 0-1
    
    # 時間戳
    recorded_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # 索引
    __table_args__ = (
        Index('idx_group_metrics_group_recorded', 'group_id', 'recorded_at'),
    )
