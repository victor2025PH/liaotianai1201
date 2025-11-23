"""
準備 session 文件用於測試

此腳本會：
1. 創建 sessions/ 目錄（如果不存在）
2. 查找項目中的 .session 文件
3. 將有效的 session 文件複製到 sessions/ 目錄
4. 顯示可用的 session 文件列表
"""
import shutil
import sys
import io
from pathlib import Path

# 設置 UTF-8 編碼（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent
sessions_dir = project_root / "sessions"

def find_session_files():
    """查找項目中的所有 .session 文件"""
    session_files = []
    
    # 在項目根目錄查找
    for file in project_root.glob("*.session"):
        if file.is_file() and not file.name.endswith(".session.session"):
            session_files.append(file)
    
    # 在 utils 目錄查找
    utils_dir = project_root / "utils"
    if utils_dir.exists():
        for file in utils_dir.glob("*.session"):
            if file.is_file():
                session_files.append(file)
    
    return session_files

def prepare_sessions():
    """準備 session 文件"""
    print("="*60)
    print("準備 Session 文件用於測試")
    print("="*60)
    
    # 1. 創建 sessions 目錄
    print("\n[1] 創建 sessions 目錄...")
    sessions_dir.mkdir(exist_ok=True)
    print(f"[OK] sessions 目錄已準備: {sessions_dir}")
    
    # 2. 查找現有的 session 文件
    print("\n[2] 查找現有的 session 文件...")
    session_files = find_session_files()
    
    if not session_files:
        print("[WARN] 未找到任何 .session 文件")
        print("\n提示: 可以使用以下命令生成新的 session 文件:")
        print("  py tools/session_manager/generate_session.py")
        return []
    
    print(f"[OK] 找到 {len(session_files)} 個 session 文件:")
    for i, file in enumerate(session_files, 1):
        size_kb = file.stat().st_size / 1024
        print(f"  {i}. {file.name} ({size_kb:.1f} KB) - {file.parent}")
    
    # 3. 複製到 sessions 目錄
    print("\n[3] 複製 session 文件到 sessions/ 目錄...")
    copied_files = []
    
    for file in session_files:
        target = sessions_dir / file.name
        
        # 如果目標已存在，跳過
        if target.exists():
            print(f"  [SKIP] {file.name} 已存在於 sessions/ 目錄")
            copied_files.append(target)
            continue
        
        try:
            shutil.copy2(file, target)
            print(f"  [OK] 已複製: {file.name}")
            copied_files.append(target)
        except Exception as e:
            print(f"  [FAIL] 複製 {file.name} 失敗: {e}")
    
    # 4. 顯示最終結果
    print("\n[4] 檢查 sessions/ 目錄...")
    final_files = list(sessions_dir.glob("*.session"))
    
    if final_files:
        print(f"[OK] sessions/ 目錄中有 {len(final_files)} 個 session 文件:")
        for file in final_files:
            size_kb = file.stat().st_size / 1024
            print(f"  - {file.name} ({size_kb:.1f} KB)")
    else:
        print("[WARN] sessions/ 目錄中沒有 session 文件")
    
    print("\n" + "="*60)
    print("準備完成！")
    print("="*60)
    print("\n現在可以運行真實測試:")
    print("  py scripts/test_account_manager.py")
    
    return final_files

if __name__ == "__main__":
    try:
        prepare_sessions()
    except KeyboardInterrupt:
        print("\n\n操作已中斷")
    except Exception as e:
        print(f"\n\n發生錯誤: {e}")
        import traceback
        traceback.print_exc()

