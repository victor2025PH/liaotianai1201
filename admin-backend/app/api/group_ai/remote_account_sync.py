"""
遠端賬號同步模塊

從 Worker 節點同步賬號信息到數據庫
"""
import logging
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime

from app.models.group_ai import GroupAIAccount
from app.db import get_db

logger = logging.getLogger(__name__)


def normalize_account_id(account_id: str) -> str:
    """
    標準化 account_id 格式
    移除常見的前綴，只保留數字部分
    
    例如：
    - "+639454959591" -> "639454959591"
    - "639454959591" -> "639454959591"
    - "@username" -> "@username" (保留用戶名格式)
    """
    if not account_id:
        return account_id
    
    account_id = str(account_id).strip()
    
    # 如果是純數字或帶 + 前綴的數字，標準化為純數字
    if account_id.startswith('+'):
        # 移除 + 前綴
        account_id = account_id[1:]
    
    # 如果是電話號碼格式（主要是數字），移除所有非數字字符
    if re.match(r'^[\d\s\-\+\(\)]+$', account_id):
        account_id = re.sub(r'[^\d]', '', account_id)
    
    return account_id


def find_existing_account(
    db: Session,
    account_id: str,
    phone_number: Optional[str] = None,
    user_id: Optional[int] = None
) -> Optional[GroupAIAccount]:
    """
    查找現有賬號，使用多種匹配條件
    
    優先順序：
    1. 精確匹配 account_id
    2. 標準化後匹配 account_id
    3. 匹配 phone_number
    4. 匹配 user_id（Telegram User ID）
    """
    normalized_id = normalize_account_id(account_id)
    
    # 1. 首先嘗試精確匹配
    db_account = db.query(GroupAIAccount).filter(
        GroupAIAccount.account_id == account_id
    ).first()
    
    if db_account:
        logger.debug(f"精確匹配找到賬號: {account_id}")
        return db_account
    
    # 2. 嘗試標準化後匹配
    if normalized_id != account_id:
        db_account = db.query(GroupAIAccount).filter(
            GroupAIAccount.account_id == normalized_id
        ).first()
        if db_account:
            logger.debug(f"標準化匹配找到賬號: {normalized_id} (原始: {account_id})")
            return db_account
    
    # 3. 嘗試匹配 phone_number
    if phone_number:
        normalized_phone = normalize_account_id(phone_number)
        db_account = db.query(GroupAIAccount).filter(
            or_(
                GroupAIAccount.phone_number == phone_number,
                GroupAIAccount.phone_number == normalized_phone,
                GroupAIAccount.account_id == normalized_phone
            )
        ).first()
        if db_account:
            logger.debug(f"手機號匹配找到賬號: {phone_number}")
            return db_account
    
    # 4. 嘗試匹配 user_id
    if user_id:
        db_account = db.query(GroupAIAccount).filter(
            GroupAIAccount.user_id == user_id
        ).first()
        if db_account:
            logger.debug(f"User ID 匹配找到賬號: {user_id}")
            return db_account
    
    # 5. 最後嘗試模糊匹配（account_id 包含關係）
    # 例如：數據庫中是 "639454959591"，Worker 傳來的是 "+639454959591"
    all_accounts = db.query(GroupAIAccount).all()
    for acc in all_accounts:
        acc_normalized = normalize_account_id(acc.account_id)
        if acc_normalized == normalized_id:
            logger.debug(f"模糊匹配找到賬號: {acc.account_id} (搜索: {account_id})")
            return acc
    
    return None


def sync_accounts_from_worker(
    node_id: str,
    accounts: List[Dict[str, Any]],
    db: Session
) -> Dict[str, Any]:
    """
    從 Worker 節點同步賬號到數據庫
    
    Args:
        node_id: Worker 節點 ID
        accounts: 賬號列表（從 Worker 心跳獲取）
        db: 數據庫會話
        
    Returns:
        同步結果統計
    """
    synced_count = 0
    updated_count = 0
    created_count = 0
    skipped_count = 0
    errors = []
    
    logger.info(f"開始同步節點 {node_id} 的 {len(accounts)} 個賬號")
    
    for account_data in accounts:
        try:
            account_id = account_data.get('account_id')
            if not account_id:
                errors.append("賬號數據缺少 account_id")
                continue
            
            # 標準化 account_id
            original_account_id = account_id
            account_id = normalize_account_id(account_id)
            
            logger.debug(f"處理賬號: {original_account_id} -> {account_id}")
            
            # 使用增強的查找邏輯
            db_account = find_existing_account(
                db=db,
                account_id=account_id,
                phone_number=account_data.get('phone_number'),
                user_id=account_data.get('user_id')
            )
            
            if db_account:
                # 找到現有賬號 - 只更新運行狀態，不覆蓋用戶手動配置
                logger.info(f"找到現有賬號 {db_account.account_id}，進行狀態更新")
                
                # 更新在線狀態
                if 'status' in account_data:
                    # 狀態映射：online -> active=True, offline -> active=False
                    db_account.active = (account_data.get('status') == 'online')
                
                # 更新統計信息（存儲在 config 字段中）
                if not db_account.config:
                    db_account.config = {}
                
                # 合併 config，保留現有配置
                config_updates = {}
                if 'message_count' in account_data:
                    config_updates['message_count'] = account_data.get('message_count', 0)
                if 'reply_count' in account_data:
                    config_updates['reply_count'] = account_data.get('reply_count', 0)
                if 'last_activity' in account_data:
                    config_updates['last_activity'] = account_data.get('last_activity')
                
                # 保留 node_id 和來源信息
                config_updates['node_id'] = node_id
                config_updates['last_sync'] = datetime.now().isoformat()
                
                # 合併配置（不覆蓋用戶手動設置的其他配置）
                db_account.config = {**db_account.config, **config_updates}
                
                # 【重要】不要覆蓋用戶在後台設置的 script_id
                # 只在以下情況更新 script_id：
                # 1. 數據庫中的 script_id 是空的或是 "default"
                # 2. 並且 Worker 提供了有效的 script_id
                worker_script_id = account_data.get('script_id')
                if worker_script_id and worker_script_id != 'default':
                    # Worker 有具體的劇本分配
                    if not db_account.script_id or db_account.script_id == 'default':
                        db_account.script_id = worker_script_id
                        logger.info(f"更新賬號 {db_account.account_id} 的劇本為 {worker_script_id}")
                
                # 更新 server_id（確保賬號關聯到正確的節點）
                if db_account.server_id != node_id:
                    logger.info(f"賬號 {db_account.account_id} 從節點 {db_account.server_id} 移動到 {node_id}")
                    db_account.server_id = node_id
                
                # 更新手機號和用戶信息（如果提供且數據庫中為空）
                if account_data.get('phone_number') and not db_account.phone_number:
                    db_account.phone_number = account_data.get('phone_number')
                if account_data.get('user_id') and not db_account.user_id:
                    db_account.user_id = account_data.get('user_id')
                if account_data.get('username') and not db_account.username:
                    db_account.username = account_data.get('username')
                if account_data.get('first_name') and not db_account.first_name:
                    db_account.first_name = account_data.get('first_name')
                if account_data.get('last_name') and not db_account.last_name:
                    db_account.last_name = account_data.get('last_name')
                
                db_account.updated_at = datetime.now()
                updated_count += 1
                
            else:
                # 沒有找到現有賬號 - 創建新記錄
                # 使用標準化的 account_id
                logger.info(f"創建新賬號記錄: {account_id} (來自節點 {node_id})")
                
                new_account = GroupAIAccount(
                    account_id=account_id,  # 使用標準化後的 ID
                    server_id=node_id,
                    session_file=account_data.get('session_file', f'{account_id}.session'),
                    script_id=account_data.get('script_id') or 'default',
                    group_ids=account_data.get('group_ids', []),
                    active=account_data.get('status') == 'online',
                    phone_number=account_data.get('phone_number'),
                    username=account_data.get('username'),
                    first_name=account_data.get('first_name'),
                    last_name=account_data.get('last_name'),
                    user_id=account_data.get('user_id'),
                    config={
                        'message_count': account_data.get('message_count', 0),
                        'reply_count': account_data.get('reply_count', 0),
                        'last_activity': account_data.get('last_activity'),
                        'node_id': node_id,
                        'source': 'worker',  # 標記來源為 Worker 節點
                        'created_from_heartbeat': True,
                        'original_account_id': original_account_id,  # 保存原始 ID
                        'created_at': datetime.now().isoformat()
                    }
                )
                db.add(new_account)
                created_count += 1
            
            synced_count += 1
            
        except Exception as e:
            error_msg = f"同步賬號 {account_data.get('account_id', 'unknown')} 失敗: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
    
    try:
        db.commit()
        logger.info(
            f"從節點 {node_id} 同步完成: "
            f"總計 {synced_count} 個賬號（新建: {created_count}, 更新: {updated_count}, 跳過: {skipped_count}）"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"提交賬號同步失敗: {e}", exc_info=True)
        raise
    
    return {
        'synced_count': synced_count,
        'created_count': created_count,
        'updated_count': updated_count,
        'skipped_count': skipped_count,
        'errors': errors
    }
