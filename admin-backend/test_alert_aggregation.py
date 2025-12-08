#!/usr/bin/env python3
"""
测试告警聚合功能
"""
import sys
from datetime import datetime, timedelta
from app.services.alert_aggregator import get_alert_aggregator, AlertSeverity

def test_alert_aggregation():
    """测试告警聚合功能"""
    aggregator = get_alert_aggregator()
    
    print("=" * 60)
    print("测试告警聚合功能")
    print("=" * 60)
    
    # 1. 添加新告警
    print("\n1. 添加新告警...")
    is_new, alert = aggregator.add_alert(
        alert_type="error",
        message="账户连接失败",
        account_id="account_001"
    )
    print(f"   新告警: {is_new}, 告警键: {alert.alert_key if alert else None}")
    assert is_new, "应该是新告警"
    
    # 2. 添加重复告警（5分钟内）
    print("\n2. 添加重复告警（5分钟内）...")
    is_new2, alert2 = aggregator.add_alert(
        alert_type="error",
        message="账户连接失败",
        account_id="account_001"
    )
    print(f"   新告警: {is_new2}, 计数: {alert2.count if alert2 else 0}")
    assert not is_new2, "应该是重复告警"
    assert alert2.count == 2, f"计数应该是2，实际是{alert2.count}"
    
    # 3. 添加不同级别的告警
    print("\n3. 添加不同级别的告警...")
    is_new3, alert3 = aggregator.add_alert(
        alert_type="warning",
        message="响应时间较慢",
        account_id="account_002"
    )
    print(f"   新告警: {is_new3}, 严重程度: {alert3.severity.value if alert3 else None}")
    assert is_new3, "应该是新告警"
    assert alert3.severity == AlertSeverity.MEDIUM, "警告应该是中等严重程度"
    
    # 4. 获取活跃告警
    print("\n4. 获取活跃告警...")
    active_alerts = aggregator.get_active_alerts()
    print(f"   活跃告警数量: {len(active_alerts)}")
    assert len(active_alerts) >= 2, "应该有至少2个活跃告警"
    
    # 5. 获取统计信息
    print("\n5. 获取统计信息...")
    stats = aggregator.get_alert_statistics()
    print(f"   总告警数: {stats['total_alerts']}")
    print(f"   去重数量: {stats['deduplicated']}")
    print(f"   聚合数量: {stats['aggregated']}")
    print(f"   活跃告警: {stats['total_active']}")
    assert stats['total_alerts'] >= 2, "应该有至少2个告警"
    assert stats['deduplicated'] >= 1, "应该有至少1个去重"
    
    # 6. 静默告警
    print("\n6. 静默告警...")
    success = aggregator.suppress_alert(
        alert_key=alert.alert_key,
        duration_seconds=3600,
        reason="测试静默"
    )
    print(f"   静默成功: {success}")
    assert success, "静默应该成功"
    
    # 7. 确认告警
    print("\n7. 确认告警...")
    success2 = aggregator.acknowledge_alert(
        alert_key=alert3.alert_key,
        acknowledged_by="test_user@example.com"
    )
    print(f"   确认成功: {success2}")
    assert success2, "确认应该成功"
    
    # 8. 解决告警
    print("\n8. 解决告警...")
    success3 = aggregator.resolve_alert(alert_key=alert3.alert_key)
    print(f"   解决成功: {success3}")
    assert success3, "解决应该成功"
    
    # 9. 最终统计
    print("\n9. 最终统计...")
    final_stats = aggregator.get_alert_statistics()
    print(f"   总告警数: {final_stats['total_alerts']}")
    print(f"   已解决: {final_stats['resolved']}")
    print(f"   已抑制: {final_stats['suppressed']}")
    assert final_stats['resolved'] >= 1, "应该有至少1个已解决告警"
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        test_alert_aggregation()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

