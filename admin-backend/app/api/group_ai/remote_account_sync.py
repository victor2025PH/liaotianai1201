"""
遠端賬號同步模塊

從 Worker 節點同步賬號信息到數據庫
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.group_ai import GroupAIAccount
from app.db import get_db

logger = logging.getLogger(__name__)


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
    errors = []
    
    for account_data in accounts:
        try:
            account_id = account_data.get('account_id')
            if not account_id:
                errors.append("賬號數據缺少 account_id")
                continue
            
            # 檢查賬號是否存在
            db_account = db.query(GroupAIAccount).filter(
                GroupAIAccount.account_id == account_id
            ).first()
            
            if db_account:
                # 更新現有賬號
                # 更新狀態信息
                if 'status' in account_data:
                    # 狀態映射：online -> active=True, offline -> active=False
                    db_account.active = (account_data.get('status') == 'online')
                
                # 更新統計信息
                if 'message_count' in account_data:
                    # 可以存儲在 config 字段中
                    if not db_account.config:
                        db_account.config = {}
                    db_account.config['message_count'] = account_data.get('message_count', 0)
                    db_account.config['reply_count'] = account_data.get('reply_count', 0)
                    db_account.config['last_activity'] = account_data.get('last_activity')
                
                # 更新劇本 ID（如果提供）
                if 'script_id' in account_data:
                    db_account.script_id = account_data.get('script_id')
                
                # 確保 server_id 正確
                if db_account.server_id != node_id:
                    db_account.server_id = node_id
                
                db_account.updated_at = datetime.now()
                updated_count += 1
            else:
                # 創建新賬號記錄
                new_account = GroupAIAccount(
                    account_id=account_id,
                    server_id=node_id,
                    session_file=account_data.get('session_file', f'{account_id}.session'),
                    script_id=account_data.get('script_id', 'default'),
                    group_ids=account_data.get('group_ids', []),
                    active=account_data.get('status') == 'online',
                    config={
                        'message_count': account_data.get('message_count', 0),
                        'reply_count': account_data.get('reply_count', 0),
                        'last_activity': account_data.get('last_activity'),
                        'node_id': node_id,
                        'source': 'worker'  # 標記來源為 Worker 節點
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
        logger.info(f"從節點 {node_id} 同步了 {synced_count} 個賬號（新建: {created_count}, 更新: {updated_count}）")
    except Exception as e:
        db.rollback()
        logger.error(f"提交賬號同步失敗: {e}", exc_info=True)
        raise
    
    return {
        'synced_count': synced_count,
        'created_count': created_count,
        'updated_count': updated_count,
        'errors': errors
    }
