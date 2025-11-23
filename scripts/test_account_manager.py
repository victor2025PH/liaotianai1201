"""
AccountManager 手動測試腳本

使用方法:
    python scripts/test_account_manager.py

注意事項:
    1. 確保已配置環境變量或 config.py 中的 Telegram API 憑證
    2. 準備測試用的 .session 文件（放在 sessions/ 目錄下）
    3. 確保數據庫已初始化
"""
import asyncio
import sys
import os
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


# 顏色輸出（Windows 兼容）
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
    
    # 測試 1.1: 列出賬號（應該為空）
    print("\n[1.1] 列出所有賬號（初始狀態）")
    accounts = manager.list_accounts()
    print(f"  當前賬號數量: {len(accounts)}")
    if len(accounts) == 0:
        Colors.print_success("初始狀態正確（無賬號）")
    else:
        Colors.print_warning(f"發現 {len(accounts)} 個已存在的賬號")
    
    # 測試 1.2: 獲取不存在的賬號狀態
    print("\n[1.2] 獲取不存在的賬號狀態")
    status = manager.get_account_status("non_existent_account")
    if status is None:
        Colors.print_success("正確返回 None（賬號不存在）")
    else:
        Colors.print_error("應該返回 None")
    
    return manager


async def test_add_account(manager: AccountManager):
    """測試添加賬號"""
    print("\n" + "="*60)
    print("測試 2: 添加賬號測試")
    print("="*60)
    
    # 檢查是否有測試用的 session 文件
    sessions_dir = Path("sessions")
    session_files = list(sessions_dir.glob("*.session")) if sessions_dir.exists() else []
    
    if not session_files:
        Colors.print_warning("未找到 .session 文件，跳過添加賬號測試")
        Colors.print_info("提示: 將 .session 文件放在 sessions/ 目錄下以進行測試")
        return None
    
    # 使用第一個找到的 session 文件
    test_session = session_files[0]
    test_account_id = test_session.stem
    
    print(f"\n[2.1] 添加賬號: {test_account_id}")
    print(f"  Session 文件: {test_session}")
    
    try:
        config = AccountConfig(
            account_id=test_account_id,
            session_file=str(test_session),
            script_id="test_script",
            group_ids=[123456789],  # 測試群組 ID
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
        print(f"  監聽群組: {account.config.group_ids}")
        
        return test_account_id
        
    except FileNotFoundError as e:
        Colors.print_error(f"Session 文件不存在: {e}")
        return None
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
        print(f"    消息數: {account.message_count}")
        print(f"    回復數: {account.reply_count}")
    
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
        print(f"  紅包數: {status.redpacket_count}")
        print(f"  錯誤數: {status.error_count}")
        print(f"  運行時間: {status.uptime_seconds} 秒")
        if status.last_activity:
            print(f"  最後活動: {status.last_activity}")
    else:
        Colors.print_error("狀態獲取失敗")


async def test_start_stop_account(manager: AccountManager, account_id: str):
    """測試啟動和停止賬號"""
    print("\n" + "="*60)
    print("測試 5: 啟動/停止賬號測試")
    print("="*60)
    
    if not account_id:
        Colors.print_warning("沒有可用賬號，跳過啟動/停止測試")
        return
    
    # 測試啟動（需要真實的 Telegram 憑證）
    print(f"\n[5.1] 啟動賬號: {account_id}")
    Colors.print_warning("注意: 這需要有效的 Telegram API 憑證和 session 文件")
    
    user_input = input("  是否嘗試啟動賬號？(y/N): ").strip().lower()
    if user_input != 'y':
        Colors.print_info("跳過啟動測試（需要用戶確認）")
        return
    
    try:
        success = await manager.start_account(account_id)
        if success:
            Colors.print_success("賬號啟動成功")
            
            # 等待一下，然後檢查狀態
            await asyncio.sleep(2)
            status = manager.get_account_status(account_id)
            if status:
                print(f"  當前狀態: {status.status.value}")
                print(f"  在線: {status.online}")
            
            # 測試停止
            print(f"\n[5.2] 停止賬號: {account_id}")
            user_input = input("  是否停止賬號？(y/N): ").strip().lower()
            if user_input == 'y':
                success = await manager.stop_account(account_id)
                if success:
                    Colors.print_success("賬號停止成功")
                else:
                    Colors.print_error("賬號停止失敗")
        else:
            Colors.print_error("賬號啟動失敗（可能是憑證問題或 session 無效）")
            Colors.print_info("提示: 檢查 Telegram API 憑證和 session 文件是否有效")
    
    except Exception as e:
        Colors.print_error(f"啟動賬號時發生錯誤: {e}")
        import traceback
        traceback.print_exc()


async def test_batch_load(manager: AccountManager):
    """測試批量加載"""
    print("\n" + "="*60)
    print("測試 6: 批量加載測試")
    print("="*60)
    
    sessions_dir = Path("sessions")
    if not sessions_dir.exists():
        Colors.print_warning("sessions/ 目錄不存在，跳過批量加載測試")
        Colors.print_info("提示: 創建 sessions/ 目錄並放入 .session 文件")
        return
    
    session_files = list(sessions_dir.glob("*.session"))
    if not session_files:
        Colors.print_warning("sessions/ 目錄中沒有 .session 文件")
        return
    
    print(f"\n[6.1] 從目錄批量加載（找到 {len(session_files)} 個文件）")
    Colors.print_info("注意: 這會嘗試加載所有 .session 文件")
    
    user_input = input("  是否繼續？(y/N): ").strip().lower()
    if user_input != 'y':
        Colors.print_info("跳過批量加載測試")
        return
    
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


async def test_remove_account(manager: AccountManager, account_id: str):
    """測試移除賬號"""
    print("\n" + "="*60)
    print("測試 7: 移除賬號測試")
    print("="*60)
    
    if not account_id:
        Colors.print_warning("沒有可用賬號，跳過移除測試")
        return
    
    print(f"\n[7.1] 移除賬號: {account_id}")
    user_input = input("  是否移除測試賬號？(y/N): ").strip().lower()
    if user_input != 'y':
        Colors.print_info("跳過移除測試")
        return
    
    try:
        success = await manager.remove_account(account_id)
        if success:
            Colors.print_success("賬號移除成功")
            
            # 驗證已移除
            status = manager.get_account_status(account_id)
            if status is None:
                Colors.print_success("驗證: 賬號已從列表中移除")
            else:
                Colors.print_error("驗證失敗: 賬號仍在列表中")
        else:
            Colors.print_error("賬號移除失敗")
    
    except Exception as e:
        Colors.print_error(f"移除賬號時發生錯誤: {e}")


async def main():
    """主測試流程"""
    print("\n" + "="*60)
    print("AccountManager 手動測試")
    print("="*60)
    print("\n此腳本將測試 AccountManager 的各項功能")
    print("請確保已配置 Telegram API 憑證\n")
    
    # 檢查環境
    try:
        from config import API_ID, API_HASH
        Colors.print_success(f"找到 Telegram API 憑證 (API_ID: {API_ID})")
    except ImportError:
        Colors.print_error("未找到 config.py 或 API 憑證未配置")
        Colors.print_info("請確保 config.py 存在並配置了 TELEGRAM_API_ID 和 TELEGRAM_API_HASH")
        return
    except Exception as e:
        Colors.print_warning(f"讀取配置時出現問題: {e}")
    
    # 執行測試
    manager = await test_basic_operations()
    
    account_id = await test_add_account(manager)
    
    await test_list_accounts(manager)
    
    if account_id:
        await test_get_status(manager, account_id)
        await test_start_stop_account(manager, account_id)
    
    await test_batch_load(manager)
    
    # 最後詢問是否移除測試賬號
    if account_id:
        await test_remove_account(manager, account_id)
    
    print("\n" + "="*60)
    print("測試完成")
    print("="*60)
    print("\n提示:")
    print("  - 如果某些測試失敗，請檢查:")
    print("    1. Telegram API 憑證是否正確")
    print("    2. Session 文件是否有效")
    print("    3. 網絡連接是否正常")
    print("    4. 是否有足夠的權限")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n測試已中斷")
    except Exception as e:
        print(f"\n\n測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

