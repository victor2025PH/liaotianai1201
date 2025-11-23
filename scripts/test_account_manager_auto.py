"""
AccountManager 自動化測試腳本（無需用戶輸入）

這個腳本會自動執行所有測試，不需要交互式輸入
適合 CI/CD 或自動化測試環境
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


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    
    @staticmethod
    def print_success(msg):
        print(f"{Colors.GREEN}[OK] {msg}{Colors.RESET}")
    
    @staticmethod
    def print_warning(msg):
        print(f"{Colors.YELLOW}[WARN] {msg}{Colors.RESET}")
    
    @staticmethod
    def print_error(msg):
        print(f"{Colors.RED}[FAIL] {msg}{Colors.RESET}")
    
    @staticmethod
    def print_info(msg):
        print(f"{Colors.BLUE}[INFO] {msg}{Colors.RESET}")


async def test_basic_operations():
    """測試基本操作"""
    print("\n" + "="*60)
    print("測試 1: 基本操作測試")
    print("="*60)
    
    manager = AccountManager()
    Colors.print_info("AccountManager 已創建")
    
    accounts = manager.list_accounts()
    print(f"\n[1.1] 當前賬號數量: {len(accounts)}")
    if len(accounts) == 0:
        Colors.print_success("初始狀態正確（無賬號）")
    
    status = manager.get_account_status("non_existent")
    if status is None:
        Colors.print_success("正確返回 None（賬號不存在）")
    
    return manager


async def test_add_account(manager: AccountManager):
    """測試添加賬號"""
    print("\n" + "="*60)
    print("測試 2: 添加賬號測試")
    print("="*60)
    
    sessions_dir = Path("sessions")
    session_files = list(sessions_dir.glob("*.session")) if sessions_dir.exists() else []
    
    if not session_files:
        Colors.print_warning("未找到 .session 文件，跳過添加賬號測試")
        return None
    
    test_session = session_files[0]
    test_account_id = test_session.stem
    
    print(f"\n[2.1] 添加賬號: {test_account_id}")
    print(f"  Session 文件: {test_session}")
    
    try:
        config = AccountConfig(
            account_id=test_account_id,
            session_file=str(test_session),
            script_id="test_script",
            group_ids=[123456789],
            active=True
        )
        
        account = await manager.add_account(
            account_id=test_account_id,
            session_file=str(test_session),
            config=config
        )
        
        Colors.print_success(f"賬號 {test_account_id} 添加成功")
        print(f"  賬號 ID: {account.account_id}")
        print(f"  狀態: {account.status.value}")
        print(f"  劇本 ID: {account.config.script_id}")
        
        return test_account_id
        
    except Exception as e:
        Colors.print_error(f"添加賬號失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_list_accounts(manager: AccountManager):
    """測試列出賬號"""
    print("\n" + "="*60)
    print("測試 3: 列出賬號測試")
    print("="*60)
    
    accounts = manager.list_accounts()
    print(f"\n[3.1] 當前賬號列表（共 {len(accounts)} 個）")
    
    if len(accounts) == 0:
        Colors.print_warning("沒有賬號")
        return
    
    for i, account in enumerate(accounts, 1):
        print(f"\n  賬號 {i}:")
        print(f"    ID: {account.account_id}")
        print(f"    Session: {account.session_file}")
        print(f"    劇本: {account.script_id}")
        print(f"    狀態: {account.status.value}")
        print(f"    群組數: {account.group_count}")
    
    Colors.print_success("賬號列表獲取成功")


async def test_get_status(manager: AccountManager, account_id: str):
    """測試獲取賬號狀態"""
    print("\n" + "="*60)
    print("測試 4: 獲取賬號狀態測試")
    print("="*60)
    
    if not account_id:
        Colors.print_warning("沒有可用賬號，跳過狀態測試")
        return
    
    print(f"\n[4.1] 獲取賬號狀態: {account_id}")
    status = manager.get_account_status(account_id)
    
    if status:
        Colors.print_success("狀態獲取成功")
        print(f"  賬號 ID: {status.account_id}")
        print(f"  狀態: {status.status.value}")
        print(f"  在線: {status.online}")
        print(f"  消息數: {status.message_count}")
        print(f"  回復數: {status.reply_count}")
    else:
        Colors.print_error("狀態獲取失敗")


async def test_batch_load(manager: AccountManager):
    """測試批量加載"""
    print("\n" + "="*60)
    print("測試 5: 批量加載測試")
    print("="*60)
    
    sessions_dir = Path("sessions")
    if not sessions_dir.exists():
        Colors.print_warning("sessions/ 目錄不存在，跳過批量加載測試")
        return
    
    session_files = list(sessions_dir.glob("*.session"))
    if not session_files:
        Colors.print_warning("sessions/ 目錄中沒有 .session 文件")
        return
    
    print(f"\n[5.1] 從目錄批量加載（找到 {len(session_files)} 個文件）")
    
    try:
        loaded = await manager.load_accounts_from_directory(
            directory="sessions",
            script_id="batch_test",
            group_ids=[123456789]
        )
        
        Colors.print_success(f"批量加載完成，成功加載 {len(loaded)} 個賬號")
        if loaded:
            print("  已加載的賬號:")
            for account_id in loaded:
                print(f"    - {account_id}")
    
    except Exception as e:
        Colors.print_error(f"批量加載失敗: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主測試流程"""
    print("\n" + "="*60)
    print("AccountManager 自動化測試")
    print("="*60)
    print("\n此腳本將自動執行所有測試（無需用戶輸入）\n")
    
    # 檢查環境
    try:
        from config import API_ID, API_HASH
        Colors.print_success(f"找到 Telegram API 憑證 (API_ID: {API_ID})")
    except Exception as e:
        Colors.print_warning(f"讀取配置時出現問題: {e}")
    
    # 執行測試
    manager = await test_basic_operations()
    account_id = await test_add_account(manager)
    await test_list_accounts(manager)
    
    if account_id:
        await test_get_status(manager, account_id)
    
    await test_batch_load(manager)
    
    print("\n" + "="*60)
    print("測試完成")
    print("="*60)
    print("\n提示:")
    print("  - 如需測試啟動/停止功能，請運行: py scripts/test_account_manager.py")
    print("  - 該腳本需要交互式輸入來確認啟動賬號")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n測試已中斷")
    except Exception as e:
        print(f"\n\n測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

