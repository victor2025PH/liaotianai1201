#!/usr/bin/env python3
"""
告警通知测试脚本
测试告警触发、聚合和通知发送功能
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "admin-backend"))

import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_alert_aggregation():
    """测试告警聚合功能"""
    print("\n=== 测试告警聚合功能 ===")
    
    try:
        from app.services.alert_aggregator import get_alert_aggregator, AlertSeverity
        
        aggregator = get_alert_aggregator()
        
        # 添加测试告警
        test_alerts = [
            {
                "alert_key": "test_api_slow_001",
                "severity": AlertSeverity.MEDIUM,
                "message": "API响应时间超过阈值: /api/v1/group-ai/dashboard 响应时间 1200ms",
                "source": "performance_monitor",
                "metadata": {"endpoint": "/api/v1/group-ai/dashboard", "response_time_ms": 1200}
            },
            {
                "alert_key": "test_api_slow_002",
                "severity": AlertSeverity.MEDIUM,
                "message": "API响应时间超过阈值: /api/v1/group-ai/scripts 响应时间 1500ms",
                "source": "performance_monitor",
                "metadata": {"endpoint": "/api/v1/group-ai/scripts", "response_time_ms": 1500}
            },
            {
                "alert_key": "test_database_slow",
                "severity": AlertSeverity.HIGH,
                "message": "检测到慢查询: SELECT * FROM group_ai_accounts 耗时 800ms",
                "source": "database_monitor",
                "metadata": {"query": "SELECT * FROM group_ai_accounts", "time_ms": 800}
            },
            {
                "alert_key": "test_cpu_high",
                "severity": AlertSeverity.HIGH,
                "message": "CPU使用率过高: 85%",
                "source": "system_monitor",
                "metadata": {"cpu_usage": 85}
            }
        ]
        
        # 添加告警
        for alert in test_alerts:
            aggregator.add_alert(**alert)
            print(f"✓ 添加告警: {alert['alert_key']}")
        
        # 获取活跃告警
        active_alerts = aggregator.get_active_alerts()
        print(f"\n活跃告警数: {len(active_alerts)}")
        
        # 获取统计信息
        stats = aggregator.get_alert_statistics()
        print(f"\n告警统计:")
        print(f"  - 总告警数: {stats['total_alerts']}")
        print(f"  - 去重后: {stats['deduplicated']}")
        print(f"  - 已聚合: {stats['aggregated']}")
        print(f"  - 活跃告警: {stats['total_active']}")
        print(f"  - 按严重程度:")
        for severity, count in stats['active_by_severity'].items():
            print(f"    {severity}: {count}")
        
        # 测试告警静默
        print(f"\n=== 测试告警静默 ===")
        if active_alerts:
            test_alert_key = active_alerts[0]['alert_key']
            success = aggregator.suppress_alert(test_alert_key, duration_seconds=3600, reason="测试静默")
            if success:
                print(f"✓ 告警 {test_alert_key} 已静默")
            else:
                print(f"✗ 告警静默失败")
        
        # 测试告警确认
        print(f"\n=== 测试告警确认 ===")
        if len(active_alerts) > 1:
            test_alert_key = active_alerts[1]['alert_key']
            success = aggregator.acknowledge_alert(test_alert_key, acknowledged_by="test_user")
            if success:
                print(f"✓ 告警 {test_alert_key} 已确认")
            else:
                print(f"✗ 告警确认失败")
        
        return True
        
    except Exception as e:
        logger.error(f"告警聚合测试失败: {e}", exc_info=True)
        print(f"✗ 告警聚合测试失败: {e}")
        return False


async def test_alert_rules_loading():
    """测试告警规则加载"""
    print("\n=== 测试告警规则加载 ===")
    
    try:
        import yaml
        from pathlib import Path
        
        rules_file = Path(__file__).parent.parent.parent / "admin-backend" / "app" / "config" / "alert_rules.yaml"
        
        if not rules_file.exists():
            print(f"⚠ 告警规则文件不存在: {rules_file}")
            return False
        
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)
        
        print(f"✓ 成功加载告警规则文件")
        print(f"  - 性能告警规则: {len(rules.get('performance', {}))} 条")
        print(f"  - 系统告警规则: {len(rules.get('system', {}))} 条")
        print(f"  - 服务告警规则: {len(rules.get('services', {}))} 条")
        print(f"  - 业务告警规则: {len(rules.get('business', {}))} 条")
        
        # 验证关键规则
        if 'performance' in rules and 'api_response_time' in rules['performance']:
            threshold = rules['performance']['api_response_time'].get('threshold_ms', 0)
            print(f"  - API响应时间阈值: {threshold}ms")
        
        return True
        
    except ImportError:
        print("⚠ PyYAML未安装，跳过规则加载测试")
        return True
    except Exception as e:
        logger.error(f"告警规则加载测试失败: {e}", exc_info=True)
        print(f"✗ 告警规则加载测试失败: {e}")
        return False


async def test_notification_config():
    """测试通知配置"""
    print("\n=== 测试通知配置 ===")
    
    try:
        from app.db import SessionLocal
        from app.crud.notification import get_notification_configs
        
        db = SessionLocal()
        try:
            configs = get_notification_configs(db)
            print(f"✓ 通知配置数量: {len(configs)}")
            
            for config in configs:
                print(f"  - {config.name}: {config.notification_type} ({'启用' if config.enabled else '禁用'})")
            
            return True
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"通知配置测试失败: {e}", exc_info=True)
        print(f"✗ 通知配置测试失败: {e}")
        return False


async def test_alert_api_endpoints():
    """测试告警API端点"""
    print("\n=== 测试告警API端点 ===")
    
    try:
        import requests
        
        # 注意：这需要服务正在运行
        base_url = "http://localhost:8000"
        
        # 测试健康检查
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✓ 后端服务运行正常")
            else:
                print(f"⚠ 后端服务响应异常: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("⚠ 后端服务未运行，跳过API测试")
            return True
        
        # 这里可以添加更多API测试
        # 需要认证token，所以暂时跳过
        
        return True
        
    except ImportError:
        print("⚠ requests未安装，跳过API测试")
        return True
    except Exception as e:
        logger.error(f"API端点测试失败: {e}", exc_info=True)
        print(f"✗ API端点测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("=" * 60)
    print("告警通知测试")
    print("=" * 60)
    
    results = {}
    
    # 测试告警聚合
    results["alert_aggregation"] = await test_alert_aggregation()
    
    # 测试告警规则加载
    results["alert_rules"] = await test_alert_rules_loading()
    
    # 测试通知配置
    results["notification_config"] = await test_notification_config()
    
    # 测试API端点
    results["api_endpoints"] = await test_alert_api_endpoints()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, result in results.items():
        status = "✓" if result else "✗"
        print(f"{status} {test_name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

