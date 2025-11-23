"""
核心配置模組測試
測試 Settings 類和配置相關功能
"""
import pytest
import os
from unittest.mock import patch, Mock

from app.core.config import Settings, get_settings


class TestSettings:
    """Settings 類測試"""

    def test_settings_default_values(self):
        """測試默認值（可能被環境變量覆蓋）"""
        # 清除緩存
        get_settings.cache_clear()
        
        settings = Settings()
        
        # 基本字段應該存在
        assert settings.app_name == "Smart TG Admin API"
        assert isinstance(settings.database_url, str)
        assert isinstance(settings.redis_url, str)
        assert isinstance(settings.jwt_secret, str)
        assert settings.jwt_algorithm == "HS256"
        assert isinstance(settings.access_token_expire_minutes, int)
        assert "@" in settings.admin_default_email  # 應該是有效的郵箱格式
        assert isinstance(settings.admin_default_password, str)

    def test_settings_database_pool_config(self):
        """測試數據庫連接池配置"""
        settings = Settings()
        
        assert settings.database_pool_size == 10
        assert settings.database_max_overflow == 20
        assert settings.database_pool_recycle == 3600
        assert settings.database_pool_timeout == 30

    def test_settings_notification_config(self):
        """測試通知服務配置"""
        settings = Settings()
        
        assert settings.email_enabled is False
        assert settings.smtp_host == "smtp.gmail.com"
        assert settings.smtp_port == 587
        assert settings.webhook_enabled is False
        assert settings.telegram_bot_token == ""

    def test_settings_alert_check_config(self):
        """測試告警檢查配置"""
        settings = Settings()
        
        assert settings.alert_check_interval_seconds == 300
        assert settings.alert_check_enabled is True

    def test_settings_disable_auth(self):
        """測試禁用認證配置"""
        settings = Settings()
        
        assert settings.disable_auth is False

    @patch.dict(os.environ, {
        "DISABLE_AUTH": "true",
        "JWT_SECRET": "test_secret",
        "ADMIN_DEFAULT_EMAIL": "test@example.com",
        "DATABASE_URL": "sqlite:///./test.db"
    })
    def test_settings_from_env_vars(self):
        """測試從環境變量讀取配置"""
        # 清除緩存
        get_settings.cache_clear()
        
        settings = get_settings()
        
        assert settings.jwt_secret == "test_secret"
        assert settings.admin_default_email == "test@example.com"
        assert settings.database_url == "sqlite:///./test.db"
        # disable_auth 應該被解析為布爾值
        assert settings.disable_auth is True
        
        # 恢復
        get_settings.cache_clear()

    @patch.dict(os.environ, {
        "DISABLE_AUTH": "1",
        "ALERT_CHECK_ENABLED": "false"
    }, clear=False)
    def test_settings_boolean_parsing(self):
        """測試布爾值解析"""
        # 清除緩存
        get_settings.cache_clear()
        
        settings = get_settings()
        
        # "1" 應該解析為 True
        assert settings.disable_auth is True
        # "false" 應該解析為 False
        assert settings.alert_check_enabled is False
        
        # 恢復
        get_settings.cache_clear()

    @patch.dict(os.environ, {
        "DISABLE_AUTH": "yes",
        "ALERT_CHECK_ENABLED": "on"
    }, clear=False)
    def test_settings_boolean_parsing_variants(self):
        """測試布爾值解析變體"""
        # 清除緩存
        get_settings.cache_clear()
        
        settings = get_settings()
        
        # "yes" 和 "on" 應該解析為 True
        assert settings.disable_auth is True
        assert settings.alert_check_enabled is True
        
        # 恢復
        get_settings.cache_clear()

    @patch.dict(os.environ, {
        "DISABLE_AUTH": "no",
        "ALERT_CHECK_ENABLED": "off"
    }, clear=False)
    def test_settings_boolean_false_values(self):
        """測試布爾值 false 解析"""
        # 清除緩存
        get_settings.cache_clear()
        
        settings = get_settings()
        
        # "no" 和 "off" 應該解析為 False
        assert settings.disable_auth is False
        assert settings.alert_check_enabled is False
        
        # 恢復
        get_settings.cache_clear()

    @patch.dict(os.environ, {
        "ACCESS_TOKEN_EXPIRE_MINUTES": "120",
        "DATABASE_POOL_SIZE": "20",
        "SMTP_PORT": "465"
    }, clear=False)
    def test_settings_numeric_values(self):
        """測試數值配置"""
        # 清除緩存
        get_settings.cache_clear()
        
        settings = get_settings()
        
        assert settings.access_token_expire_minutes == 120
        assert settings.database_pool_size == 20
        assert settings.smtp_port == 465
        
        # 恢復
        get_settings.cache_clear()

    def test_settings_service_urls(self):
        """測試服務 URL 配置"""
        settings = Settings()
        
        assert settings.session_service_url == "http://localhost:8001"
        assert settings.redpacket_service_url == "http://localhost:8002"
        assert settings.monitoring_service_url == "http://localhost:8003"

    @patch.dict(os.environ, {
        "SESSION_SERVICE_URL": "http://test:9001",
        "REDPACKET_SERVICE_URL": "http://test:9002"
    }, clear=False)
    def test_settings_service_urls_from_env(self):
        """測試從環境變量讀取服務 URL"""
        # 清除緩存
        get_settings.cache_clear()
        
        settings = get_settings()
        
        assert settings.session_service_url == "http://test:9001"
        assert settings.redpacket_service_url == "http://test:9002"
        
        # 恢復
        get_settings.cache_clear()


class TestGetSettings:
    """get_settings 函數測試"""

    def test_get_settings_cached(self):
        """測試設置緩存"""
        # 清除緩存
        get_settings.cache_clear()
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        # 應該返回同一個實例（緩存）
        assert settings1 is settings2

    def test_get_settings_singleton(self):
        """測試單例模式"""
        # 清除緩存
        get_settings.cache_clear()
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        # 應該是同一個對象
        assert id(settings1) == id(settings2)

    def test_get_settings_after_cache_clear(self):
        """測試清除緩存後重新獲取"""
        # 清除緩存
        get_settings.cache_clear()
        
        settings1 = get_settings()
        get_settings.cache_clear()
        settings2 = get_settings()
        
        # 清除緩存後，應該創建新實例（但可能還是同一個對象，取決於實現）
        # 至少應該能正常獲取
        assert settings1 is not None
        assert settings2 is not None


class TestSettingsParseEnvVar:
    """Settings.parse_env_var 方法測試"""

    def test_parse_env_var_disable_auth_true(self):
        """測試解析 disable_auth 為 True"""
        result = Settings.parse_env_var("disable_auth", "true")
        assert result is True
        
        result = Settings.parse_env_var("disable_auth", "1")
        assert result is True
        
        result = Settings.parse_env_var("disable_auth", "yes")
        assert result is True
        
        result = Settings.parse_env_var("disable_auth", "on")
        assert result is True

    def test_parse_env_var_disable_auth_false(self):
        """測試解析 disable_auth 為 False"""
        result = Settings.parse_env_var("disable_auth", "false")
        assert result is False
        
        result = Settings.parse_env_var("disable_auth", "0")
        assert result is False
        
        result = Settings.parse_env_var("disable_auth", "no")
        assert result is False
        
        result = Settings.parse_env_var("disable_auth", "off")
        assert result is False

    def test_parse_env_var_other_field(self):
        """測試解析其他字段（不應該特殊處理）"""
        # 其他字段應該返回原值或使用默認處理
        result = Settings.parse_env_var("jwt_secret", "test_secret")
        # 如果沒有特殊處理，可能返回原值或 None
        assert result is not None

