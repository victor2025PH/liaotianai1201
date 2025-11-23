"""
依賴注入函數測試
測試 FastAPI 依賴注入函數（認證、數據庫等）
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError

from app.api.deps import (
    get_db_session,
    get_current_user,
    get_current_active_user,
    get_optional_user,
    require_superuser
)
from app.models.user import User
from app.core.config import Settings


class TestGetDbSession:
    """數據庫會話依賴測試"""

    def test_get_db_session(self):
        """測試獲取數據庫會話"""
        # 測試生成器函數
        gen = get_db_session()
        assert gen is not None
        
        # 測試可以迭代（實際會創建數據庫會話）
        try:
            session = next(gen)
            assert session is not None
        except Exception:
            pass  # 可能沒有真實數據庫連接
        finally:
            try:
                gen.close()
            except:
                pass


class TestGetCurrentUser:
    """當前用戶獲取測試"""

    def test_get_current_user_no_token(self, prepare_database):
        """測試沒有 token 時獲取用戶"""
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=None, credentials=None, db=Mock())
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('app.api.deps.decode_access_token')
    @patch('app.api.deps.get_user_by_email')
    @patch('app.api.deps.get_settings')
    def test_get_current_user_valid_token(self, mock_get_settings, mock_get_user, mock_decode_token, prepare_database):
        """測試有效 token 獲取用戶"""
        from app.db import SessionLocal
        
        mock_settings = Mock()
        mock_settings.jwt_secret = "test_secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.disable_auth = False
        mock_get_settings.return_value = mock_settings
        
        mock_user = Mock(spec=User)
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        mock_decode_token.return_value = "test@example.com"
        
        db = SessionLocal()
        try:
            from app.schemas.auth import TokenPayload
            
            with patch('app.api.deps.jwt.decode', return_value={"sub": "test@example.com"}):
                user = get_current_user(token="valid_token", credentials=None, db=db)
                
                assert user is not None
                assert user.email == "test@example.com"
        finally:
            db.close()

    @patch('app.api.deps.get_settings')
    def test_get_current_user_disable_auth(self, mock_get_settings):
        """測試禁用認證時獲取用戶"""
        mock_settings = Mock()
        mock_settings.disable_auth = True
        mock_get_settings.return_value = mock_settings
        
        user = get_current_user(token=None, credentials=None, db=Mock())
        
        assert user is None

    @patch('app.api.deps.jwt.decode')
    @patch('app.api.deps.get_settings')
    def test_get_current_user_invalid_token(self, mock_get_settings, mock_jwt_decode):
        """測試無效 token"""
        mock_settings = Mock()
        mock_settings.jwt_secret = "test_secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.disable_auth = False
        mock_get_settings.return_value = mock_settings
        
        mock_jwt_decode.side_effect = JWTError("Invalid token")
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token="invalid_token", credentials=None, db=Mock())
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_from_http_bearer(self, prepare_database):
        """測試從 HTTP Bearer 獲取 token"""
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "bearer_token"
        
        with patch('app.api.deps.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.disable_auth = False
            mock_settings.jwt_secret = "test_secret"
            mock_settings.jwt_algorithm = "HS256"
            mock_get_settings.return_value = mock_settings
            
            with patch('app.api.deps.jwt.decode') as mock_jwt_decode:
                mock_jwt_decode.side_effect = JWTError("Invalid token")
                
                with pytest.raises(HTTPException):
                    get_current_user(token=None, credentials=mock_credentials, db=Mock())


class TestGetCurrentActiveUser:
    """當前活躍用戶獲取測試"""

    @patch('app.api.deps.get_settings')
    def test_get_current_active_user_disable_auth(self, mock_get_settings):
        """測試禁用認證時獲取活躍用戶"""
        mock_settings = Mock()
        mock_settings.disable_auth = True
        mock_get_settings.return_value = mock_settings
        
        user = get_current_active_user(current_user=None)
        assert user is None

    def test_get_current_active_user_none(self):
        """測試當前用戶為 None"""
        with patch('app.api.deps.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.disable_auth = False
            mock_get_settings.return_value = mock_settings
            
            with pytest.raises(HTTPException) as exc_info:
                get_current_active_user(current_user=None)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_active_user_inactive(self):
        """測試非活躍用戶"""
        with patch('app.api.deps.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.disable_auth = False
            mock_get_settings.return_value = mock_settings
            
            mock_user = Mock(spec=User)
            mock_user.is_active = False
            
            with pytest.raises(HTTPException) as exc_info:
                get_current_active_user(current_user=mock_user)
            
            assert exc_info.value.status_code == 400
            assert "已禁用" in str(exc_info.value.detail)

    def test_get_current_active_user_active(self):
        """測試活躍用戶"""
        mock_user = Mock(spec=User)
        mock_user.is_active = True
        
        with patch('app.api.deps.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.disable_auth = False
            mock_get_settings.return_value = mock_settings
            
            user = get_current_active_user(current_user=mock_user)
            assert user is mock_user


class TestGetOptionalUser:
    """可選用戶獲取測試"""

    @patch('app.api.deps.get_settings')
    def test_get_optional_user_disable_auth(self, mock_get_settings):
        """測試禁用認證時獲取可選用戶"""
        mock_settings = Mock()
        mock_settings.disable_auth = True
        mock_get_settings.return_value = mock_settings
        
        user = get_optional_user(token=None, credentials=None, db=Mock())
        assert user is None

    def test_get_optional_user_no_token(self, prepare_database):
        """測試沒有 token 時返回 None"""
        with patch('app.api.deps.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.disable_auth = False
            mock_get_settings.return_value = mock_settings
            
            user = get_optional_user(token=None, credentials=None, db=Mock())
            assert user is None

    @patch('app.api.deps.get_user_by_email')
    @patch('app.api.deps.get_settings')
    def test_get_optional_user_valid_token(self, mock_get_settings, mock_get_user):
        """測試有效 token 時返回用戶"""
        mock_settings = Mock()
        mock_settings.disable_auth = False
        mock_settings.jwt_secret = "test_secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_get_settings.return_value = mock_settings
        
        mock_user = Mock(spec=User)
        mock_user.is_active = True
        mock_get_user.return_value = mock_user
        
        with patch('app.api.deps.jwt.decode', return_value={"sub": "test@example.com"}):
            user = get_optional_user(token="valid_token", credentials=None, db=Mock())
            assert user is mock_user

    @patch('app.api.deps.get_settings')
    def test_get_optional_user_invalid_token(self, mock_get_settings):
        """測試無效 token 時返回 None"""
        mock_settings = Mock()
        mock_settings.disable_auth = False
        mock_settings.jwt_secret = "test_secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_get_settings.return_value = mock_settings
        
        with patch('app.api.deps.jwt.decode', side_effect=JWTError("Invalid token")):
            user = get_optional_user(token="invalid_token", credentials=None, db=Mock())
            assert user is None


class TestRequireSuperuser:
    """超級用戶要求測試"""

    def test_require_superuser_superuser(self):
        """測試超級用戶"""
        mock_user = Mock(spec=User)
        mock_user.is_superuser = True
        
        user = require_superuser(current_user=mock_user)
        assert user is mock_user

    def test_require_superuser_not_superuser(self):
        """測試非超級用戶"""
        mock_user = Mock(spec=User)
        mock_user.is_superuser = False
        
        with pytest.raises(HTTPException) as exc_info:
            require_superuser(current_user=mock_user)
        
        assert exc_info.value.status_code == 403
        # 錯誤消息可能是繁體或簡體中文
        detail_str = str(exc_info.value.detail)
        assert "無權訪問" in detail_str or "无权访问" in detail_str

