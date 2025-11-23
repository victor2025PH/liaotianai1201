"""
群組 AI 系統配置管理
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class GroupAIConfig(BaseSettings):
    """群組 AI 系統配置"""
    
    # 賬號管理配置
    max_accounts: int = 100
    session_files_directory: str = "sessions"
    account_health_check_interval: int = 60  # 秒
    account_reconnect_delay: int = 5  # 秒
    account_max_reconnect_attempts: int = 3
    
    # 劇本配置
    scripts_directory: str = "ai_models/group_scripts"
    script_cache_size: int = 100
    script_reload_on_change: bool = True
    
    # 對話配置
    default_reply_rate: float = 0.3
    min_reply_interval: int = 3  # 秒
    max_replies_per_hour: int = 50
    context_window_size: int = 10
    ai_temperature: float = 0.7
    ai_max_tokens: int = 500
    
    # AI 生成器配置
    ai_provider: str = "mock"  # openai, mock 等
    ai_api_key: Optional[str] = None  # AI API 密鑰
    
    # 紅包配置
    redpacket_detection_enabled: bool = True
    default_redpacket_probability: float = 0.5
    redpacket_max_per_hour: int = 10
    redpacket_cooldown_seconds: int = 300
    redpacket_min_amount: float = 0.01  # 最小紅包金額（防止 amountTo 太小）
    redpacket_notification_enabled: bool = True  # 是否啟用搶包通知
    redpacket_best_luck_announcement_enabled: bool = True  # 是否啟用最佳手氣提示
    
    # 遊戲系統 API 配置
    game_api_base_url: Optional[str] = None
    game_api_key: Optional[str] = None
    game_api_timeout: int = 30
    game_api_enabled: bool = False
    
    # 遊戲系統數據庫配置（用於直接查詢）
    game_database_url: Optional[str] = None
    
    # 遊戲系統代碼路徑（用於導入遊戲系統函數）
    game_system_path: Optional[str] = None
    
    # 監控配置
    metrics_collection_interval: int = 30  # 秒
    metrics_retention_days: int = 30
    alert_check_interval: int = 60  # 秒
    
    # 告警配置
    # 錯誤率告警閾值
    alert_error_rate_threshold: float = 0.5  # 錯誤率超過 50% 觸發錯誤告警
    alert_warning_rate_threshold: float = 0.2  # 錯誤率超過 20% 觸發警告告警
    alert_system_errors_threshold: int = 100  # 系統總錯誤數超過此值觸發告警
    
    # 賬號離線告警閾值
    alert_account_offline_threshold: float = 0.3  # 離線率超過 30% 觸發告警
    alert_account_inactive_seconds: int = 300  # 賬號無活動超過此秒數視為離線
    
    # 響應時間告警閾值（毫秒）
    alert_response_time_threshold: float = 5000.0  # 平均響應時間超過 5 秒觸發告警
    
    # 紅包參與失敗率告警閾值
    alert_redpacket_failure_rate_threshold: float = 0.3  # 紅包參與失敗率超過 30% 觸發告警
    
    # 消息處理異常告警閾值
    alert_message_processing_error_threshold: int = 10  # 每小時消息處理錯誤數超過此值觸發告警
    
    # 通知配置
    alert_notification_enabled: bool = True  # 是否啟用告警通知
    alert_email_enabled: bool = False  # 是否啟用郵件通知
    alert_telegram_enabled: bool = False  # 是否啟用 Telegram 通知
    alert_webhook_enabled: bool = False  # 是否啟用 Webhook 通知
    
    # 郵件通知配置
    alert_email_smtp_host: Optional[str] = None
    alert_email_smtp_port: int = 587
    alert_email_smtp_user: Optional[str] = None
    alert_email_smtp_password: Optional[str] = None
    alert_email_from: Optional[str] = None
    alert_email_to: Optional[str] = None  # 逗號分隔的多個郵箱
    
    # Telegram 通知配置
    alert_telegram_bot_token: Optional[str] = None
    alert_telegram_chat_id: Optional[str] = None
    
    # Webhook 通知配置
    alert_webhook_url: Optional[str] = None
    
    # 性能配置
    max_concurrent_messages: int = 50
    message_processing_timeout: int = 10  # 秒
    enable_message_queue: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "GROUP_AI_"


def get_group_ai_config() -> GroupAIConfig:
    """獲取群組 AI 配置"""
    return GroupAIConfig()

