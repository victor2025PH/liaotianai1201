"""
診斷帳號 API 問題的腳本
"""
import sys
from pathlib import Path

# 添加項目路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_service_manager():
    """測試 ServiceManager 初始化"""
    print("="*60)
    print("測試 ServiceManager 初始化")
    print("="*60)
    
    try:
        from group_ai_service.service_manager import ServiceManager
        print("[OK] ServiceManager 導入成功")
        
        print("\n初始化 ServiceManager...")
        sm = ServiceManager()
        print("[OK] ServiceManager 初始化成功")
        
        print("\n測試 AccountManager...")
        am = sm.account_manager
        print("[OK] AccountManager 獲取成功")
        
        print("\n測試 list_accounts()...")
        accounts = am.list_accounts()
        print(f"[OK] list_accounts() 成功，返回 {len(accounts)} 個帳號")
        
        if accounts:
            print("\n帳號列表:")
            for acc in accounts:
                print(f"  - {acc.account_id}: {acc.status}")
        else:
            print("\n[WARN] 沒有帳號（這是正常的，如果還沒有添加帳號）")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dialogue_manager():
    """測試 DialogueManager 初始化"""
    print("\n" + "="*60)
    print("測試 DialogueManager 初始化")
    print("="*60)
    
    try:
        from group_ai_service.dialogue_manager import DialogueManager
        print("[OK] DialogueManager 導入成功")
        
        print("\n初始化 DialogueManager...")
        dm = DialogueManager()
        print("[OK] DialogueManager 初始化成功")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("\n開始診斷帳號 API 問題...\n")
    
    # 測試 DialogueManager
    dm_ok = test_dialogue_manager()
    
    # 測試 ServiceManager
    sm_ok = test_service_manager()
    
    print("\n" + "="*60)
    print("診斷結果")
    print("="*60)
    
    if dm_ok and sm_ok:
        print("[OK] 所有組件初始化正常")
        print("[WARN] 如果 API 仍然返回 500，可能是其他問題")
        print("   建議檢查後端終端日誌以獲取詳細錯誤信息")
    else:
        print("[ERROR] 發現問題，請查看上面的錯誤信息")
    
    return 0 if (dm_ok and sm_ok) else 1

if __name__ == "__main__":
    sys.exit(main())

