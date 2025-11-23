"""
統一錯誤處理
"""
from typing import Optional
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class UserFriendlyError(HTTPException):
    """用戶友好錯誤"""
    
    ERROR_MESSAGES = {
        "DATABASE_ERROR": "數據庫連接失敗，請稍後重試",
        "NETWORK_ERROR": "網絡連接異常，請檢查網絡設置",
        "TIMEOUT": "請求超時，請稍後重試",
        "NOT_FOUND": "請求的資源不存在",
        "VALIDATION_ERROR": "輸入數據格式錯誤，請檢查後重試",
        "PERMISSION_DENIED": "您沒有權限執行此操作",
        "RATE_LIMIT": "請求過於頻繁，請稍後再試",
        "INTERNAL_ERROR": "服務器內部錯誤，請聯繫管理員",
        "FILE_NOT_FOUND": "文件不存在，請檢查路徑",
        "INVALID_CONFIG": "配置錯誤，請檢查配置項",
    }
    
    def __init__(
        self,
        error_code: str,
        detail: Optional[str] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        technical_detail: Optional[str] = None
    ):
        message = self.ERROR_MESSAGES.get(error_code, "發生未知錯誤")
        if detail:
            message = f"{message}: {detail}"
        
        # 構建錯誤詳情
        error_detail = {
            "error_code": error_code,
            "message": message,
        }
        
        # 在開發環境下添加技術詳情
        import os
        if os.getenv("ENVIRONMENT", "production") == "development" and technical_detail:
            error_detail["technical_detail"] = technical_detail
        
        super().__init__(
            status_code=status_code,
            detail=error_detail
        )


def create_error_response(
    error_code: str,
    message: Optional[str] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    technical_detail: Optional[str] = None
) -> JSONResponse:
    """創建錯誤響應"""
    error_msg = UserFriendlyError.ERROR_MESSAGES.get(error_code, "發生未知錯誤")
    if message:
        error_msg = f"{error_msg}: {message}"
    
    response_data = {
        "error_code": error_code,
        "message": error_msg,
    }
    
    # 在開發環境下添加技術詳情
    import os
    if os.getenv("ENVIRONMENT", "production") == "development" and technical_detail:
        response_data["technical_detail"] = technical_detail
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )

