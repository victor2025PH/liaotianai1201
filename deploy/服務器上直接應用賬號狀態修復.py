#!/usr/bin/env python3
"""
在服務器上直接應用賬號狀態端點修復
修復 get_account_status 函數，添加數據庫檢查
"""

import re
import sys
from pathlib import Path

# 修復後的完整函數代碼
FIXED_FUNCTION = '''@router.get("/{account_id}/status", response_model=AccountStatusResponse)
async def get_account_status(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    manager: AccountManager = Depends(get_account_manager),
    db: Session = Depends(get_db)
):
    """獲取賬號狀態（需要 account:view 權限）"""
    check_permission(current_user, PermissionCode.ACCOUNT_VIEW.value, db)
    try:
        # 1. 先檢查 AccountManager（在內存中運行的賬號）
        status_data = manager.get_account_status(account_id)
        if status_data:
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
        
        # 2. 檢查數據庫（包含遠程服務器賬號）
        db_account = db.query(GroupAIAccount).filter(
            GroupAIAccount.account_id == account_id
        ).first()
        
        if db_account:
            # 賬號在數據庫中但不在 AccountManager 中，返回默認的 offline 狀態
            from group_ai_service.models.account import AccountStatusEnum
            return AccountStatusResponse(
                account_id=account_id,
                status=AccountStatusEnum.OFFLINE.value,
                online=False,
                last_activity=None,
                message_count=0,
                reply_count=0,
                redpacket_count=0,
                error_count=0,
                last_error=None,
                uptime_seconds=0
            )
        
        # 3. 都不存在，返回 404
        raise HTTPException(status_code=404, detail=f"賬號 {account_id} 不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"獲取賬號狀態失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"獲取賬號狀態失敗: {str(e)}")'''


def apply_fix(file_path: Path):
    """應用修復"""
    # 讀取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 備份原文件
    backup_path = file_path.with_suffix('.py.bak')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 已備份原文件: {backup_path}")
    
    # 找到要替換的函數範圍
    # 匹配從 @router.get 開始到函數結束（下一個 @ 或 class 或 def 或文件結尾）
    pattern = r'@router\.get\("/{account_id}/status".*?)(?=\n@|\nclass |\ndef |\Z)'
    
    if re.search(pattern, content, re.DOTALL):
        # 替換函數
        new_content = re.sub(pattern, FIXED_FUNCTION + '\n\n', content, flags=re.DOTALL)
        
        # 寫回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 修復已應用: {file_path}")
        return True
    else:
        print(f"❌ 未找到要修復的函數")
        return False


def main():
    # 默認文件路徑
    default_path = Path('/home/ubuntu/liaotian/deployment-package/admin-backend/app/api/group_ai/accounts.py')
    
    # 如果提供命令行參數，使用參數
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        file_path = default_path
    
    # 檢查文件是否存在
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        print(f"使用方式: python3 {sys.argv[0]} <文件路徑>")
        sys.exit(1)
    
    print(f"處理文件: {file_path}")
    
    # 應用修復
    if apply_fix(file_path):
        print("\n✅ 修復完成！")
        print("請重啟後端服務以應用修復。")
    else:
        print("\n❌ 修復失敗")
        sys.exit(1)


if __name__ == '__main__':
    main()
