"""
AccountManager 快速測試腳本（無需真實 session 文件）

這個腳本只測試不涉及實際 Telegram 連接的功能
"""
import asyncio
import sys
import io
from pathlib import Path

# 設置 UTF-8 編碼（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from group_ai_service import AccountManager
from group_ai_service.models.account import AccountConfig


async def quick_test():
    """快速測試（無需真實連接）"""
    print("="*60)
    print("AccountManager 快速測試（無需真實 session）")
    print("="*60)
    
    # 1. 創建管理器
    print("\n[1] 創建 AccountManager...")
    manager = AccountManager()
    print("[OK] AccountManager 創建成功")
    
    # 2. 列出賬號（應該為空）
    print("\n[2] 列出所有賬號...")
    accounts = manager.list_accounts()
    print(f"[OK] 當前賬號數量: {len(accounts)}")
    
    # 3. 獲取不存在的賬號狀態
    print("\n[3] 獲取不存在的賬號狀態...")
    status = manager.get_account_status("non_existent")
    if status is None:
        print("[OK] 正確返回 None（賬號不存在）")
    else:
        print("[FAIL] 應該返回 None")
    
    # 4. 測試添加賬號（使用不存在的 session 文件，應該失敗）
    print("\n[4] 嘗試添加不存在的 session 文件...")
    try:
        config = AccountConfig(
            account_id="test_account",
            session_file="non_existent.session",
            script_id="test",
            group_ids=[]
        )
        await manager.add_account("test_account", "non_existent.session", config)
        print("[FAIL] 應該拋出 FileNotFoundError")
    except FileNotFoundError:
        print("[OK] 正確捕獲 FileNotFoundError")
    except Exception as e:
        print(f"[FAIL] 意外的錯誤: {e}")
    
    # 5. 測試配置
    print("\n[5] 檢查配置...")
    config = manager.config
    print(f"[OK] 最大賬號數: {config.max_accounts}")
    print(f"[OK] 默認回復頻率: {config.default_reply_rate}")
    print(f"[OK] 健康檢查間隔: {config.account_health_check_interval} 秒")
    
    print("\n" + "="*60)
    print("快速測試完成！")
    print("="*60)
    print("\n如需測試完整功能（包括啟動賬號），請運行:")
    print("  python scripts/test_account_manager.py")


if __name__ == "__main__":
    asyncio.run(quick_test())

