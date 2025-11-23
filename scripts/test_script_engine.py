"""
劇本引擎測試腳本
"""
import asyncio
import sys
import io
from pathlib import Path
from unittest.mock import Mock

# 設置 UTF-8 編碼（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from group_ai_service import ScriptParser, ScriptEngine
from pyrogram.types import Message, User, Chat


def create_mock_message(text: str) -> Message:
    """創建模擬消息"""
    user = Mock(spec=User)
    user.first_name = "測試用戶"
    user.id = 123456789
    
    chat_type = Mock()
    chat_type.name = "GROUP"
    
    chat = Mock(spec=Chat)
    chat.id = -1001234567890
    chat.type = chat_type
    
    message = Mock(spec=Message)
    message.text = text
    message.from_user = user
    message.chat = chat
    
    return message


async def test_script_parser():
    """測試劇本解析器"""
    print("="*60)
    print("測試 1: 劇本解析器")
    print("="*60)
    
    parser = ScriptParser()
    
    # 加載劇本
    script_path = "ai_models/group_scripts/daily_chat.yaml"
    if not Path(script_path).exists():
        print(f"[FAIL] 劇本文件不存在: {script_path}")
        return None
    
    try:
        script = parser.load_script(script_path)
        print(f"[OK] 劇本加載成功: {script.script_id} v{script.version}")
        print(f"  場景數: {len(script.scenes)}")
        print(f"  變量數: {len(script.variables)}")
        
        # 驗證劇本
        errors = parser.validate_script(script)
        if errors:
            print(f"[WARN] 劇本驗證發現 {len(errors)} 個問題:")
            for error in errors:
                print(f"    - {error}")
        else:
            print("[OK] 劇本驗證通過")
        
        return script
    except Exception as e:
        print(f"[FAIL] 加載劇本失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_script_engine(script):
    """測試劇本引擎"""
    print("\n" + "="*60)
    print("測試 2: 劇本引擎")
    print("="*60)
    
    if not script:
        print("[WARN] 跳過測試（劇本未加載）")
        return
    
    engine = ScriptEngine()
    account_id = "test_account"
    
    # 初始化賬號
    engine.initialize_account(account_id, script)
    print(f"[OK] 賬號 {account_id} 劇本狀態已初始化")
    
    current_scene = engine.get_current_scene(account_id)
    print(f"  當前場景: {current_scene}")
    
    # 測試處理消息
    print("\n[2.1] 測試處理消息（關鍵詞觸發）")
    message = create_mock_message("你好")
    reply = await engine.process_message(account_id, message)
    if reply:
        print(f"[OK] 生成回復: {reply}")
        print(f"  當前場景: {engine.get_current_scene(account_id)}")
    else:
        print("[WARN] 未生成回復")
    
    # 測試處理長消息
    print("\n[2.2] 測試處理長消息")
    message = create_mock_message("今天天氣真好，我想出去走走")
    reply = await engine.process_message(account_id, message)
    if reply:
        print(f"[OK] 生成回復: {reply}")
    else:
        print("[WARN] 未生成回復")
    
    # 測試場景切換
    print("\n[2.3] 測試場景切換")
    success = engine.transition_scene(account_id, "conversation")
    if success:
        print(f"[OK] 場景切換成功，當前場景: {engine.get_current_scene(account_id)}")
    else:
        print("[FAIL] 場景切換失敗")


async def main():
    """主測試流程"""
    print("\n" + "="*60)
    print("劇本引擎測試")
    print("="*60)
    
    # 測試解析器
    script = await test_script_parser()
    
    # 測試引擎
    await test_script_engine(script)
    
    print("\n" + "="*60)
    print("測試完成")
    print("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n測試已中斷")
    except Exception as e:
        print(f"\n\n測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

