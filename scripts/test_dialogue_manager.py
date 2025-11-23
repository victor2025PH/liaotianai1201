"""
對話管理器測試腳本
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

from group_ai_service import DialogueManager, ScriptEngine, ScriptParser
from group_ai_service.models.account import AccountConfig
from pyrogram.types import Message, User, Chat


def create_mock_message(text: str, group_id: int = -1001234567890) -> Message:
    """創建模擬消息"""
    user = Mock(spec=User)
    user.first_name = "測試用戶"
    user.id = 123456789
    user.is_self = False
    
    chat_type = Mock()
    chat_type.name = "GROUP"
    
    chat = Mock(spec=Chat)
    chat.id = group_id
    chat.type = chat_type
    
    message = Mock(spec=Message)
    message.text = text
    message.from_user = user
    message.chat = chat
    message.id = 1
    message.date = None
    
    return message


async def test_dialogue_manager():
    """測試對話管理器"""
    print("="*60)
    print("測試 1: 對話管理器基礎功能")
    print("="*60)
    
    # 創建對話管理器
    dialogue_manager = DialogueManager()
    print("[OK] DialogueManager 創建成功")
    
    # 加載劇本
    parser = ScriptParser()
    script = parser.load_script("ai_models/group_scripts/daily_chat.yaml")
    print(f"[OK] 劇本加載成功: {script.script_id}")
    
    # 創建劇本引擎
    script_engine = ScriptEngine()
    account_id = "test_account"
    script_engine.initialize_account(account_id, script)
    print(f"[OK] 劇本引擎初始化成功")
    
    # 初始化對話管理器
    group_ids = [-1001234567890]
    dialogue_manager.initialize_account(account_id, script_engine, group_ids)
    print(f"[OK] 對話管理器初始化成功")
    
    # 創建賬號配置
    config = AccountConfig(
        account_id=account_id,
        session_file="test.session",
        script_id=script.script_id,
        group_ids=group_ids,
        active=True,
        reply_rate=1.0,  # 100% 回復率（測試用）
        max_replies_per_hour=100,
        min_reply_interval=0  # 無間隔（測試用）
    )
    
    # 測試處理消息
    print("\n[1.1] 測試處理消息（關鍵詞觸發）")
    message = create_mock_message("你好", group_ids[0])
    reply = await dialogue_manager.process_message(account_id, group_ids[0], message, config)
    if reply:
        print(f"[OK] 生成回復: {reply}")
    else:
        print("[WARN] 未生成回復")
    
    # 測試上下文
    print("\n[1.2] 測試對話上下文")
    context = dialogue_manager.get_context(account_id, group_ids[0])
    if context:
        print(f"[OK] 上下文獲取成功")
        print(f"  歷史消息數: {len(context.history)}")
        print(f"  今日回復數: {context.reply_count_today}")
    else:
        print("[FAIL] 上下文獲取失敗")
    
    # 測試回復頻率限制
    print("\n[1.3] 測試回復頻率限制")
    config.reply_rate = 0.0  # 0% 回復率
    message = create_mock_message("測試消息", group_ids[0])
    reply = await dialogue_manager.process_message(account_id, group_ids[0], message, config)
    if not reply:
        print("[OK] 正確跳過回復（回復率限制）")
    else:
        print("[FAIL] 應該跳過回復")
    
    # 測試新成員檢測
    print("\n[1.4] 測試新成員檢測")
    context = dialogue_manager.get_context(account_id, group_ids[0])
    
    # 測試方式1: new_chat_members 屬性
    new_member_message = create_mock_message("", group_ids[0])
    new_member_message.new_chat_members = [Mock()]
    is_new_member1 = dialogue_manager._check_new_member(new_member_message, context)
    if is_new_member1:
        print("[OK] 通過 new_chat_members 屬性檢測到新成員")
    else:
        print("[FAIL] 應該檢測到新成員")
    
    # 測試方式2: service 類型
    service_message = create_mock_message("", group_ids[0])
    service_message.service = Mock()
    service_message.service.type = "new_members"
    is_new_member2 = dialogue_manager._check_new_member(service_message, context)
    if is_new_member2:
        print("[OK] 通過 service 類型檢測到新成員")
    else:
        print("[FAIL] 應該檢測到新成員")
    
    # 測試方式3: 關鍵詞檢測（備用）
    keyword_message = create_mock_message("歡迎新成員加入", group_ids[0])
    keyword_message.from_user = None  # 模擬系統消息
    is_new_member3 = dialogue_manager._check_new_member(keyword_message, context)
    print(f"[INFO] 關鍵詞檢測結果: {is_new_member3} (可能因條件不滿足而為 False)")
    
    # 測試普通消息不應被識別為新成員
    normal_message = create_mock_message("普通聊天消息", group_ids[0])
    is_new_member4 = dialogue_manager._check_new_member(normal_message, context)
    if not is_new_member4:
        print("[OK] 普通消息正確識別為非新成員")
    else:
        print("[FAIL] 普通消息不應該被識別為新成員")
    
    print("\n" + "="*60)
    print("測試完成")
    print("="*60)


async def main():
    """主測試流程"""
    print("\n" + "="*60)
    print("對話管理器測試")
    print("="*60 + "\n")
    
    await test_dialogue_manager()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n測試已中斷")
    except Exception as e:
        print(f"\n\n測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

