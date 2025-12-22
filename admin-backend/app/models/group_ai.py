"""
群組 AI 系統數據庫模型
"""
from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import Column, String, Integer, Boolean, Float, JSON, DateTime, BigInteger, Text, UniqueConstraint
from sqlalchemy.sql import func

# 使用统一的 Base（从 app.db 导入）
from app.db import Base


def generate_uuid():
    """生成UUID字符串"""
    return str(uuid.uuid4())


class GroupAIAccount(Base):
    """群組 AI 賬號表"""
    __tablename__ = "group_ai_accounts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)  # UUID，自动生成
    account_id = Column(String(100), unique=True, nullable=False, index=True)
    session_file = Column(String(500), nullable=False)
    script_id = Column(String(100), nullable=False, index=True)
    server_id = Column(String(100), nullable=True, index=True)  # 關聯的服務器ID
    group_ids = Column(JSON, nullable=False, default=list)  # 群組 ID 列表
    active = Column(Boolean, default=True, nullable=False)
    reply_rate = Column(Float, default=0.3, nullable=False)
    redpacket_enabled = Column(Boolean, default=True, nullable=False)
    redpacket_probability = Column(Float, default=0.5, nullable=False)
    max_replies_per_hour = Column(Integer, default=50, nullable=False)
    min_reply_interval = Column(Integer, default=3, nullable=False)
    config = Column(JSON, default=dict)  # 自定義配置
    # 帳號資料信息
    phone_number = Column(String(20), nullable=True)  # 手機號
    username = Column(String(100), nullable=True)  # Telegram用戶名
    first_name = Column(String(200), nullable=True)  # 名字
    last_name = Column(String(200), nullable=True)  # 姓氏
    display_name = Column(String(200), nullable=True)  # 顯示名稱（可編輯）
    avatar_url = Column(String(500), nullable=True)  # 頭像URL
    bio = Column(Text, nullable=True)  # 個人簡介
    user_id = Column(BigInteger, nullable=True, index=True)  # Telegram用戶ID
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class GroupAIScript(Base):
    """群組 AI 劇本表"""
    __tablename__ = "group_ai_scripts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)  # UUID，自动生成
    script_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    version = Column(String(20), nullable=False)
    yaml_content = Column(Text, nullable=False)  # YAML 內容（與 API 保持一致）
    description = Column(Text)
    status = Column(String(20), default="draft", nullable=False, index=True)  # 狀態：draft, reviewing, published, disabled
    created_by = Column(String(100))  # 創建者用戶ID
    reviewed_by = Column(String(100))  # 審核者用戶ID
    reviewed_at = Column(DateTime)  # 審核時間
    published_at = Column(DateTime)  # 發布時間
    tags = Column(JSON, default=list)  # 標籤列表
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class GroupAIScriptVersion(Base):
    """群組 AI 劇本版本歷史表"""
    __tablename__ = "group_ai_script_versions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    script_id = Column(String(100), nullable=False, index=True)  # 關聯到 GroupAIScript.script_id
    version = Column(String(20), nullable=False)  # 版本號
    yaml_content = Column(Text, nullable=False)  # 該版本的YAML內容
    description = Column(Text)  # 版本描述/變更說明
    created_by = Column(String(100))  # 創建者用戶ID
    change_summary = Column(Text)  # 變更摘要
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # 索引：script_id + version 唯一
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class AllocationHistory(Base):
    """账号分配历史表"""
    __tablename__ = "allocation_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    account_id = Column(String(100), nullable=False, index=True)
    server_id = Column(String(100), nullable=False, index=True)
    allocation_type = Column(String(50), nullable=False)  # initial, rebalance, manual
    load_score = Column(Float, nullable=True)  # 分配时的负载分数
    strategy = Column(String(50), nullable=True)  # 使用的分配策略
    reason = Column(Text, nullable=True)  # 分配原因
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # 索引
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class GroupAIDialogueHistory(Base):
    """群組 AI 對話歷史表"""
    __tablename__ = "group_ai_dialogue_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)  # UUID，自动生成
    account_id = Column(String(100), nullable=False, index=True)
    group_id = Column(BigInteger, nullable=False, index=True)
    message_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False, index=True)
    message_text = Column(Text)
    reply_text = Column(Text)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    context_snapshot = Column(JSON)  # 上下文快照


class GroupAIRedpacketLog(Base):
    """群組 AI 紅包日誌表"""
    __tablename__ = "group_ai_redpacket_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)  # UUID，自动生成
    account_id = Column(String(100), nullable=False, index=True)
    group_id = Column(BigInteger, nullable=False, index=True)
    redpacket_id = Column(String(100), nullable=False, index=True)
    amount = Column(Float)
    success = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)


class GroupAIMetric(Base):
    """群組 AI 指標表"""
    __tablename__ = "group_ai_metrics"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)  # UUID，自动生成
    account_id = Column(String(100), nullable=True, index=True)  # None 表示系統級指標
    metric_type = Column(String(50), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    extra_data = Column(JSON)  # 額外元數據（避免與 SQLAlchemy metadata 衝突）


class GroupAIAlertRule(Base):
    """群組 AI 告警規則表"""
    __tablename__ = "group_ai_alert_rules"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)  # UUID，自动生成
    name = Column(String(200), nullable=False, unique=True, index=True)  # 規則名稱
    rule_type = Column(String(50), nullable=False, index=True)  # 規則類型：error_rate, response_time, system_errors, account_offline 等
    alert_level = Column(String(20), nullable=False, default="warning")  # 告警級別：error, warning, info
    threshold_value = Column(Float, nullable=False)  # 閾值（根據規則類型不同而不同）
    threshold_operator = Column(String(10), nullable=False, default=">")  # 比較運算符：>, >=, <, <=, ==, !=
    enabled = Column(Boolean, default=True, nullable=False, index=True)  # 是否啟用
    notification_method = Column(String(50), default="email")  # 通知方式：email, webhook, telegram
    notification_target = Column(String(500))  # 通知目標（郵箱地址、Webhook URL、Telegram Chat ID 等）
    rule_conditions = Column(JSON, default=dict)  # 規則條件（JSON格式，支持更複雜的條件）
    description = Column(Text)  # 規則描述
    created_by = Column(String(100))  # 創建者用戶ID
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class GroupAIRoleAssignmentScheme(Base):
    """群組 AI 角色分配方案表"""
    __tablename__ = "group_ai_role_assignment_schemes"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False, index=True)  # 方案名稱
    description = Column(Text)  # 方案描述
    script_id = Column(String(100), nullable=False, index=True)  # 關聯的劇本ID
    assignments = Column(JSON, nullable=False)  # 分配方案數據: [{role_id, account_id, weight}]
    mode = Column(String(20), default="auto", nullable=False)  # 分配模式: auto, manual
    account_ids = Column(JSON, nullable=False, default=list)  # 參與分配的賬號ID列表
    created_by = Column(String(100))  # 創建者用戶ID
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class GroupAIRoleAssignmentHistory(Base):
    """群組 AI 角色分配歷史記錄表"""
    __tablename__ = "group_ai_role_assignment_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    scheme_id = Column(String(36), nullable=False, index=True)  # 關聯的方案ID
    script_id = Column(String(100), nullable=False, index=True)  # 劇本ID
    account_id = Column(String(100), nullable=False, index=True)  # 賬號ID
    role_id = Column(String(100), nullable=False)  # 分配的角色ID
    applied_by = Column(String(100))  # 應用者用戶ID
    applied_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    extra_data = Column(JSON, default=dict)  # 額外信息（如分配權重等，避免與SQLAlchemy metadata衝突）


class GroupAIAutomationTask(Base):
    """自動化任務表"""
    __tablename__ = "group_ai_automation_tasks"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    task_type = Column(String(50), nullable=False, index=True)  # scheduled, triggered, manual
    task_action = Column(String(100), nullable=False)  # account_start, account_stop, script_publish, alert_check, etc.
    schedule_config = Column(JSON, nullable=True)  # cron表達式或間隔配置
    trigger_config = Column(JSON, nullable=True)  # 觸發條件配置
    action_config = Column(JSON, nullable=False, default=dict)  # 任務執行參數
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True, index=True)
    run_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    last_result = Column(Text, nullable=True)  # 最後執行結果
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(100), nullable=True)
    # 任務依賴：完成後自動觸發的任務ID列表
    dependent_tasks = Column(JSON, nullable=True, default=list)  # 依賴的任務ID列表
    # 通知配置：任務執行結果是否發送通知
    notify_on_success = Column(Boolean, default=False, nullable=False)  # 成功時通知
    notify_on_failure = Column(Boolean, default=True, nullable=False)  # 失敗時通知
    notify_recipients = Column(JSON, nullable=True, default=list)  # 通知接收人列表（郵箱或用戶ID）


class GroupAIAutomationTaskLog(Base):
    """自動化任務執行日誌表"""
    __tablename__ = "group_ai_automation_task_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # success, failure, running
    started_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    result = Column(Text, nullable=True)  # 執行結果或錯誤信息
    error_message = Column(Text, nullable=True)
    execution_data = Column(JSON, nullable=True)  # 執行時的數據快照


class AIProviderConfig(Base):
    """AI 提供商配置表（支持多个 Key）"""
    __tablename__ = "ai_provider_configs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    provider_name = Column(String(50), nullable=False, index=True)  # openai, gemini, grok
    key_name = Column(String(100), nullable=False, default="default")  # Key 名称/别名，用于区分多个 Key
    api_key = Column(Text, nullable=True)  # 加密存储的 API Key
    is_valid = Column(Boolean, default=False, nullable=False)
    last_tested = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)  # 是否激活（当前使用的 Key）
    usage_stats = Column(JSON, default=dict)  # 使用统计
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # 唯一约束：同一提供商的同一名称只能有一个（允许同一提供商有多个不同名称的 Key）
    __table_args__ = (
        UniqueConstraint('provider_name', 'key_name', name='_provider_key_name_uc'),
        {'sqlite_autoincrement': True},
    )


class AIProviderSettings(Base):
    """AI 提供商全局设置表（单例）"""
    __tablename__ = "ai_provider_settings"
    
    id = Column(String(36), primary_key=True, default=lambda: "singleton")  # 单例，固定ID
    current_provider = Column(String(50), default="openai", nullable=False)  # 当前使用的提供商
    auto_failover_enabled = Column(Boolean, default=True, nullable=False)
    failover_providers = Column(JSON, default=list)  # 备用提供商列表
    active_keys = Column(JSON, default=dict)  # 每个提供商当前激活的Key ID { "openai": "key_id_1", "gemini": "key_id_2" }
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class KeywordMonitorRule(Base):
    """關鍵詞監控規則表"""
    __tablename__ = "keyword_monitor_rules"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False, index=True)  # 規則名稱
    keyword = Column(String(200), nullable=True, index=True)  # 關鍵詞（單個，已廢棄，使用 keywords）
    keywords = Column(JSON, default=list)  # 關鍵詞列表（JSON 數組，優先使用）
    group_id = Column(BigInteger, nullable=True, index=True)  # 監控的群組ID（NULL 表示所有群組）
    account_id = Column(String(100), nullable=True, index=True)  # 觸發後使用的賬號ID（NULL 表示使用檢測到關鍵詞的賬號）
    action = Column(String(50), nullable=False, default="send_private_message")  # 觸發動作：send_private_message, send_message, notify, etc.
    action_params = Column(JSON, default=dict)  # 動作參數（JSON格式）
    enabled = Column(Boolean, default=True, nullable=False, index=True)  # 是否啟用
    match_mode = Column(String(20), default="contains")  # 匹配模式：contains, exact, regex
    case_sensitive = Column(Boolean, default=False)  # 是否區分大小寫
    description = Column(Text)  # 規則描述
    trigger_count = Column(Integer, default=0, nullable=False)  # 觸發次數統計
    last_triggered_at = Column(DateTime, nullable=True)  # 最後觸發時間
    created_by = Column(String(100))  # 創建者用戶ID
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class KeywordTriggerEvent(Base):
    """關鍵詞觸發事件記錄表"""
    __tablename__ = "keyword_trigger_events"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    rule_id = Column(String(36), nullable=False, index=True)  # 關聯的規則ID
    account_id = Column(String(100), nullable=False, index=True)  # 檢測到關鍵詞的賬號ID
    group_id = Column(BigInteger, nullable=False, index=True)  # 群組ID
    user_id = Column(BigInteger, nullable=False, index=True)  # 發送消息的用戶ID
    message_id = Column(BigInteger, nullable=False)  # 消息ID
    message_text = Column(Text)  # 消息內容
    matched_keyword = Column(String(200), nullable=False)  # 匹配的關鍵詞
    action_taken = Column(String(50), nullable=False)  # 執行的動作
    action_result = Column(JSON, default=dict)  # 動作執行結果
    triggered_at = Column(DateTime, default=func.now(), nullable=False, index=True)


class RedPacketStrategy(Base):
    """紅包搶包策略表 - Phase 2: 擬人化版"""
    __tablename__ = "redpacket_strategies"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False, index=True)  # 策略名稱
    description = Column(Text, nullable=True)  # 策略描述
    keywords = Column(JSON, nullable=False, default=list)  # 關鍵詞列表，例如 ["USDT", "TON", "積分", "紅包"]
    delay_min = Column(Integer, nullable=False, default=1000)  # 最小延遲（毫秒）
    delay_max = Column(Integer, nullable=False, default=5000)  # 最大延遲（毫秒）
    target_groups = Column(JSON, nullable=False, default=list)  # 目標群組 ID 列表
    probability = Column(Integer, nullable=True, default=100)  # 搶包概率 (0-100)，可選，模擬偶爾沒看到的情況
    enabled = Column(Boolean, default=True, nullable=False, index=True)  # 是否啟用
    created_by = Column(String(100), nullable=True)  # 創建者用戶ID
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)