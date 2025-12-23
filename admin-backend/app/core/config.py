from functools import lru_cache
import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart TG Admin API"
    database_url: str = "sqlite:///./admin.db"
    redis_url: str = "redis://localhost:6379/0"
    # 支持 .env 文件中的 secret_key 和 jwt_secret 两种写法
    jwt_secret: str = Field(default="change_me", validation_alias="secret_key")
    # 支持 .env 文件中的 algorithm 和 jwt_algorithm 两种写法
    jwt_algorithm: str = Field(default="HS256", validation_alias="algorithm")
    access_token_expire_minutes: int = 60
    # 日志级别（可选，用于兼容 .env 文件中的 log_level）
    log_level: str = Field(default="INFO", description="日志级别")
    admin_default_email: str = "admin@example.com"
    admin_default_password: str = "changeme123"
    session_service_url: str = "http://localhost:8001"
    redpacket_service_url: str = "http://localhost:8002"
    monitoring_service_url: str = "http://localhost:8003"
    
    # CORS 配置
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:8080,https://aizkw.usdt2026.cc,https://hongbao.usdt2026.cc,https://tgmini.usdt2026.cc,https://aikz.usdt2026.cc,https://aiadmin.usdt2026.cc"  # 前端應用地址（逗號分隔）
    
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
    
    # Gemini API 配置（可选，用于前端 AI 聊天功能）
    gemini_api_key: str = Field(default="", description="Google Gemini API Key")
    
    @classmethod
    def parse_env_var(cls, field_name: str, raw_val: str) -> any:
        """解析環境變量，支持布爾值字符串"""
        if field_name == 'disable_auth':
            return raw_val.lower() in ('true', '1', 'yes', 'on')
        return cls.json_schema_extra(field_name, raw_val) if hasattr(cls, 'json_schema_extra') else raw_val

    # Pydantic v2 配置方式
    # 动态查找 .env 文件路径
    @staticmethod
    def _find_env_file() -> str:
        """查找 .env 文件的绝对路径"""
        # 方法1: 从环境变量获取（如果设置了）
        if env_file := os.getenv("ENV_FILE"):
            if Path(env_file).exists():
                return env_file
        
        # 方法2: 从当前文件位置向上查找 admin-backend 目录
        # 当前文件: admin-backend/app/core/config.py
        # 目标: admin-backend/.env
        current_file = Path(__file__).resolve()
        admin_backend_dir = current_file.parent.parent.parent
        env_file_path = admin_backend_dir / ".env"
        
        if env_file_path.exists():
            return str(env_file_path)
        
        # 方法3: 尝试当前工作目录
        cwd_env = Path.cwd() / ".env"
        if cwd_env.exists():
            return str(cwd_env)
        
        # 方法4: 尝试 /home/ubuntu/telegram-ai-system/admin-backend/.env
        default_path = Path("/home/ubuntu/telegram-ai-system/admin-backend/.env")
        if default_path.exists():
            return str(default_path)
        
        # 如果都找不到，返回默认值（Pydantic 会在当前目录查找）
        return ".env"
    
    # 在类定义时计算 .env 文件路径
    _env_file_path = _find_env_file()
    
    model_config = SettingsConfigDict(
        # 启用 .env 文件读取（使用计算出的绝对路径）
        env_file=_env_file_path,
        env_file_encoding="utf-8",
        case_sensitive=False,
        # 允许额外字段（忽略未定义的字段，避免测试环境配置错误）
        extra="ignore",
        # 允许从环境变量读取（支持小写下划线格式）
        env_prefix="",
        # 允许使用字段别名和验证别名
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]

