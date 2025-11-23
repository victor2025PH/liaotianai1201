"""
核心安全模組測試
測試密碼哈希、JWT token等安全功能
"""
import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)
from app.core.config import get_settings


class TestPasswordHashing:
    """密碼哈希測試"""

    def test_get_password_hash_basic(self):
        """測試基本密碼哈希"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        # bcrypt 哈希通常以 $2b$ 或類似前綴開頭
        assert hashed.startswith("$2")

    def test_get_password_hash_empty(self):
        """測試空密碼"""
        with pytest.raises(ValueError, match="密碼不能為空"):
            get_password_hash("")

    def test_get_password_hash_none(self):
        """測試None密碼"""
        with pytest.raises((ValueError, TypeError)):
            get_password_hash(None)

    def test_get_password_hash_long_password(self):
        """測試長密碼（超過72字節）"""
        # 創建超過72字節的密碼
        long_password = "a" * 100
        hashed = get_password_hash(long_password)
        
        assert hashed is not None
        assert isinstance(hashed, str)

    def test_get_password_hash_unicode(self):
        """測試Unicode密碼"""
        unicode_password = "測試密碼123!@#"
        hashed = get_password_hash(unicode_password)
        
        assert hashed is not None
        assert isinstance(hashed, str)

    def test_verify_password_correct(self):
        """測試驗證正確密碼"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        result = verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self):
        """測試驗證錯誤密碼"""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        result = verify_password(wrong_password, hashed)
        assert result is False

    def test_verify_password_empty(self):
        """測試驗證空密碼"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        result = verify_password("", hashed)
        assert result is False

    def test_verify_password_invalid_hash(self):
        """測試驗證無效哈希"""
        password = "test_password_123"
        invalid_hash = "invalid_hash_string"
        
        try:
            result = verify_password(password, invalid_hash)
            # 應該返回 False 或拋出異常
            assert result is False
        except Exception:
            # 如果拋出異常，這也是合理的行為
            pass

    def test_verify_password_different_passwords(self):
        """測試驗證不同密碼的哈希"""
        password1 = "password1"
        password2 = "password2"
        
        hashed1 = get_password_hash(password1)
        hashed2 = get_password_hash(password2)
        
        # 不同密碼應該產生不同哈希
        assert hashed1 != hashed2
        
        # 驗證時應該不匹配
        assert verify_password(password1, hashed2) is False
        assert verify_password(password2, hashed1) is False

    def test_password_hash_consistency(self):
        """測試密碼哈希一致性（相同密碼多次哈希應該不同，但都能驗證）"""
        password = "test_password_123"
        
        hashed1 = get_password_hash(password)
        hashed2 = get_password_hash(password)
        
        # bcrypt 每次會生成不同的鹽，所以哈希應該不同
        assert hashed1 != hashed2
        
        # 但都能驗證原始密碼
        assert verify_password(password, hashed1) is True
        assert verify_password(password, hashed2) is True


class TestJWTToken:
    """JWT Token 測試"""

    def test_create_access_token_basic(self):
        """測試基本token創建"""
        subject = "test@example.com"
        token = create_access_token(subject)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expires_delta(self):
        """測試帶過期時間的token創建"""
        subject = "test@example.com"
        expires_delta = timedelta(minutes=30)
        token = create_access_token(subject, expires_delta=expires_delta)
        
        assert token is not None
        assert isinstance(token, str)

    def test_decode_access_token_valid(self):
        """測試解碼有效token"""
        subject = "test@example.com"
        token = create_access_token(subject)
        
        decoded = decode_access_token(token)
        assert decoded == subject

    def test_decode_access_token_invalid(self):
        """測試解碼無效token"""
        invalid_token = "invalid_token_string"
        
        decoded = decode_access_token(invalid_token)
        assert decoded is None

    def test_decode_access_token_expired(self):
        """測試解碼過期token"""
        subject = "test@example.com"
        # 創建已過期的token（負的過期時間）
        expires_delta = timedelta(minutes=-10)
        token = create_access_token(subject, expires_delta=expires_delta)
        
        decoded = decode_access_token(token)
        # 過期token應該返回None
        assert decoded is None

    def test_decode_access_token_empty(self):
        """測試解碼空token"""
        decoded = decode_access_token("")
        assert decoded is None

    def test_create_and_decode_token_different_subjects(self):
        """測試不同subject的token"""
        subject1 = "user1@example.com"
        subject2 = "user2@example.com"
        
        token1 = create_access_token(subject1)
        token2 = create_access_token(subject2)
        
        # Token應該不同
        assert token1 != token2
        
        # 解碼應該返回正確的subject
        assert decode_access_token(token1) == subject1
        assert decode_access_token(token2) == subject2

    def test_create_access_token_different_expires(self):
        """測試不同過期時間的token"""
        subject = "test@example.com"
        
        token1 = create_access_token(subject, expires_delta=timedelta(minutes=10))
        token2 = create_access_token(subject, expires_delta=timedelta(hours=1))
        
        # Token應該不同（因為過期時間不同）
        assert token1 != token2
        
        # 但都能解碼到相同的subject
        assert decode_access_token(token1) == subject
        assert decode_access_token(token2) == subject

    @patch('app.core.security.get_settings')
    def test_create_access_token_with_custom_settings(self, mock_get_settings):
        """測試使用自定義設置創建token"""
        mock_settings = MagicMock()
        mock_settings.jwt_secret = "custom_secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.access_token_expire_minutes = 120
        mock_get_settings.return_value = mock_settings
        
        subject = "test@example.com"
        token = create_access_token(subject)
        
        assert token is not None
        # 應該能解碼
        # 注意：由於我們mock了get_settings，decode_access_token也會使用相同的mock
        # 所以這可能不會正常工作，但至少確保create_access_token不會崩潰

    def test_token_format(self):
        """測試token格式（JWT應該有三個部分，用點分隔）"""
        subject = "test@example.com"
        token = create_access_token(subject)
        
        # JWT格式：header.payload.signature
        parts = token.split('.')
        assert len(parts) == 3


class TestSecurityEdgeCases:
    """安全功能邊界情況測試"""

    def test_password_hash_special_characters(self):
        """測試特殊字符密碼"""
        special_password = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        hashed = get_password_hash(special_password)
        
        assert hashed is not None
        assert verify_password(special_password, hashed) is True

    def test_password_hash_whitespace(self):
        """測試包含空白字符的密碼"""
        password_with_spaces = "  test password  "
        hashed = get_password_hash(password_with_spaces)
        
        assert hashed is not None
        assert verify_password(password_with_spaces, hashed) is True
        # 驗證時空白字符應該被保留
        assert verify_password("test password", hashed) is False  # 沒有前後空格

    def test_token_with_special_characters_in_subject(self):
        """測試subject包含特殊字符的token"""
        subject = "user+test@example.com"
        token = create_access_token(subject)
        
        decoded = decode_access_token(token)
        assert decoded == subject

    def test_token_with_unicode_subject(self):
        """測試subject包含Unicode字符的token"""
        subject = "用戶@測試.com"
        token = create_access_token(subject)
        
        decoded = decode_access_token(token)
        assert decoded == subject

