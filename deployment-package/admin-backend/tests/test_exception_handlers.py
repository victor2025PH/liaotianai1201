"""
異常處理器測試
測試 FastAPI 應用中的異常處理器
"""
import pytest
import os
from unittest.mock import Mock, patch
from fastapi import Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse

from app.main import app
from app.core.errors import UserFriendlyError
from fastapi import status


client = TestClient(app)


class TestUserFriendlyErrorHandler:
    """用戶友好錯誤處理器測試"""

    def test_user_friendly_error_handler(self):
        """測試用戶友好錯誤處理"""
        # 創建一個會拋出 UserFriendlyError 的端點用於測試
        # 注意：不能在運行時動態添加路由，使用現有端點或創建臨時路由
        # 這裡測試錯誤處理器的邏輯而非動態路由
        from app.core.errors import UserFriendlyError
        from fastapi import Request
        from app.main import user_friendly_error_handler
        
        # 直接測試錯誤處理器
        mock_request = Mock(spec=Request)
        error = UserFriendlyError(
            error_code="NOT_FOUND",
            detail="測試資源不存在",
            status_code=404
        )
        
        import asyncio
        response = asyncio.run(user_friendly_error_handler(mock_request, error))
        
        assert response.status_code == 404
        data = response.body
        import json
        content = json.loads(data.decode())
        assert "error_code" in content
        assert "message" in content

    def test_user_friendly_error_handler_with_detail_dict(self):
        """測試帶字典詳情的錯誤處理"""
        from app.core.errors import UserFriendlyError
        from fastapi import Request
        from app.main import user_friendly_error_handler
        
        mock_request = Mock(spec=Request)
        error = UserFriendlyError(
            error_code="VALIDATION_ERROR",
            detail={"field": "email", "error": "無效格式"},
            status_code=400
        )
        
        import asyncio
        response = asyncio.run(user_friendly_error_handler(mock_request, error))
        
        assert response.status_code == 400
        import json
        content = json.loads(response.body.decode())
        assert isinstance(content, dict)


class TestGeneralExceptionHandler:
    """通用異常處理器測試"""

    def test_general_exception_handler_development(self):
        """測試開發環境通用異常處理"""
        original_env = os.getenv("ENVIRONMENT")
        
        try:
            os.environ["ENVIRONMENT"] = "development"
            
            from fastapi import Request
            from app.main import general_exception_handler
            
            mock_request = Mock(spec=Request)
            exception = ValueError("測試異常")
            
            import asyncio
            response = asyncio.run(general_exception_handler(mock_request, exception))
            
            # 應該返回 500 狀態碼
            assert response.status_code == 500
            
            # 開發環境應該包含詳細信息
            import json
            data = json.loads(response.body.decode())
            assert "error_code" in data
            assert "message" in data
            # 開發環境可能包含技術詳情
            if "technical_detail" in data:
                assert "測試異常" in data["technical_detail"]
        finally:
            if original_env:
                os.environ["ENVIRONMENT"] = original_env
            elif "ENVIRONMENT" in os.environ:
                del os.environ["ENVIRONMENT"]

    def test_general_exception_handler_production(self):
        """測試生產環境通用異常處理"""
        original_env = os.getenv("ENVIRONMENT")
        
        try:
            os.environ["ENVIRONMENT"] = "production"
            
            from fastapi import Request
            from app.main import general_exception_handler
            
            mock_request = Mock(spec=Request)
            exception = ValueError("測試異常")
            
            import asyncio
            response = asyncio.run(general_exception_handler(mock_request, exception))
            
            # 應該返回 500 狀態碼
            assert response.status_code == 500
            
            # 生產環境不應該包含詳細信息
            import json
            data = json.loads(response.body.decode())
            assert "error_code" in data
            assert "message" in data
            # 生產環境不應該包含 technical_detail 或 traceback
            assert "technical_detail" not in data
            assert "traceback" not in data
        finally:
            if original_env:
                os.environ["ENVIRONMENT"] = original_env
            elif "ENVIRONMENT" in os.environ:
                del os.environ["ENVIRONMENT"]

    def test_general_exception_handler_default_development(self):
        """測試默認開發環境（無環境變量）"""
        original_env = os.getenv("ENVIRONMENT")
        
        try:
            # 移除環境變量（默認為開發環境）
            if "ENVIRONMENT" in os.environ:
                del os.environ["ENVIRONMENT"]
            
            from fastapi import Request
            from app.main import general_exception_handler
            
            mock_request = Mock(spec=Request)
            exception = RuntimeError("默認環境異常")
            
            import asyncio
            response = asyncio.run(general_exception_handler(mock_request, exception))
            
            assert response.status_code == 500
            import json
            data = json.loads(response.body.decode())
            # 默認應該是開發環境，可能包含詳細信息
            assert "error_code" in data
            assert "message" in data
        finally:
            if original_env:
                os.environ["ENVIRONMENT"] = original_env

    def test_exception_handler_http_exception(self):
        """測試 HTTPException 處理（FastAPI 默認）"""
        from fastapi import HTTPException
        
        # HTTPException 由 FastAPI 默認處理，測試一個會返回 403 的場景
        # 使用現有需要權限的端點
        resp = client.get("/api/v1/users")
        
        # 應該返回 401（未認證）或 403（無權限），不會到達 HTTPException 處理器
        # 但可以驗證錯誤處理正常工作
        assert resp.status_code in [401, 403]


class TestExceptionHandlerIntegration:
    """異常處理器集成測試"""

    def test_invalid_endpoint(self):
        """測試不存在的端點"""
        resp = client.get("/nonexistent/endpoint")
        assert resp.status_code == 404

    def test_invalid_method(self):
        """測試不支持的 HTTP 方法"""
        resp = client.patch("/health")
        # 可能返回 405 (Method Not Allowed) 或 404
        assert resp.status_code in [404, 405]

    def test_validation_error(self):
        """測試驗證錯誤（通過無效請求）"""
        # 發送無效的 JSON 到需要 JSON 的端點
        resp = client.post(
            "/api/v1/auth/login",
            json={"invalid": "data"}
        )
        # 應該返回 422 (Validation Error) 或 401
        assert resp.status_code in [422, 401, 400]

