"""
群組 AI 賬號管理 API
"""
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query
from typing import List, Optional
from pydantic import BaseModel
import sys
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 導入緩存功能
from app.core.cache import cached, invalidate_cache
from app.core.errors import UserFriendlyError

# 導入限流（可選）
try:
    from app.core.limiter import limiter, RATE_LIMITS
    from slowapi.errors import RateLimitExceeded
    from fastapi import Request
    RATE_LIMITING_ENABLED = True
except ImportError:
    RATE_LIMITING_ENABLED = False
    limiter = None
    RATE_LIMITS = {}
    RateLimitExceeded = Exception

# 添加項目根目錄到路徑
# accounts.py 在 admin-backend/app/api/group_ai/ 目錄
# 需要向上 4 級到達項目根目錄
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from group_ai_service import AccountManager
from group_ai_service.service_manager import ServiceManager
from group_ai_service.models.account import AccountConfig, AccountStatusEnum

from app.db import get_db
from app.models.group_ai import GroupAIAccount
from sqlalchemy.orm import Session
from app.utils.telegram_profile import get_telegram_profile
from app.api.deps import get_current_active_user
from app.middleware.permission import check_permission, require_permission
from app.core.permissions import PermissionCode
from app.models.user import User

router = APIRouter()

# 全局 ServiceManager 實例（統一管理所有服務）
_service_manager: Optional[ServiceManager] = None


def get_service_manager() -> ServiceManager:
    """獲取 ServiceManager 實例（單例模式）"""
    global _service_manager
    if _service_manager is None:
        try:
            logger.info("初始化 ServiceManager...")
            _service_manager = ServiceManager()
            logger.info("ServiceManager 初始化成功")
        except Exception as e:
            logger.exception(f"ServiceManager 初始化失敗: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"服務管理器初始化失敗: {str(e)}"
            )
    return _service_manager


def get_account_manager() -> AccountManager:
    """獲取 AccountManager 實例（通過 ServiceManager）"""
    return get_service_manager().account_manager


# ============ 請求/響應模型 ============

class AccountCreateRequest(BaseModel):
    account_id: str
    session_file: str
    script_id: str = "default"
    group_ids: List[int] = []
    active: bool = True
    reply_rate: float = 0.3
    redpacket_enabled: bool = True
    redpacket_probability: float = 0.5
    max_replies_per_hour: int = 50
    min_reply_interval: int = 3


class AccountUpdateRequest(BaseModel):
    script_id: Optional[str] = None
    server_id: Optional[str] = None  # 服務器ID
    group_ids: Optional[List[int]] = None
    active: Optional[bool] = None
    reply_rate: Optional[float] = None
    redpacket_enabled: Optional[bool] = None
    redpacket_probability: Optional[float] = None
    max_replies_per_hour: Optional[int] = None
    min_reply_interval: Optional[int] = None
    # 帳號資料信息（可編輯）
    display_name: Optional[str] = None  # 顯示名稱（可編輯）
    bio: Optional[str] = None  # 個人簡介（可編輯）


class AccountResponse(BaseModel):
    account_id: str
    session_file: str
    script_id: str
    server_id: Optional[str] = None  # 關聯的服務器ID
    status: str
    group_count: int
    message_count: int
    reply_count: int
    last_activity: Optional[str] = None
    # 帳號資料信息
    phone_number: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    user_id: Optional[int] = None


class AccountStatusResponse(BaseModel):
    account_id: str
    status: str
    online: bool
    last_activity: Optional[str] = None
    message_count: int
    reply_count: int
    redpacket_count: int
    error_count: int
    last_error: Optional[str] = None
    uptime_seconds: int


class AccountListResponse(BaseModel):
    items: List[AccountResponse]
    total: int


class BatchImportRequest(BaseModel):
    directory: str
    script_id: str = "default"
    group_ids: List[int] = []


# ============ API 端點 ============

@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    request: AccountCreateRequest,
    current_user: User = Depends(get_current_active_user),
    service_manager: ServiceManager = Depends(get_service_manager),
    db: Session = Depends(get_db)
):
    """創建賬號（需要 account:create 權限）"""
    check_permission(current_user, PermissionCode.ACCOUNT_CREATE.value, db)
    try:
        from pathlib import Path
        from group_ai_service.config import get_group_ai_config
        
        # 處理session文件路徑
        session_file = request.session_file
        session_path = Path(session_file)
        
        # 如果是絕對路徑，直接驗證文件是否存在
        if session_path.is_absolute():
            if not session_path.exists():
                logger.error(f"Session 文件不存在（絕對路徑）: {session_file}")
                raise UserFriendlyError(
                    "FILE_NOT_FOUND",
                    detail=f"Session 文件不存在: {session_file}。請檢查文件路徑是否正確。",
                    status_code=404
                )
            # 絕對路徑存在，直接使用
            session_file = str(session_path)
            logger.info(f"使用絕對路徑 Session 文件: {session_file}")
        # 如果是相對路徑，嘗試從sessions目錄查找
        else:
            config = get_group_ai_config()
            
            # 方法1: 從當前工作目錄解析
            current_work_dir = Path.cwd()
            sessions_dir_from_cwd = current_work_dir / config.session_files_directory
            
            # 方法2: 從API文件位置解析項目根目錄
            api_file_path = Path(__file__).resolve()
            project_root_from_api = api_file_path.parent.parent.parent.parent.parent
            sessions_dir_from_api = project_root_from_api / config.session_files_directory
            
            # 優先使用存在的目錄
            sessions_dir = None
            if sessions_dir_from_cwd.exists():
                sessions_dir = sessions_dir_from_cwd
                logger.info(f"使用當前工作目錄的 sessions: {sessions_dir}")
            elif sessions_dir_from_api.exists():
                sessions_dir = sessions_dir_from_api
                logger.info(f"使用項目根目錄的 sessions: {sessions_dir}")
            
            if sessions_dir and sessions_dir.exists():
                # 如果輸入的是文件名，直接從sessions目錄查找
                session_path = sessions_dir / Path(session_file).name
                
                if session_path.exists():
                    session_file = str(session_path)
                    logger.info(f"找到 Session 文件: {session_file}")
                else:
                    logger.warning(f"Session 文件不存在: {session_path}")
                    # 列出目录中的文件用于调试
                    all_files = list(sessions_dir.glob("*.session"))
                    logger.warning(f"Sessions 目錄中的文件: {[f.name for f in all_files]}")
            else:
                logger.warning(f"Sessions 目錄不存在: sessions_dir_from_cwd={sessions_dir_from_cwd}, sessions_dir_from_api={sessions_dir_from_api}")
            
            # 最終驗證 - 如果文件不存在，再次嘗試從項目根目錄解析
            final_path = Path(session_file)
            if not final_path.exists():
                # 再次嘗試從項目根目錄解析
                api_file_path = Path(__file__).resolve()
                project_root = api_file_path.parent.parent.parent.parent.parent
                sessions_dir_final = project_root / config.session_files_directory
                if sessions_dir_final.exists():
                    final_path = sessions_dir_final / Path(session_file).name
                    if final_path.exists():
                        session_file = str(final_path)
                        logger.info(f"最終找到 Session 文件: {session_file}")
            
            if not Path(session_file).exists():
                logger.error(f"Session 文件驗證失敗: {session_file}")
                logger.error(f"請求的 session_file: {request.session_file}")
                logger.error(f"當前工作目錄: {Path.cwd()}")
                logger.error(f"API文件路徑: {Path(__file__).resolve()}")
                # 列出sessions目录中的所有文件用于调试
                api_file_path = Path(__file__).resolve()
                project_root = api_file_path.parent.parent.parent.parent.parent
                sessions_dir_final = project_root / config.session_files_directory
                if sessions_dir_final.exists():
                    all_files = list(sessions_dir_final.glob("*.session"))
                    logger.error(f"Sessions 目錄 ({sessions_dir_final}) 中的文件: {[f.name for f in all_files]}")
                raise UserFriendlyError(
                    "FILE_NOT_FOUND",
                    detail=f"Session 文件不存在: {request.session_file}。請確保文件位於 sessions 文件夾內。嘗試的路徑: {session_file}",
                    status_code=404
                )
        
        config = AccountConfig(
            account_id=request.account_id,
            session_file=session_file,  # 使用解析後的路徑
            script_id=request.script_id,
            group_ids=request.group_ids,
            active=request.active,
            reply_rate=request.reply_rate,
            redpacket_enabled=request.redpacket_enabled,
            redpacket_probability=request.redpacket_probability,
            max_replies_per_hour=request.max_replies_per_hour,
            min_reply_interval=request.min_reply_interval
        )
        
        # 保存本地文件路徑（用於獲取資料信息）
        local_session_file = session_file
        
        # 獲取帳號資料信息（從Telegram，使用本地文件）
        profile_info = None
        try:
            logger.info(f"開始獲取帳號資料信息: {local_session_file}")
            profile_info = await get_telegram_profile(local_session_file)
            if profile_info:
                logger.info(f"成功獲取帳號資料信息: user_id={profile_info.get('user_id')}, username={profile_info.get('username')}, display_name={profile_info.get('display_name')}")
            else:
                logger.warning(f"無法獲取帳號資料信息，可能是：1) Pyrogram 未安裝 2) API_ID/API_HASH 未設置 3) Session 文件無效或需要驗證")
        except Exception as e:
            logger.warning(f"獲取帳號資料信息失敗: {e}，將繼續創建帳號", exc_info=True)
        
        # 自動上傳session文件到遠程服務器（智能分配，每個服務器最多5個賬號）
        server_id = None
        try:
            from app.api.group_ai.session_uploader import SessionUploader
            
            uploader = SessionUploader()
            if uploader.servers:
                # 使用智能分配算法找到最適合的服務器
                # 使用本地文件路徑上傳
                server_node, remote_path, error_msg = uploader.auto_upload_and_assign(
                    session_file=str(Path(local_session_file)),
                    account_id=request.account_id
                )
                
                if server_node and remote_path:
                    logger.info(f"Session文件已自動分配到服務器 {server_node.node_id}: {remote_path}")
                    # 使用遠程路徑作為session_file（用於AccountManager）
                    session_file = remote_path
                    server_id = server_node.node_id
                else:
                    logger.warning(f"自動分配失敗: {error_msg}，繼續使用本地文件")
            else:
                logger.info("未配置遠程服務器，使用本地文件")
        except Exception as e:
            logger.warning(f"自動上傳session文件時出錯: {e}，繼續使用本地文件")
        
        try:
            account = await service_manager.account_manager.add_account(
                account_id=request.account_id,
                session_file=session_file,  # 使用解析後的路徑（可能是遠程路徑）
                config=config
            )
        except FileNotFoundError as e:
            # AccountManager 拋出的 FileNotFoundError，轉換為 UserFriendlyError
            raise UserFriendlyError(
                "FILE_NOT_FOUND",
                detail=str(e),
                status_code=404
            )
        except Exception as e:
            # AccountManager 的其他異常
            logger.error(f"AccountManager.add_account 失敗: {e}", exc_info=True)
            raise UserFriendlyError(
                "INTERNAL_ERROR",
                detail=f"添加賬號到 AccountManager 失敗: {str(e)}",
                technical_detail=str(e),
                status_code=500
            )
        
        # 保存帳號資料信息到數據庫
        db_account = db.query(GroupAIAccount).filter(
            GroupAIAccount.account_id == request.account_id
        ).first()
        
        if not db_account:
            # 創建新的數據庫記錄
            db_account = GroupAIAccount(
                account_id=request.account_id,
                session_file=session_file,
                script_id=request.script_id,
                server_id=server_id,
                group_ids=request.group_ids,
                active=request.active,
                reply_rate=request.reply_rate,
                redpacket_enabled=request.redpacket_enabled,
                redpacket_probability=request.redpacket_probability,
                max_replies_per_hour=request.max_replies_per_hour,
                min_reply_interval=request.min_reply_interval
            )
            db.add(db_account)
        else:
            # 更新現有記錄
            db_account.server_id = server_id or db_account.server_id
            db_account.script_id = request.script_id
        
        # 如果有獲取到資料信息，保存到數據庫
        if profile_info:
            db_account.phone_number = profile_info.get("phone_number")
            db_account.username = profile_info.get("username")
            db_account.first_name = profile_info.get("first_name")
            db_account.last_name = profile_info.get("last_name")
            db_account.display_name = profile_info.get("display_name") or profile_info.get("first_name")
            db_account.avatar_url = profile_info.get("avatar_url")
            db_account.bio = profile_info.get("bio")
            db_account.user_id = profile_info.get("user_id")
        
        try:
            # 先 flush 確保數據寫入（但不提交事務）
            db.flush()
            # 然後提交事務
            db.commit()
            # 刷新對象以獲取最新數據（包括自動生成的字段）
            db.refresh(db_account)
            
            logger.info(f"賬號創建成功: {request.account_id} (數據庫 ID: {db_account.id})")
            
            # 驗證數據是否已保存（使用新的會話確保讀取到最新數據）
            from app.db import SessionLocal as NewSessionLocal
            verify_db = NewSessionLocal()
            try:
                saved_account = verify_db.query(GroupAIAccount).filter(
                    GroupAIAccount.account_id == request.account_id
                ).first()
                if not saved_account:
                    logger.error(f"賬號創建後驗證失敗: {request.account_id} 在數據庫中不存在")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="賬號保存失敗：數據未正確寫入數據庫"
                    )
                logger.info(f"賬號驗證成功: {saved_account.account_id} 已持久化到數據庫")
            finally:
                verify_db.close()
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"保存賬號到數據庫失敗: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"保存賬號失敗: {str(e)}"
            )
        
        account_info = service_manager.account_manager.list_accounts()
        account_data = next((a for a in account_info if a.account_id == request.account_id), None)
        
        if not account_data:
            # 嘗試從數據庫獲取信息，即使 AccountManager 中沒有
            logger.warning(f"AccountManager 中找不到賬號 {request.account_id}，但數據庫記錄已創建")
            # 仍然返回數據庫中的記錄信息
            return AccountResponse(
                account_id=db_account.account_id,
                session_file=db_account.session_file,
                script_id=db_account.script_id,
                server_id=db_account.server_id,
                status="offline",  # 默認狀態為離線
                group_count=len(db_account.group_ids) if db_account.group_ids else 0,
                message_count=0,
                reply_count=0,
                last_activity=None,
                phone_number=db_account.phone_number,
                username=db_account.username,
                first_name=db_account.first_name,
                last_name=db_account.last_name,
                display_name=db_account.display_name,
                avatar_url=db_account.avatar_url,
                bio=db_account.bio,
                user_id=db_account.user_id
            )
        
        # 清除緩存
        invalidate_cache("accounts_list*")
        
        return AccountResponse(
            account_id=account_data.account_id,
            session_file=account_data.session_file,
            script_id=account_data.script_id,
            server_id=db_account.server_id,
            status=account_data.status.value,
            group_count=account_data.group_count,
            message_count=account_data.message_count,
            reply_count=account_data.reply_count,
            last_activity=account_data.last_activity.isoformat() if account_data.last_activity else None,
            phone_number=db_account.phone_number,
            username=db_account.username,
            first_name=db_account.first_name,
            last_name=db_account.last_name,
            display_name=db_account.display_name,
            avatar_url=db_account.avatar_url,
            bio=db_account.bio,
            user_id=db_account.user_id
        )
    
    except UserFriendlyError:
        raise
    except FileNotFoundError as e:
        raise UserFriendlyError(
            "FILE_NOT_FOUND",
            detail=str(e),
            status_code=404
        )
    except Exception as e:
        logger.exception(f"創建賬號失敗: {e}")
        raise UserFriendlyError(
            "INTERNAL_ERROR",
            technical_detail=str(e),
            status_code=500
        )


@router.get("/scan-sessions", status_code=status.HTTP_200_OK)
async def scan_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """掃描 sessions 文件夾內的所有有效 session 文件（需要 session:view 權限）"""
    check_permission(current_user, PermissionCode.SESSION_VIEW.value, db)
    try:
        from group_ai_service.config import get_group_ai_config
        
        config = get_group_ai_config()
        sessions_dir = Path(config.session_files_directory)
        
        # 如果是相對路徑，嘗試從項目根目錄解析
        if not sessions_dir.is_absolute():
            # 方法1: 從API文件位置解析項目根目錄（優先使用）
            # __file__ 是 admin-backend/app/api/group_ai/accounts.py
            # 向上5級到達項目根目錄: parent.parent.parent.parent.parent
            # accounts.py -> group_ai -> api -> app -> admin-backend -> 項目根目錄
            api_file_path = Path(__file__).resolve()
            project_root_from_api = api_file_path.parent.parent.parent.parent.parent
            sessions_dir_from_api = project_root_from_api / config.session_files_directory
            
            # 方法2: 從當前工作目錄解析（備用）
            current_work_dir = Path.cwd()
            sessions_dir_from_cwd = current_work_dir / config.session_files_directory
            
            # 優先使用從API文件解析的路徑（更可靠）
            if sessions_dir_from_api.exists():
                sessions_dir = sessions_dir_from_api
                logger.info(f"從項目根目錄解析 Session 目錄: {sessions_dir}")
            elif sessions_dir_from_cwd.exists():
                sessions_dir = sessions_dir_from_cwd
                logger.info(f"從當前工作目錄找到 Session 目錄: {sessions_dir}")
            else:
                # 如果都不存在，使用項目根目錄的（即使不存在也記錄）
                sessions_dir = sessions_dir_from_api
                logger.warning(f"Session 目錄不存在，嘗試的路徑: {sessions_dir}")
                logger.debug(f"當前工作目錄: {current_work_dir}")
                logger.debug(f"API文件路徑: {api_file_path}")
                logger.debug(f"項目根目錄: {project_root_from_api}")
                logger.debug(f"從CWD解析: {sessions_dir_from_cwd} (存在: {sessions_dir_from_cwd.exists()})")
                logger.debug(f"從API解析: {sessions_dir_from_api} (存在: {sessions_dir_from_api.exists()})")
        
        # 如果目錄不存在，返回空列表
        if not sessions_dir.exists():
            logger.warning(f"Session 目錄不存在: {sessions_dir}")
            return {
                "sessions": [],
                "count": 0,
                "directory": str(sessions_dir),
                "exists": False
            }
        
        # 掃描所有 session 文件（包括加密和明文）
        from utils.session_encryption import get_session_manager
        from utils.session_permissions import get_session_permission_manager
        from utils.session_audit import log_session_access
        
        session_manager = get_session_manager()
        permission_manager = get_session_permission_manager()
        
        # 使用 SessionFileManager 列出所有文件（包括加密和明文）
        all_sessions = session_manager.list_sessions()
        logger.debug(f"在目錄 {sessions_dir} 中找到 {len(all_sessions)} 個 session 文件（包括加密文件）")
        
        # 記錄審計日誌
        log_session_access(
            user_id=current_user.id,
            user_email=current_user.email,
            action="view",
            file_path=str(sessions_dir),
            success=True,
            metadata={"file_count": len(all_sessions)}
        )
        
        # 更新 Prometheus 指標
        try:
            from app.monitoring.prometheus_metrics import update_session_metrics, session_files_total
            update_session_metrics(action="view", status="success")
            
            # 更新 Session 文件总数
            plain_count = sum(1 for f in all_sessions if not f.name.endswith('.encrypted'))
            encrypted_count = sum(1 for f in all_sessions if f.name.endswith('.encrypted'))
            session_files_total.labels(type="plain").set(plain_count)
            session_files_total.labels(type="encrypted").set(encrypted_count)
        except Exception as e:
            logger.debug(f"更新 Prometheus 指標失敗: {e}")
        
        sessions = []
        for session_file in all_sessions:
            try:
                # 排除 journal 文件
                if session_file.name.endswith("-journal"):
                    continue
                
                # 排除測試帳號（文件名以 test 開頭，不區分大小寫）
                filename_lower = session_file.name.lower()
                if filename_lower.startswith("test"):
                    logger.debug(f"跳過測試帳號: {session_file.name}")
                    continue
                
                # 檢查文件是否有效（至少有一些內容）
                file_size = session_file.stat().st_size
                if file_size > 0:
                    # 檢查是否為加密文件
                    is_encrypted = session_manager.encryptor and session_manager.encryptor.is_encrypted_file(session_file)
                    
                    # 檢查文件權限
                    permissions = permission_manager.get_file_permissions(session_file)
                    
                    sessions.append({
                        "filename": session_file.name,
                        "path": str(session_file),
                        "size": file_size,
                        "modified": session_file.stat().st_mtime,
                        "encrypted": is_encrypted,
                        "permissions": permissions
                    })
                else:
                    logger.warning(f"跳過空文件: {session_file.name}")
            except Exception as e:
                logger.warning(f"處理文件 {session_file.name} 時出錯: {e}")
        
        logger.info(f"掃描到 {len(sessions)} 個有效的 session 文件（目錄: {sessions_dir}）")
        
        return {
            "sessions": sessions,
            "count": len(sessions),
            "directory": str(sessions_dir),
            "exists": True
        }
    
    except Exception as e:
        logger.error(f"掃描 Session 文件失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"掃描 Session 文件失敗: {str(e)}"
        )


@router.post("/upload-session", status_code=status.HTTP_200_OK)
async def upload_session_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """上傳 session 文件（需要 session:upload 權限）"""
    check_permission(current_user, PermissionCode.SESSION_UPLOAD.value, db)
    try:
        from group_ai_service.config import get_group_ai_config
        
        # 驗證文件擴展名
        if not file.filename.endswith('.session'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持 .session 文件"
            )
        
        # 獲取 sessions 目錄
        config = get_group_ai_config()
        sessions_dir = Path(config.session_files_directory)
        
        # 確保目錄存在
        sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        file_path = sessions_dir / file.filename
        
        # 如果文件已存在，添加後綴
        counter = 1
        original_path = file_path
        while file_path.exists():
            stem = original_path.stem
            file_path = sessions_dir / f"{stem}_{counter}.session"
            counter += 1
        
        # 讀取文件內容
        content = await file.read()
        
        # 檢查是否啟用加密存儲
        from utils.session_encryption import get_session_manager
        from utils.session_permissions import get_session_permission_manager
        
        session_manager = get_session_manager()
        permission_manager = get_session_permission_manager()
        
        # 保存文件（根據配置決定是否加密）
        saved_path = session_manager.save_session(content, file.filename)
        
        # 設置文件權限（僅所有者可讀寫）
        permission_manager.secure_new_file(saved_path)
        
        # 記錄審計日誌
        from utils.session_audit import log_session_access
        log_session_access(
            user_id=current_user.id,
            user_email=current_user.email,
            action="upload",
            file_path=str(saved_path),
            success=True
        )
        
        # 更新 Prometheus 指標
        try:
            from app.monitoring.prometheus_metrics import update_session_metrics
            update_session_metrics(
                action="upload",
                status="success",
                file_type="encrypted" if session_manager.encryption_enabled else "plain"
            )
        except Exception as e:
            logger.debug(f"更新 Prometheus 指標失敗: {e}")
        
        logger.info(f"Session 文件已上傳: {saved_path} (用戶: {current_user.email})")
        
        return {
            "success": True,
            "message": f"文件已上傳到 {saved_path.name}",
            "filename": saved_path.name,
            "path": str(saved_path),
            "encrypted": session_manager.encryption_enabled,
            "permissions": permission_manager.get_file_permissions(saved_path)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上傳 Session 文件失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上傳 Session 文件失敗: {str(e)}"
        )


@router.get("/", response_model=AccountListResponse)
async def list_accounts(
    request: Request,  # 用於限流
    current_user: User = Depends(get_current_active_user),
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁數量"),
    search: Optional[str] = Query(None, description="搜索關鍵詞（賬號ID、顯示名稱、用戶名、手機號）"),
    status_filter: Optional[str] = Query(None, description="狀態過濾（online, offline, error）"),
    script_id: Optional[str] = Query(None, description="劇本ID過濾"),
    server_id: Optional[str] = Query(None, description="服務器ID過濾"),
    active: Optional[bool] = Query(None, description="是否激活過濾"),
    sort_by: Optional[str] = Query("created_at", description="排序字段（account_id, display_name, created_at, script_id）"),
    sort_order: Optional[str] = Query("desc", description="排序順序（asc, desc）"),
    service_manager: ServiceManager = Depends(get_service_manager),
    db: Session = Depends(get_db)
):
    """列出所有賬號（支持搜索、過濾、排序）"""
    check_permission(current_user, PermissionCode.ACCOUNT_VIEW.value, db)
    
    # 生成緩存鍵（僅在無搜索/過濾時使用緩存）
    use_cache = not (search or status_filter or script_id or server_id or active is not None)
    cache_key = None
    if use_cache:
        from app.core.cache import get_cache_manager, get_cache_key
        cache_manager = get_cache_manager()
        cache_key = get_cache_key(
            "accounts_list",
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            logger.debug(f"從緩存獲取賬號列表: page={page}")
            return AccountListResponse(**cached_result)
    
    try:
        # 從數據庫獲取賬號列表（包含完整信息）
        db_query = db.query(GroupAIAccount)
        
        # 搜索過濾
        if search:
            search_filter = f"%{search}%"
            db_query = db_query.filter(
                (GroupAIAccount.account_id.like(search_filter)) |
                (GroupAIAccount.display_name.like(search_filter)) |
                (GroupAIAccount.username.like(search_filter)) |
                (GroupAIAccount.phone_number.like(search_filter))
            )
        
        # 劇本ID過濾
        if script_id:
            db_query = db_query.filter(GroupAIAccount.script_id == script_id)
        
        # 服務器ID過濾
        if server_id:
            db_query = db_query.filter(GroupAIAccount.server_id == server_id)
        
        # 激活狀態過濾
        if active is not None:
            db_query = db_query.filter(GroupAIAccount.active == active)
        
        # 排序
        if sort_by == "account_id":
            order_by = GroupAIAccount.account_id
        elif sort_by == "display_name":
            order_by = GroupAIAccount.display_name
        elif sort_by == "script_id":
            order_by = GroupAIAccount.script_id
        else:  # 默認按創建時間
            order_by = GroupAIAccount.created_at
        
        if sort_order == "asc":
            db_query = db_query.order_by(order_by.asc())
        else:
            db_query = db_query.order_by(order_by.desc())
        
        # 獲取總數
        total = db_query.count()
        
        # 分頁
        offset = (page - 1) * page_size
        db_accounts = db_query.offset(offset).limit(page_size).all()
        
        # 獲取 AccountManager（用於獲取實時狀態）
        logger.debug("獲取 AccountManager...")
        manager = service_manager.account_manager
        logger.debug(f"AccountManager 獲取成功，帳號數量: {len(manager.accounts)}")
        
        # 構建響應數據
        items = []
        for db_account in db_accounts:
            # 從 AccountManager 獲取實時狀態
            account_info = manager.accounts.get(db_account.account_id)
            if account_info:
                status_value = account_info.status.value
                group_count = len(account_info.config.group_ids) if account_info.config.group_ids else 0
                message_count = 0  # 可以從監控服務獲取
                reply_count = 0
                last_activity = None
            else:
                status_value = "offline"
                group_count = len(db_account.group_ids) if db_account.group_ids else 0
                message_count = 0
                reply_count = 0
                last_activity = None
            
            # 狀態過濾（如果指定）
            if status_filter and status_value != status_filter:
                continue
            
            items.append(AccountResponse(
                account_id=db_account.account_id,
                session_file=db_account.session_file,
                script_id=db_account.script_id,
                server_id=db_account.server_id,
                status=status_value,
                group_count=group_count,
                message_count=message_count,
                reply_count=reply_count,
                last_activity=last_activity,
                phone_number=db_account.phone_number,
                username=db_account.username,
                first_name=db_account.first_name,
                last_name=db_account.last_name,
                display_name=db_account.display_name,
                avatar_url=db_account.avatar_url,
                bio=db_account.bio,
                user_id=db_account.user_id
            ))
        
        # 如果進行了狀態過濾，需要重新計算總數
        if status_filter:
            total = len(items)
        
        logger.debug(f"返回 {len(items)} 個帳號 (page={page}, page_size={page_size}, total={total})")
        result = AccountListResponse(items=items, total=total)
        
        # 緩存結果（僅在無搜索/過濾時）
        if use_cache and cache_key:
            cache_manager.set(cache_key, result.dict(), expire=60)  # 緩存60秒
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"獲取賬號列表失敗: {e}", exc_info=True)
        # 返回更詳細的錯誤信息（開發環境）
        import os
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "development":
            detail = f"獲取賬號列表失敗: {str(e)}\n錯誤類型: {type(e).__name__}"
        else:
            detail = "獲取賬號列表失敗，請聯繫管理員"
        raise HTTPException(status_code=500, detail=detail)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    manager: AccountManager = Depends(get_account_manager),
    db: Session = Depends(get_db)
):
    """獲取賬號詳情（需要 account:view 權限）"""
    check_permission(current_user, PermissionCode.ACCOUNT_VIEW.value, db)
    try:
        accounts = manager.list_accounts()
        account = next((a for a in accounts if a.account_id == account_id), None)
        
        if not account:
            raise HTTPException(status_code=404, detail=f"賬號 {account_id} 不存在")
        
        return AccountResponse(
            account_id=account.account_id,
            session_file=account.session_file,
            script_id=account.script_id,
            status=account.status.value,
            group_count=account.group_count,
            message_count=account.message_count,
            reply_count=account.reply_count,
            last_activity=account.last_activity.isoformat() if account.last_activity else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取賬號詳情失敗: {str(e)}")


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    request: AccountUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    manager: AccountManager = Depends(get_account_manager),
    db: Session = Depends(get_db)
):
    """更新賬號（需要 account:update 權限）"""
    check_permission(current_user, PermissionCode.ACCOUNT_UPDATE.value, db)
    try:
        if account_id not in manager.accounts:
            raise HTTPException(status_code=404, detail=f"賬號 {account_id} 不存在")
        
        account = manager.accounts[account_id]
        
        # 更新配置
        if request.script_id is not None:
            account.config.script_id = request.script_id
        if request.group_ids is not None:
            account.config.group_ids = request.group_ids
        if request.active is not None:
            account.config.active = request.active
        if request.reply_rate is not None:
            account.config.reply_rate = request.reply_rate
        if request.redpacket_enabled is not None:
            account.config.redpacket_enabled = request.redpacket_enabled
        if request.redpacket_probability is not None:
            account.config.redpacket_probability = request.redpacket_probability
        if request.max_replies_per_hour is not None:
            account.config.max_replies_per_hour = request.max_replies_per_hour
        if request.min_reply_interval is not None:
            account.config.min_reply_interval = request.min_reply_interval
        
        # 更新數據庫記錄
        db_account = db.query(GroupAIAccount).filter(
            GroupAIAccount.account_id == account_id
        ).first()
        
        if db_account:
            # 更新配置字段
            if request.script_id is not None:
                db_account.script_id = request.script_id
            if request.server_id is not None:
                db_account.server_id = request.server_id
            if request.group_ids is not None:
                db_account.group_ids = request.group_ids
            if request.active is not None:
                db_account.active = request.active
            if request.reply_rate is not None:
                db_account.reply_rate = request.reply_rate
            if request.redpacket_enabled is not None:
                db_account.redpacket_enabled = request.redpacket_enabled
            if request.redpacket_probability is not None:
                db_account.redpacket_probability = request.redpacket_probability
            if request.max_replies_per_hour is not None:
                db_account.max_replies_per_hour = request.max_replies_per_hour
            if request.min_reply_interval is not None:
                db_account.min_reply_interval = request.min_reply_interval
            
            # 更新資料信息（可編輯字段）
            if request.display_name is not None:
                db_account.display_name = request.display_name
            if request.bio is not None:
                db_account.bio = request.bio
            
            db.commit()
            db.refresh(db_account)
        else:
            # 如果數據庫記錄不存在，創建一個（不應該發生，但為了安全性）
            logger.warning(f"數據庫記錄不存在，創建新記錄: {account_id}")
            db_account = GroupAIAccount(
                account_id=account_id,
                session_file=account.config.session_file,
                script_id=request.script_id or account.config.script_id,
                server_id=request.server_id,
                group_ids=request.group_ids or account.config.group_ids,
                active=request.active if request.active is not None else account.config.active,
                reply_rate=request.reply_rate if request.reply_rate is not None else account.config.reply_rate,
                redpacket_enabled=request.redpacket_enabled if request.redpacket_enabled is not None else account.config.redpacket_enabled,
                redpacket_probability=request.redpacket_probability if request.redpacket_probability is not None else account.config.redpacket_probability,
                max_replies_per_hour=request.max_replies_per_hour if request.max_replies_per_hour is not None else account.config.max_replies_per_hour,
                min_reply_interval=request.min_reply_interval if request.min_reply_interval is not None else account.config.min_reply_interval,
                display_name=request.display_name,
                bio=request.bio
            )
            db.add(db_account)
            db.commit()
            db.refresh(db_account)
        
        # 返回更新後的賬號信息
        accounts = manager.list_accounts()
        account_data = next((a for a in accounts if a.account_id == account_id), None)
        
        if not account_data:
            raise HTTPException(status_code=500, detail="更新失敗")
        
        # 清除緩存
        invalidate_cache("accounts_list*")
        
        return AccountResponse(
            account_id=account_data.account_id,
            session_file=account_data.session_file,
            script_id=account_data.script_id,
            server_id=db_account.server_id if db_account else None,
            status=account_data.status.value,
            group_count=account_data.group_count,
            message_count=account_data.message_count,
            reply_count=account_data.reply_count,
            last_activity=account_data.last_activity.isoformat() if account_data.last_activity else None,
            phone_number=db_account.phone_number if db_account else None,
            username=db_account.username if db_account else None,
            first_name=db_account.first_name if db_account else None,
            last_name=db_account.last_name if db_account else None,
            display_name=db_account.display_name if db_account else None,
            avatar_url=db_account.avatar_url if db_account else None,
            bio=db_account.bio if db_account else None,
            user_id=db_account.user_id if db_account else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新賬號失敗: {str(e)}")


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    manager: AccountManager = Depends(get_account_manager),
    db: Session = Depends(get_db)
):
    """刪除賬號（需要 account:delete 權限）"""
    check_permission(current_user, PermissionCode.ACCOUNT_DELETE.value, db)
    try:
        # 先檢查數據庫中是否存在
        db_account = db.query(GroupAIAccount).filter(
            GroupAIAccount.account_id == account_id
        ).first()
        
        # 嘗試從 AccountManager 中移除（如果存在）
        manager_success = False
        try:
            manager_success = await manager.remove_account(account_id)
        except Exception as e:
            logger.warning(f"從 AccountManager 移除賬號 {account_id} 失敗（可能不存在）: {e}")
        
        # 如果數據庫中存在，刪除數據庫記錄
        if db_account:
            db.delete(db_account)
            db.commit()
            logger.info(f"已從數據庫刪除賬號: {account_id}")
        
        # 如果 AccountManager 和數據庫中都不存在，返回 404
        if not manager_success and not db_account:
            raise HTTPException(status_code=404, detail=f"賬號 {account_id} 不存在")
        
        # 清除緩存
        invalidate_cache("accounts_list*")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"刪除賬號失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"刪除賬號失敗: {str(e)}")


@router.post("/batch-import")
async def batch_import_accounts(
    request: BatchImportRequest,
    current_user: User = Depends(get_current_active_user),
    manager: AccountManager = Depends(get_account_manager),
    db: Session = Depends(get_db)
):
    """批量導入賬號（需要 account:batch_operate 權限）"""
    check_permission(current_user, PermissionCode.ACCOUNT_BATCH_OPERATE.value, db)
    try:
        loaded = await manager.load_accounts_from_directory(
            directory=request.directory,
            script_id=request.script_id,
            group_ids=request.group_ids
        )
        return {
            "message": "批量導入完成",
            "loaded_count": len(loaded),
            "account_ids": loaded
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量導入失敗: {str(e)}")


@router.post("/{account_id}/start")
async def start_account(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    service_manager: ServiceManager = Depends(get_service_manager),
    db: Session = Depends(get_db)
):
    """啟動賬號（需要 account:start 權限）"""
    check_permission(current_user, PermissionCode.ACCOUNT_START.value, db)
    try:
        # 先檢查 AccountManager 中是否存在
        if account_id not in service_manager.account_manager.accounts:
            # 如果不存在，檢查數據庫中是否存在
            db_account = db.query(GroupAIAccount).filter(
                GroupAIAccount.account_id == account_id
            ).first()
            
            if not db_account:
                raise HTTPException(status_code=404, detail=f"賬號 {account_id} 不存在")
            
            # 從數據庫加載賬號到 AccountManager
            logger.info(f"賬號 {account_id} 不在 AccountManager 中，嘗試從數據庫加載")
            try:
                from group_ai_service.models.account import AccountConfig
                from pathlib import Path
                
                # 解析 session 文件路徑
                session_file = db_account.session_file
                session_path = Path(session_file)
                
                # 如果是相對路徑，嘗試從項目根目錄解析
                if not session_path.is_absolute():
                    from group_ai_service.config import get_group_ai_config
                    config_obj = get_group_ai_config()
                    api_file_path = Path(__file__).resolve()
                    project_root = api_file_path.parent.parent.parent.parent.parent
                    sessions_dir = project_root / config_obj.session_files_directory
                    session_path = sessions_dir / Path(session_file).name
                    if session_path.exists():
                        session_file = str(session_path)
                    elif Path(session_file).exists():
                        session_file = str(Path(session_file).resolve())
                
                # 創建配置
                account_config = AccountConfig(
                    account_id=db_account.account_id,
                    session_file=session_file,
                    script_id=db_account.script_id or "default",
                    group_ids=db_account.group_ids or [],
                    active=db_account.active if db_account.active is not None else True,
                    reply_rate=db_account.reply_rate or 0.3,
                    redpacket_enabled=db_account.redpacket_enabled if db_account.redpacket_enabled is not None else True,
                    redpacket_probability=db_account.redpacket_probability or 0.5,
                    max_replies_per_hour=db_account.max_replies_per_hour or 50,
                    min_reply_interval=db_account.min_reply_interval or 3
                )
                
                # 添加到 AccountManager
                account = await service_manager.account_manager.add_account(
                    account_id=db_account.account_id,
                    session_file=session_file,
                    config=account_config
                )
                logger.info(f"成功從數據庫加載賬號 {account_id} 到 AccountManager")
            except Exception as e:
                logger.error(f"從數據庫加載賬號 {account_id} 失敗: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"從數據庫加載賬號失敗: {str(e)}。請檢查 session 文件是否存在。"
                )
        
        # 嘗試從數據庫獲取劇本內容
        script_yaml_content = None
        account = service_manager.account_manager.accounts.get(account_id)
        if account and account.config.script_id:
            try:
                script_record = db.query(GroupAIScript).filter(
                    GroupAIScript.script_id == account.config.script_id
                ).first()
                if script_record and script_record.yaml_content:
                    script_yaml_content = script_record.yaml_content
            except Exception as e:
                logger.warning(f"從數據庫獲取劇本失敗: {e}，將嘗試從文件系統加載")
        
        # 嘗試啟動賬號
        success = await service_manager.start_account(account_id, script_yaml_content)
        if not success:
            # 獲取詳細的錯誤信息
            error_details = []
            
            # 檢查賬號是否在 AccountManager 中
            if account_id not in service_manager.account_manager.accounts:
                error_details.append("賬號未在 AccountManager 中")
            
            # 檢查劇本是否可用
            account = service_manager.account_manager.accounts.get(account_id)
            if account:
                script = service_manager.get_script(account.config.script_id, script_yaml_content)
                if not script:
                    error_details.append(f"無法加載劇本: {account.config.script_id}")
                
                # 檢查 session 文件是否存在
                from pathlib import Path
                session_path = Path(account.config.session_file)
                if not session_path.exists():
                    error_details.append(f"Session 文件不存在: {account.config.session_file}")
                
                # 檢查賬號狀態
                if account.status.value == "error":
                    error_details.append("Telegram 連接失敗（請檢查 session 文件是否有效）")
            
            error_msg = f"啟動賬號 {account_id} 失敗"
            if error_details:
                error_msg += f"。詳細信息: {'; '.join(error_details)}"
            else:
                error_msg += "（未知原因，請檢查日誌）"
            
            raise HTTPException(status_code=400, detail=error_msg)
        
        return {"message": f"賬號 {account_id} 已啟動", "account_id": account_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"啟動賬號失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"啟動賬號失敗: {str(e)}")


@router.post("/{account_id}/stop")
async def stop_account(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    manager: AccountManager = Depends(get_account_manager),
    db: Session = Depends(get_db)
):
    """停止賬號（需要 account:stop 權限）"""
    check_permission(current_user, PermissionCode.ACCOUNT_STOP.value, db)
    try:
        # 檢查賬號是否存在
        if account_id not in manager.accounts:
            # 如果 AccountManager 中不存在，檢查數據庫中是否存在
            db_account = db.query(GroupAIAccount).filter(
                GroupAIAccount.account_id == account_id
            ).first()
            
            if not db_account:
                raise HTTPException(status_code=404, detail=f"賬號 {account_id} 不存在")
            
            # 如果賬號在數據庫中存在但不在 AccountManager 中，說明賬號已經是停止狀態
            logger.info(f"賬號 {account_id} 不在 AccountManager 中，可能已經停止")
            return {"message": f"賬號 {account_id} 已經是停止狀態", "account_id": account_id}
        
        success = await manager.stop_account(account_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"停止賬號 {account_id} 失敗")
        return {"message": f"賬號 {account_id} 已停止", "account_id": account_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止賬號失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"停止賬號失敗: {str(e)}")


@router.get("/{account_id}/status", response_model=AccountStatusResponse)
async def get_account_status(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    manager: AccountManager = Depends(get_account_manager),
    db: Session = Depends(get_db)
):
    """獲取賬號狀態（需要 account:view 權限）"""
    check_permission(current_user, PermissionCode.ACCOUNT_VIEW.value, db)
    try:
        status_data = manager.get_account_status(account_id)
        if not status_data:
            raise HTTPException(status_code=404, detail=f"賬號 {account_id} 不存在")
        
        return AccountStatusResponse(
            account_id=status_data.account_id,
            status=status_data.status.value,
            online=status_data.online,
            last_activity=status_data.last_activity.isoformat() if status_data.last_activity else None,
            message_count=status_data.message_count,
            reply_count=status_data.reply_count,
            redpacket_count=status_data.redpacket_count,
            error_count=status_data.error_count,
            last_error=status_data.last_error,
            uptime_seconds=status_data.uptime_seconds
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取賬號狀態失敗: {str(e)}")
