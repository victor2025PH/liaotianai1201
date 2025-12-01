"""
Telegram 賬號批量導入 API

支持從 TXT 或 Excel 文件批量導入 Telegram 賬號配置。
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel
import sys
import logging
from pathlib import Path
import tempfile
import csv

logger = logging.getLogger(__name__)

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import openpyxl
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False
    logger.warning("openpyxl 未安裝，不支持 Excel 文件")

from sqlalchemy.orm import Session
from app.db import get_db
from app.models.group_ai import GroupAIAccount
from app.api.deps import get_current_active_user
from app.middleware.permission import check_permission
from app.core.permissions import PermissionCode
from app.models.user import User

router = APIRouter()


class ImportResult(BaseModel):
    """導入結果"""
    total: int
    success: int
    failed: int
    errors: List[str] = []


class AccountImportItem(BaseModel):
    """單個賬號導入項"""
    api_id: str
    api_hash: str
    session_name: str


def parse_txt_content(content: str) -> List[AccountImportItem]:
    """解析 TXT 文件內容"""
    accounts = []
    for line_num, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # 支持 | 或 , 分隔符
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
        elif ',' in line:
            parts = [p.strip() for p in line.split(',')]
        else:
            raise ValueError(f"第 {line_num} 行格式錯誤：需要使用 | 或 , 分隔符")
        
        if len(parts) != 3:
            raise ValueError(f"第 {line_num} 行格式錯誤：需要 3 個字段（API_ID, API_HASH, SESSION_NAME）")
        
        accounts.append(AccountImportItem(
            api_id=parts[0],
            api_hash=parts[1],
            session_name=parts[2]
        ))
    
    return accounts


def parse_excel_content(file_path: Path) -> List[AccountImportItem]:
    """解析 Excel 文件內容"""
    if not EXCEL_SUPPORT:
        raise HTTPException(
            status_code=400,
            detail="Excel 文件支持需要安裝 openpyxl: pip install openpyxl"
        )
    
    accounts = []
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active
    
    # 讀取表頭
    headers = [str(cell.value).strip() if cell.value else "" for cell in sheet[1]]
    
    # 查找列索引（不區分大小寫）
    api_id_idx = None
    api_hash_idx = None
    session_name_idx = None
    
    for idx, header in enumerate(headers):
        header_lower = header.lower()
        if 'api_id' in header_lower or 'apiid' in header_lower:
            api_id_idx = idx
        elif 'api_hash' in header_lower or 'apihash' in header_lower:
            api_hash_idx = idx
        elif 'session_name' in header_lower or 'sessionname' in header_lower or 'phone' in header_lower:
            session_name_idx = idx
    
    if api_id_idx is None or api_hash_idx is None or session_name_idx is None:
        raise HTTPException(
            status_code=400,
            detail="Excel 文件缺少必需的列：需要 API_ID, API_HASH, SESSION_NAME"
        )
    
    # 讀取數據
    for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
        if not any(row):  # 跳過空行
            continue
        
        api_id = str(row[api_id_idx]).strip() if row[api_id_idx] else None
        api_hash = str(row[api_hash_idx]).strip() if row[api_hash_idx] else None
        session_name = str(row[session_name_idx]).strip() if row[session_name_idx] else None
        
        if not all([api_id, api_hash, session_name]):
            continue
        
        accounts.append(AccountImportItem(
            api_id=api_id,
            api_hash=api_hash,
            session_name=session_name
        ))
    
    return accounts


def save_accounts_to_db(accounts: List[AccountImportItem], db: Session) -> ImportResult:
    """將賬號配置保存到數據庫"""
    result = ImportResult(total=len(accounts), success=0, failed=0, errors=[])
    
    for account_data in accounts:
        try:
            # 檢查是否已存在（根據 session_name 或 account_id）
            existing = db.query(GroupAIAccount).filter(
                (GroupAIAccount.account_id == account_data.session_name) |
                (GroupAIAccount.phone_number == account_data.session_name)
            ).first()
            
            if existing:
                # 更新現有賬號的配置
                if not existing.config:
                    existing.config = {}
                existing.config['telegram_api_id'] = account_data.api_id
                existing.config['telegram_api_hash'] = account_data.api_hash
                existing.config['telegram_session_name'] = account_data.session_name
                result.success += 1
                logger.info(f"更新賬號配置: {account_data.session_name}")
            else:
                # 創建新賬號記錄（僅配置，不啟動）
                new_account = GroupAIAccount(
                    account_id=account_data.session_name,
                    phone_number=account_data.session_name,
                    name=account_data.session_name,
                    active=False,
                    config={
                        'telegram_api_id': account_data.api_id,
                        'telegram_api_hash': account_data.api_hash,
                        'telegram_session_name': account_data.session_name
                    }
                )
                db.add(new_account)
                result.success += 1
                logger.info(f"創建新賬號配置: {account_data.session_name}")
        
        except Exception as e:
            result.failed += 1
            error_msg = f"賬號 {account_data.session_name}: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg, exc_info=True)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存到數據庫失敗: {str(e)}")
    
    return result


@router.post("/import", response_model=ImportResult)
async def import_telegram_accounts(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    批量導入 Telegram 賬號配置
    
    支持格式：
    - TXT 文件：每行格式 `API_ID|API_HASH|SESSION_NAME` 或 `API_ID,API_HASH,SESSION_NAME`
    - Excel 文件：包含列 `API_ID`, `API_HASH`, `SESSION_NAME`
    
    需要權限：account:create
    """
    check_permission(current_user, PermissionCode.ACCOUNT_CREATE.value, db)
    
    # 檢查文件類型
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    
    if file_ext not in ['.txt', '.csv', '.xlsx', '.xls']:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}。支持格式: .txt, .csv, .xlsx, .xls"
        )
    
    # 讀取文件內容
    content = await file.read()
    
    try:
        # 解析文件
        if file_ext in ['.xlsx', '.xls']:
            # Excel 文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                tmp_file.write(content)
                tmp_path = Path(tmp_file.name)
            
            try:
                accounts = parse_excel_content(tmp_path)
            finally:
                tmp_path.unlink()  # 刪除臨時文件
        else:
            # TXT/CSV 文件
            content_str = content.decode('utf-8')
            accounts = parse_txt_content(content_str)
        
        if not accounts:
            raise HTTPException(status_code=400, detail="文件中未找到有效的賬號配置")
        
        # 保存到數據庫
        result = save_accounts_to_db(accounts, db)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"導入失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"導入失敗: {str(e)}")


@router.post("/import/batch", response_model=ImportResult)
async def import_telegram_accounts_batch(
    accounts: List[AccountImportItem],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    批量導入 Telegram 賬號配置（JSON 格式）
    
    需要權限：account:create
    """
    check_permission(current_user, PermissionCode.ACCOUNT_CREATE.value, db)
    
    if not accounts:
        raise HTTPException(status_code=400, detail="賬號列表為空")
    
    result = save_accounts_to_db(accounts, db)
    
    return result
