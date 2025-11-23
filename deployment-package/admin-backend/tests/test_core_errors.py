"""
核心錯誤處理模組測試
"""
import pytest
import os
from fastapi import status
from fastapi.responses import JSONResponse

from app.core.errors import UserFriendlyError, create_error_response


class TestUserFriendlyError:
    """用戶友好錯誤測試"""

    def test_user_friendly_error_basic(self):
        """測試基本錯誤創建"""
        error = UserFriendlyError(
            error_code="NOT_FOUND",
            detail="資源不存在"
        )
        
        assert error.status_code == 400
        assert "error_code" in error.detail
        assert "message" in error.detail
        assert error.detail["error_code"] == "NOT_FOUND"

    def test_user_friendly_error_with_custom_status(self):
        """測試自定義狀態碼"""
        error = UserFriendlyError(
            error_code="NOT_FOUND",
            status_code=404
        )
        
        assert error.status_code == 404

    def test_user_friendly_error_unknown_code(self):
        """測試未知錯誤代碼"""
        error = UserFriendlyError(
            error_code="UNKNOWN_CODE"
        )
        
        assert "發生未知錯誤" in error.detail["message"]

    def test_user_friendly_error_with_detail(self):
        """測試帶詳細信息的錯誤"""
        error = UserFriendlyError(
            error_code="VALIDATION_ERROR",
            detail="具體的驗證錯誤信息"
        )
        
        assert "具體的驗證錯誤信息" in error.detail["message"]

    def test_user_friendly_error_all_codes(self):
        """測試所有已知錯誤代碼"""
        known_codes = [
            "DATABASE_ERROR",
            "NETWORK_ERROR",
            "TIMEOUT",
            "NOT_FOUND",
            "VALIDATION_ERROR",
            "PERMISSION_DENIED",
            "RATE_LIMIT",
            "INTERNAL_ERROR",
            "FILE_NOT_FOUND",
            "INVALID_CONFIG",
        ]
        
        for code in known_codes:
            error = UserFriendlyError(error_code=code)
            assert error.detail["error_code"] == code
            assert "message" in error.detail

    def test_user_friendly_error_development_technical_detail(self):
        """測試開發環境技術詳情"""
        original_env = os.getenv("ENVIRONMENT")
        
        try:
            os.environ["ENVIRONMENT"] = "development"
            
            error = UserFriendlyError(
                error_code="DATABASE_ERROR",
                technical_detail="具體的技術錯誤信息"
            )
            
            assert "technical_detail" in error.detail
            assert error.detail["technical_detail"] == "具體的技術錯誤信息"
        finally:
            if original_env:
                os.environ["ENVIRONMENT"] = original_env
            elif "ENVIRONMENT" in os.environ:
                del os.environ["ENVIRONMENT"]

    def test_user_friendly_error_production_no_technical_detail(self):
        """測試生產環境不包含技術詳情"""
        original_env = os.getenv("ENVIRONMENT")
        
        try:
            os.environ["ENVIRONMENT"] = "production"
            
            error = UserFriendlyError(
                error_code="DATABASE_ERROR",
                technical_detail="具體的技術錯誤信息"
            )
            
            # 生產環境不應該包含技術詳情
            assert "technical_detail" not in error.detail
        finally:
            if original_env:
                os.environ["ENVIRONMENT"] = original_env
            elif "ENVIRONMENT" in os.environ:
                del os.environ["ENVIRONMENT"]


class TestCreateErrorResponse:
    """創建錯誤響應測試"""

    def test_create_error_response_basic(self):
        """測試基本錯誤響應創建"""
        response = create_error_response(
            error_code="NOT_FOUND",
            status_code=404
        )
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        
        # 獲取響應內容
        import json
        content = json.loads(response.body.decode())
        assert content["error_code"] == "NOT_FOUND"
        assert "message" in content

    def test_create_error_response_with_message(self):
        """測試帶自定義消息的錯誤響應"""
        response = create_error_response(
            error_code="VALIDATION_ERROR",
            message="自定義錯誤消息",
            status_code=400
        )
        
        import json
        content = json.loads(response.body.decode())
        assert "自定義錯誤消息" in content["message"]

    def test_create_error_response_development_technical_detail(self):
        """測試開發環境包含技術詳情"""
        original_env = os.getenv("ENVIRONMENT")
        
        try:
            os.environ["ENVIRONMENT"] = "development"
            
            response = create_error_response(
                error_code="DATABASE_ERROR",
                technical_detail="技術詳情"
            )
            
            import json
            content = json.loads(response.body.decode())
            assert "technical_detail" in content
            assert content["technical_detail"] == "技術詳情"
        finally:
            if original_env:
                os.environ["ENVIRONMENT"] = original_env
            elif "ENVIRONMENT" in os.environ:
                del os.environ["ENVIRONMENT"]

    def test_create_error_response_production_no_technical_detail(self):
        """測試生產環境不包含技術詳情"""
        original_env = os.getenv("ENVIRONMENT")
        
        try:
            os.environ["ENVIRONMENT"] = "production"
            
            response = create_error_response(
                error_code="DATABASE_ERROR",
                technical_detail="技術詳情"
            )
            
            import json
            content = json.loads(response.body.decode())
            assert "technical_detail" not in content
        finally:
            if original_env:
                os.environ["ENVIRONMENT"] = original_env
            elif "ENVIRONMENT" in os.environ:
                del os.environ["ENVIRONMENT"]

    def test_create_error_response_all_status_codes(self):
        """測試各種狀態碼"""
        status_codes = [400, 401, 403, 404, 500]
        
        for status_code in status_codes:
            response = create_error_response(
                error_code="INTERNAL_ERROR",
                status_code=status_code
            )
            
            assert response.status_code == status_code

