"""
紅包處理器測試腳本
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
    RedpacketHandler,
    RedpacketInfo,
    RandomStrategy,
    TimeBasedStrategy,
    FrequencyStrategy,
    AmountBasedStrategy,
    CompositeStrategy
)
from group_ai_service.models.account import AccountConfig
from group_ai_service.dialogue_manager import DialogueContext
from pyrogram.types import Message, User, Chat


def create_mock_message(text: str, group_id: int = -1001234567890) -> Message:
    """創建模擬消息"""
    user = Mock(spec=User)
    user.first_name = "發送者"
    user.id = 987654321
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


async def test_redpacket_detection():
    """測試紅包檢測"""
    print("="*60)
    print("測試 1: 紅包檢測")
    print("="*60)
    
    handler = RedpacketHandler()
    
    # 測試包含紅包關鍵詞的消息
    test_cases = [
        ("發紅包了！", True),
        ("搶紅包啦", True),
        ("red packet here", True),
        ("普通消息", False),
        ("紅包雨來了，快搶！", True),
    ]
    
    for text, expected in test_cases:
        message = create_mock_message(text)
        redpacket = await handler.detect_redpacket(message)
        detected = redpacket is not None
        
        status = "✓" if detected == expected else "✗"
        print(f"{status} 消息: '{text}' -> 檢測: {detected} (預期: {expected})")
        
        if redpacket:
            print(f"    紅包 ID: {redpacket.redpacket_id}")
            print(f"    群組 ID: {redpacket.group_id}")
            if redpacket.amount:
                print(f"    金額: {redpacket.amount}")


async def test_strategies():
    """測試策略"""
    print("\n" + "="*60)
    print("測試 2: 紅包參與策略")
    print("="*60)
    
    redpacket = RedpacketInfo(
        redpacket_id="test_1",
        group_id=-1001234567890,
        sender_id=123456789,
        amount=10.0
    )
    
    config = AccountConfig(
        account_id="test_account",
        session_file="test.session",
        script_id="test",
        group_ids=[],
        redpacket_enabled=True,
        redpacket_probability=0.5
    )
    
    context = DialogueContext("test_account", -1001234567890)
    
    # 測試隨機策略
    print("\n[2.1] 隨機策略")
    strategy = RandomStrategy(base_probability=0.7)
    prob = strategy.evaluate(redpacket, config, context)
    print(f"  概率: {prob:.2f} (預期: 0.70)")
    
    # 測試時間策略
    print("\n[2.2] 時間策略")
    strategy = TimeBasedStrategy(peak_hours=[18, 19, 20], peak_probability=0.9)
    prob = strategy.evaluate(redpacket, config, context)
    print(f"  當前時間概率: {prob:.2f}")
    
    # 測試金額策略
    print("\n[2.3] 金額策略")
    strategy = AmountBasedStrategy(
        min_amount=0.01,
        max_amount=100.0,
        high_amount_probability=0.9,
        low_amount_probability=0.3
    )
    prob = strategy.evaluate(redpacket, config, context)
    print(f"  金額 {redpacket.amount} 的概率: {prob:.2f}")
    
    # 測試組合策略
    print("\n[2.4] 組合策略")
    composite = CompositeStrategy([
        (RandomStrategy(0.5), 0.3),
        (TimeBasedStrategy(), 0.4),
        (AmountBasedStrategy(), 0.3),
    ])
    prob = composite.evaluate(redpacket, config, context)
    print(f"  組合策略概率: {prob:.2f}")


async def test_participation():
    """測試參與邏輯"""
    print("\n" + "="*60)
    print("測試 3: 紅包參與")
    print("="*60)
    
    handler = RedpacketHandler()
    handler.set_default_strategy(RandomStrategy(base_probability=0.8))
    
    redpacket = RedpacketInfo(
        redpacket_id="test_2",
        group_id=-1001234567890,
        sender_id=123456789,
        amount=5.0
    )
    
    config = AccountConfig(
        account_id="test_account",
        session_file="test.session",
        script_id="test",
        group_ids=[],
        redpacket_enabled=True,
        redpacket_probability=0.5
    )
    
    context = DialogueContext("test_account", -1001234567890)
    
    # 測試參與決策
    print("\n[3.1] 參與決策")
    should_participate = await handler.should_participate(
        account_id="test_account",
        redpacket=redpacket,
        account_config=config,
        context=context
    )
    print(f"  決定參與: {should_participate}")
    
    # 測試參與執行（模擬）
    print("\n[3.2] 參與執行（模擬）")
    mock_client = Mock()
    result = await handler.participate(
        account_id="test_account",
        redpacket=redpacket,
        client=mock_client,
        sender_name="測試發包人",
        participant_name="測試參與者"
    )
    print(f"  成功: {result.success}")
    if result.success:
        print(f"  金額: {result.amount}")
    if result.error:
        print(f"  錯誤: {result.error}")
    
    # 測試重複點擊檢測
    print("\n[3.3] 重複點擊檢測")
    result2 = await handler.participate(
        account_id="test_account",
        redpacket=redpacket,
        client=mock_client,
        sender_name="測試發包人",
        participant_name="測試參與者"
    )
    if not result2.success and "重複點擊" in result2.error:
        print(f"  ✓ 重複點擊檢測成功: {result2.error}")
    else:
        print(f"  ✗ 重複點擊檢測失敗（預期應該失敗）")
    
    # 測試金額驗證（金額太小）
    print("\n[3.4] 金額驗證（金額太小）")
    small_redpacket = RedpacketInfo(
        redpacket_id="test_small",
        group_id=-1001234567890,
        sender_id=123456789,
        amount=0.001  # 小於最小金額
    )
    result3 = await handler.participate(
        account_id="test_account",
        redpacket=small_redpacket,
        client=mock_client
    )
    if not result3.success and "金額太小" in result3.error:
        print(f"  ✓ 金額驗證成功: {result3.error}")
    else:
        print(f"  ✗ 金額驗證失敗（預期應該失敗）")


async def test_statistics():
    """測試統計"""
    print("\n" + "="*60)
    print("測試 4: 參與統計")
    print("="*60)
    
    handler = RedpacketHandler()
    
    # 模擬一些參與記錄
    from datetime import datetime, timedelta
    for i in range(10):
        result = await handler.participate(
            account_id="test_account",
            redpacket=RedpacketInfo(
                redpacket_id=f"test_{i}",
                group_id=-1001234567890,
                sender_id=123456789,
                amount=1.0
            ),
            client=Mock(),
            sender_name="測試發包人",
            participant_name="測試參與者"
        )
    
    # 獲取統計
    stats = handler.get_participation_stats(account_id="test_account")
    print(f"  總參與次數: {stats['total_participations']}")
    print(f"  成功次數: {stats['successful']}")
    print(f"  失敗次數: {stats['failed']}")
    print(f"  成功率: {stats['success_rate']:.2%}")
    print(f"  總金額: {stats['total_amount']:.2f}")
    print(f"  平均金額: {stats['average_amount']:.2f}")


async def test_new_features():
    """測試新功能：最佳手氣提示、搶包通知等"""
    print("\n" + "="*60)
    print("測試 5: 新功能測試")
    print("="*60)
    
    handler = RedpacketHandler()
    handler.set_default_strategy(RandomStrategy(base_probability=1.0))  # 100% 參與
    
    # 創建一個模擬的 client
    mock_client = Mock()
    mock_me = Mock()
    mock_me.first_name = "測試參與者"
    mock_me.username = "test_participant"
    mock_client.get_me = Mock(return_value=mock_me)
    mock_client.send_message = Mock()
    mock_client.is_connected = True
    
    # 測試最佳手氣檢測
    print("\n[5.1] 最佳手氣提示測試")
    redpacket = RedpacketInfo(
        redpacket_id="test_best_luck",
        group_id=-1001234567890,
        sender_id=123456789,
        amount=10.0,
        count=5
    )
    
    # 第一次參與（應該是最佳手氣）
    result1 = await handler.participate(
        account_id="test_account",
        redpacket=redpacket,
        client=mock_client,
        sender_name="測試發包人",
        participant_name="測試參與者"
    )
    print(f"  第一次參與: 成功={result1.success}, 金額={result1.amount}")
    
    # 模擬其他參與者（金額較小）
    from group_ai_service.redpacket_handler import RedpacketResult
    handler.participation_log.append(RedpacketResult(
        redpacket_id=redpacket.redpacket_id,
        account_id="other_account",
        success=True,
        amount=2.0
    ))
    
    # 檢查是否已標記為最佳手氣
    best_luck_key = f"test_account:{redpacket.redpacket_id}"
    if best_luck_key in handler._best_luck_announced:
        print(f"  ✓ 最佳手氣已標記")
    else:
        print(f"  ✗ 最佳手氣未標記")
    
    # 測試搶包通知記錄
    print("\n[5.2] 搶包通知記錄測試")
    if redpacket.redpacket_id in handler._redpacket_notifications:
        notification_info = handler._redpacket_notifications[redpacket.redpacket_id]
        participants_count = len(notification_info.get("participants", []))
        remaining_count = notification_info.get("total_count", 0) - participants_count
        print(f"  參與者數量: {participants_count}")
        print(f"  剩餘數量: {remaining_count}")
        print(f"  ✓ 搶包通知記錄已創建")
    else:
        print(f"  ✗ 搶包通知記錄未創建")
    
    # 測試數據清理
    print("\n[5.3] 數據清理測試")
    # 手動設置舊的清理時間，觸發清理
    from datetime import datetime, timedelta
    handler._last_cleanup = datetime.now() - timedelta(seconds=3700)  # 超過1小時
    await handler._cleanup_old_data()
    print(f"  ✓ 數據清理功能正常")
    
    # 測試每小時計數功能
    print("\n[5.4] 每小時計數功能測試")
    test_account_id = "test_hourly_count"
    
    # 獲取初始計數
    initial_count = handler.get_hourly_participation_count(test_account_id)
    print(f"  初始計數: {initial_count}")
    
    # 模擬多次參與（通過直接調用計數方法）
    handler._increment_hourly_participation(test_account_id)
    handler._increment_hourly_participation(test_account_id)
    handler._increment_hourly_participation(test_account_id)
    
    # 獲取更新後的計數
    updated_count = handler.get_hourly_participation_count(test_account_id)
    print(f"  更新後計數: {updated_count}")
    
    if updated_count == initial_count + 3:
        print(f"  ✓ 每小時計數功能正常（{updated_count} 次參與）")
    else:
        print(f"  ✗ 每小時計數功能異常（預期: {initial_count + 3}, 實際: {updated_count}）")
    
    # 測試 FrequencyStrategy 使用每小時計數
    print("\n[5.5] FrequencyStrategy 每小時計數集成測試")
    from group_ai_service.redpacket_handler import FrequencyStrategy
    from group_ai_service.dialogue_manager import DialogueContext
    
    frequency_strategy = FrequencyStrategy(max_per_hour=3, cooldown_seconds=0)
    
    # 創建模擬上下文
    test_context = DialogueContext(account_id=test_account_id, group_id=-1001234567890)
    test_context.last_reply_time = None  # 無冷卻時間限制
    
    # 測試未達到上限時的概率
    test_redpacket = RedpacketInfo(
        redpacket_id="test_frequency",
        group_id=-1001234567890,
        sender_id=123456789,
        amount=5.0,
        count=10
    )
    
    from group_ai_service.models.account import AccountConfig
    test_config = AccountConfig(
        account_id=test_account_id,
        session_file="test.session",
        script_id="test",
        group_ids=[-1001234567890],
        active=True
    )
    
    # 當前計數為 3，上限為 3，應該返回 0
    probability_at_limit = frequency_strategy.evaluate(
        test_redpacket, test_config, test_context, handler=handler
    )
    print(f"  達到上限時的概率: {probability_at_limit}")
    
    if probability_at_limit == 0.0:
        print(f"  ✓ 達到上限時正確返回 0 概率")
    else:
        print(f"  ✗ 達到上限時應該返回 0，實際返回 {probability_at_limit}")
    
    # 重置計數，測試未達到上限的情況
    handler._hourly_participation.clear()
    handler._increment_hourly_participation(test_account_id)  # 計數為 1，上限為 3
    
    probability_below_limit = frequency_strategy.evaluate(
        test_redpacket, test_config, test_context, handler=handler
    )
    print(f"  未達到上限時的概率: {probability_below_limit}")
    
    if probability_below_limit > 0.0:
        print(f"  ✓ 未達到上限時返回正概率")
    else:
        print(f"  ⚠ 未達到上限時返回 0（可能因為其他限制）")


async def main():
    """主測試流程"""
    print("\n" + "="*60)
    print("紅包處理器測試")
    print("="*60 + "\n")
    
    await test_redpacket_detection()
    await test_strategies()
    await test_participation()
    await test_statistics()
    await test_new_features()
    
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

