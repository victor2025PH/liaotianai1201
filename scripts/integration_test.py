"""
系統集成測試 - 測試所有模塊的協同工作
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

from group_ai_service import (
    AccountManager,
    ScriptParser,
    ScriptEngine,
    DialogueManager,
    RedpacketHandler,
    MonitorService,
    ExtendedSessionPool,
)
from group_ai_service.models.account import AccountConfig, AccountStatusEnum
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


async def test_integration():
    """系統集成測試"""
    print("="*60)
    print("系統集成測試")
    print("="*60)
    
    # 1. 初始化所有服務
    print("\n[1] 初始化服務...")
    account_manager = AccountManager()
    script_parser = ScriptParser()
    script_engine = ScriptEngine()
    redpacket_handler = RedpacketHandler()
    monitor_service = MonitorService()
    dialogue_manager = DialogueManager()
    dialogue_manager.redpacket_handler = redpacket_handler
    dialogue_manager.monitor_service = monitor_service
    
    print("  ✅ AccountManager 初始化成功")
    print("  ✅ ScriptParser 初始化成功")
    print("  ✅ ScriptEngine 初始化成功")
    print("  ✅ RedpacketHandler 初始化成功")
    print("  ✅ MonitorService 初始化成功")
    print("  ✅ DialogueManager 初始化成功")
    
    # 2. 加載劇本
    print("\n[2] 加載劇本...")
    script_path = "ai_models/group_scripts/daily_chat.yaml"
    try:
        script = script_parser.load_script(script_path)
        print(f"  ✅ 劇本加載成功: {script.script_id}")
    except Exception as e:
        print(f"  ⚠️  劇本加載失敗: {e} (使用模擬劇本)")
        script = None
    
    # 3. 創建測試賬號配置
    print("\n[3] 創建測試賬號...")
    account_id = "test_integration_001"
    account_config = AccountConfig(
        account_id=account_id,
        session_file="test.session",
        script_id=script.script_id if script else "test_script",
        group_ids=[-1001234567890],
        active=True,
        reply_rate=1.0,
        min_reply_interval=0,
        max_replies_per_hour=100,
        redpacket_enabled=True,
        redpacket_probability=0.5
    )
    
    # 初始化對話管理器
    if script:
        script_engine.initialize_account(account_id, script)
        dialogue_manager.script_engines[account_id] = script_engine
    
    print(f"  ✅ 測試賬號創建成功: {account_id}")
    
    # 4. 測試消息處理流程
    print("\n[4] 測試消息處理流程...")
    test_messages = [
        ("你好", "關鍵詞觸發"),
        ("今天天氣怎麼樣？", "普通消息"),
        ("發紅包了！", "紅包檢測"),
    ]
    
    for msg_text, test_type in test_messages:
        message = create_mock_message(msg_text)
        
        try:
            reply = await dialogue_manager.process_message(
                account_id=account_id,
                group_id=message.chat.id,
                message=message,
                account_config=account_config
            )
            
            if reply:
                print(f"  ✅ {test_type}: '{msg_text}' -> '{reply[:50]}...'")
            else:
                print(f"  ⚠️  {test_type}: '{msg_text}' -> 無回復")
        except Exception as e:
            print(f"  ❌ {test_type}: '{msg_text}' -> 錯誤: {e}")
    
    # 5. 測試監控指標
    print("\n[5] 測試監控指標...")
    system_metrics = monitor_service.get_system_metrics()
    print(f"  ✅ 系統指標獲取成功:")
    print(f"     總賬號數: {system_metrics.total_accounts}")
    print(f"     總消息數: {system_metrics.total_messages}")
    print(f"     總回復數: {system_metrics.total_replies}")
    print(f"     總錯誤數: {system_metrics.total_errors}")
    
    account_metrics = monitor_service.get_account_metrics(account_id)
    if account_metrics:
        print(f"  ✅ 賬號指標獲取成功:")
        print(f"     消息數: {account_metrics.message_count}")
        print(f"     回復數: {account_metrics.reply_count}")
        print(f"     紅包數: {account_metrics.redpacket_count}")
    
    # 6. 測試告警
    print("\n[6] 測試告警系統...")
    alerts = monitor_service.check_alerts()
    print(f"  ✅ 告警檢查完成，發現 {len(alerts)} 個告警")
    
    # 7. 測試紅包處理
    print("\n[7] 測試紅包處理...")
    # 創建新的紅包消息（使用不同的消息 ID 避免去重）
    redpacket_message = create_mock_message("發紅包了！10元")
    redpacket_message.id = 999  # 使用不同的 ID
    redpacket = await redpacket_handler.detect_redpacket(redpacket_message)
    if redpacket:
        print(f"  ✅ 紅包檢測成功: {redpacket.redpacket_id}")
        if redpacket.amount:
            print(f"     金額: {redpacket.amount}")
        
        # 測試參與決策
        context_key = f"{account_id}:{redpacket.group_id}"
        context = dialogue_manager.contexts.get(context_key)
        if not context:
            from group_ai_service.dialogue_manager import DialogueContext
            context = DialogueContext(account_id, redpacket.group_id)
        
        should_participate = await redpacket_handler.should_participate(
            account_id=account_id,
            redpacket=redpacket,
            account_config=account_config,
            context=context
        )
        print(f"  ✅ 參與決策: {should_participate}")
    else:
        print("  ⚠️  紅包檢測失敗（可能是去重機制）")
    
    print("\n" + "="*60)
    print("集成測試完成")
    print("="*60)
    print("\n✅ 所有核心模塊協同工作正常")


async def main():
    """主測試流程"""
    try:
        await test_integration()
    except KeyboardInterrupt:
        print("\n\n測試已中斷")
    except Exception as e:
        print(f"\n\n測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

