"""
監控服務測試腳本
"""
import sys
import io
from pathlib import Path
from datetime import datetime, timedelta

# 設置 UTF-8 編碼（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from group_ai_service import MonitorService
from group_ai_service.models.account import AccountStatusEnum


def test_monitor_service():
    """測試監控服務"""
    print("="*60)
    print("測試 1: 監控服務基礎功能")
    print("="*60)
    
    monitor = MonitorService()
    print("[OK] MonitorService 創建成功")
    
    # 測試記錄消息
    print("\n[1.1] 測試記錄消息")
    monitor.record_message("account_1", "received", success=True)
    monitor.record_message("account_1", "received", success=False)
    print("[OK] 消息記錄成功")
    
    # 測試記錄回復
    print("\n[1.2] 測試記錄回復")
    monitor.record_reply("account_1", reply_time=1.5, success=True)
    monitor.record_reply("account_1", reply_time=2.0, success=True)
    monitor.record_reply("account_1", reply_time=0.5, success=False)
    print("[OK] 回復記錄成功")
    
    # 測試記錄紅包
    print("\n[1.3] 測試記錄紅包")
    monitor.record_redpacket("account_1", success=True, amount=5.0)
    monitor.record_redpacket("account_1", success=True, amount=10.0)
    monitor.record_redpacket("account_1", success=False)
    print("[OK] 紅包記錄成功")
    
    # 測試獲取賬號指標
    print("\n[1.4] 測試獲取賬號指標")
    metrics = monitor.get_account_metrics("account_1")
    if metrics:
        print(f"[OK] 賬號指標獲取成功")
        print(f"  消息數: {metrics.message_count}")
        print(f"  回復數: {metrics.reply_count}")
        print(f"  紅包數: {metrics.redpacket_count}")
        print(f"  成功數: {metrics.success_count}")
        print(f"  錯誤數: {metrics.error_count}")
        print(f"  平均回復時間: {metrics.total_reply_time / metrics.reply_count if metrics.reply_count > 0 else 0:.2f}s")
    else:
        print("[FAIL] 賬號指標獲取失敗")
    
    # 測試獲取系統指標
    print("\n[1.5] 測試獲取系統指標")
    system_metrics = monitor.get_system_metrics()
    print(f"[OK] 系統指標獲取成功")
    print(f"  總賬號數: {system_metrics.total_accounts}")
    print(f"  在線賬號數: {system_metrics.online_accounts}")
    print(f"  總消息數: {system_metrics.total_messages}")
    print(f"  總回復數: {system_metrics.total_replies}")
    print(f"  總紅包數: {system_metrics.total_redpackets}")
    print(f"  總錯誤數: {system_metrics.total_errors}")
    print(f"  平均回復時間: {system_metrics.average_reply_time:.2f}s")
    
    # 測試告警檢查
    print("\n[1.6] 測試告警檢查")
    alerts = monitor.check_alerts()
    print(f"[OK] 告警檢查完成，發現 {len(alerts)} 個告警")
    for alert in alerts[:5]:  # 只顯示前 5 個
        print(f"  - [{alert.alert_type}] {alert.message}")
    
    # 測試事件日誌
    print("\n[1.7] 測試事件日誌")
    events = monitor.get_event_log(account_id="account_1", limit=10)
    print(f"[OK] 事件日誌獲取成功，共 {len(events)} 條事件")
    for event in events[:3]:  # 只顯示前 3 條
        print(f"  - {event.get('type')}: {event.get('timestamp')}")
    
    # 測試時間範圍過濾
    print("\n[1.8] 測試時間範圍過濾")
    
    # 記錄一些帶時間戳的事件
    import time
    time.sleep(0.1)  # 確保時間戳不同
    
    # 記錄新的事件
    monitor.record_message("account_2", "received", success=True)
    monitor.record_reply("account_2", reply_time=1.0, success=True)
    monitor.record_redpacket("account_2", success=True, amount=3.0)
    
    # 獲取最近1分鐘的指標
    one_minute_ago = timedelta(minutes=1)
    metrics_with_range = monitor.get_account_metrics("account_2", time_range=one_minute_ago)
    
    if metrics_with_range:
        print(f"[OK] 時間範圍過濾成功")
        print(f"  消息數（1分鐘內）: {metrics_with_range.message_count}")
        print(f"  回復數（1分鐘內）: {metrics_with_range.reply_count}")
        print(f"  紅包數（1分鐘內）: {metrics_with_range.redpacket_count}")
        
        # 驗證過濾是否生效（應該只包含最近的事件）
        if metrics_with_range.message_count >= 1:
            print(f"  ✓ 時間範圍過濾正常工作")
        else:
            print(f"  ⚠ 時間範圍過濾可能未正確工作")
    else:
        print("[WARN] 時間範圍過濾返回 None（可能是賬號不存在）")
    
    # 測試長時間範圍（應該包含所有事件）
    one_hour_ago = timedelta(hours=1)
    all_metrics = monitor.get_account_metrics("account_1", time_range=one_hour_ago)
    if all_metrics:
        print(f"\n  賬號 account_1 的1小時內指標:")
        print(f"  消息數: {all_metrics.message_count}")
        print(f"  回復數: {all_metrics.reply_count}")
        print(f"  紅包數: {all_metrics.redpacket_count}")
    
    print("\n" + "="*60)
    print("測試完成")
    print("="*60)


def main():
    """主測試流程"""
    print("\n" + "="*60)
    print("監控服務測試")
    print("="*60 + "\n")
    
    test_monitor_service()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n測試已中斷")
    except Exception as e:
        print(f"\n\n測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

