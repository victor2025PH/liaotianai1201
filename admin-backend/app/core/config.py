from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Smart TG Admin API"
    database_url: str = "sqlite:///./admin.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    admin_default_email: str = "admin@example.com"
    admin_default_password: str = "changeme123"
    session_service_url: str = "http://localhost:8001"
    redpacket_service_url: str = "http://localhost:8002"
    monitoring_service_url: str = "http://localhost:8003"
    
    # CORS 配置
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:8080"  # 前端應用地址（逗號分隔）
    
    # 數據庫連接池配置
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_recycle: int = 3600
    database_pool_timeout: int = 30
    
    # 通知服務配置（可選）
    email_enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""
    
    webhook_enabled: bool = False
    webhook_url: str = ""
    
    telegram_bot_token: str = ""  # Telegram Bot Token（用於發送通知）
    telegram_chat_id: str = ""  # Telegram Chat ID（用於接收告警通知）
    
    # ========== Redis 缓存配置 ==========
    redis_url: str = ""  # Redis 连接 URL（可选）
    
    # ========== 自动备份配置 ==========
    auto_backup_enabled: bool = True  # 是否启用自动备份
    backup_dir: str = "backups"  # 备份目录
    backup_retention_days: int = 30  # 备份保留天数
    backup_interval_hours: int = 24  # 备份间隔（小时）
    
    # ========== 缓存配置 ==========
    cache_default_ttl: int = 300  # 默认缓存时间（秒）
    
    # ========== 性能监控配置 ==========
    performance_check_interval: int = 60  # 性能检查间隔（秒）
    
    # ========== 智能优化配置 ==========
    auto_optimize_enabled: bool = True  # 是否启用自动优化
    auto_optimize_interval_hours: int = 6  # 自动优化间隔（小时）
    
    # 定時告警檢查配置（可選）
    alert_check_interval_seconds: int = 300  # 告警檢查間隔（秒），默認 300 秒（5 分鐘）
    alert_check_enabled: bool = True  # 是否啟用定時告警檢查，默認啟用
    
    # 開發模式配置（可選）
    disable_auth: bool = False  # 是否禁用認證（僅用於開發/測試環境）
    
    # Telegram 注册模拟模式（可选）
    telegram_registration_mock_mode: bool = Field(
        default=False,
        description="是否启用 Telegram 注册模拟模式（用于测试，不调用真实 Telegram API）"
    )
    telegram_registration_mock_code: str = Field(
        default="123456",
        description="模拟模式下的验证码（默认: 123456）"
    )
    
    # 日志配置
    debug_auth_logs: bool = Field(
        default=False,
        description="是否启用认证调试日志（[AUTH DEBUG]），仅在开发/调试时启用"
    )
    
    # Telegram API 配置（可选，用于群组 AI 服务）
    telegram_api_id: str = Field(default="", description="Telegram API ID")
    telegram_api_hash: str = Field(default="", description="Telegram API Hash")
    telegram_session_name: str = Field(default="", description="Telegram Session Name")
    telegram_session_file: str = Field(default="", description="Telegram Session File Path")
    
    # OpenAI API 配置（可选，用于格式转换等 AI 功能）
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI Model Name")
    
    @classmethod
    def parse_env_var(cls, field_name: str, raw_val: str) -> any:
        """解析環境變量，支持布爾值字符串"""
        if field_name == 'disable_auth':
            return raw_val.lower() in ('true', '1', 'yes', 'on')
        return cls.json_schema_extra(field_name, raw_val) if hasattr(cls, 'json_schema_extra') else raw_val

    class Config:
        # 启用 .env 文件读取
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # 允许额外字段（忽略未定义的字段，避免测试环境配置错误）
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]

