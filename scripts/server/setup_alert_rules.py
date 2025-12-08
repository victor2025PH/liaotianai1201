#!/usr/bin/env python3
"""
配置告警规则和监控阈值
从YAML配置文件加载并应用告警规则
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "admin-backend"))

import yaml
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_alert_rules() -> Dict[str, Any]:
    """加载告警规则配置"""
    rules_file = project_root / "admin-backend" / "app" / "config" / "alert_rules.yaml"
    
    if not rules_file.exists():
        logger.error(f"告警规则文件不存在: {rules_file}")
        return {}
    
    try:
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)
        logger.info(f"成功加载告警规则: {rules_file}")
        return rules
    except Exception as e:
        logger.error(f"加载告警规则失败: {e}", exc_info=True)
        return {}


def print_alert_rules_summary(rules: Dict[str, Any]):
    """打印告警规则摘要"""
    print("\n" + "=" * 60)
    print("告警规则配置摘要")
    print("=" * 60)
    
    # 性能告警
    if 'performance' in rules:
        print("\n📊 性能告警规则:")
        perf_rules = rules['performance']
        for rule_name, rule_config in perf_rules.items():
            enabled = rule_config.get('enabled', False)
            threshold = rule_config.get('threshold_ms') or rule_config.get('threshold', 'N/A')
            severity = rule_config.get('severity', 'N/A')
            status = "✓ 启用" if enabled else "✗ 禁用"
            print(f"  - {rule_name}: {status}, 阈值={threshold}, 严重程度={severity}")
    
    # 系统资源告警
    if 'system' in rules:
        print("\n💻 系统资源告警规则:")
        sys_rules = rules['system']
        for rule_name, rule_config in sys_rules.items():
            enabled = rule_config.get('enabled', False)
            threshold = rule_config.get('threshold_percent', 'N/A')
            severity = rule_config.get('severity', 'N/A')
            status = "✓ 启用" if enabled else "✗ 禁用"
            print(f"  - {rule_name}: {status}, 阈值={threshold}%, 严重程度={severity}")
    
    # 服务健康告警
    if 'services' in rules:
        print("\n🔧 服务健康告警规则:")
        svc_rules = rules['services']
        for rule_name, rule_config in svc_rules.items():
            enabled = rule_config.get('enabled', False)
            severity = rule_config.get('severity', 'N/A')
            status = "✓ 启用" if enabled else "✗ 禁用"
            print(f"  - {rule_name}: {status}, 严重程度={severity}")
    
    # 业务告警
    if 'business' in rules:
        print("\n📈 业务告警规则:")
        biz_rules = rules['business']
        for rule_name, rule_config in biz_rules.items():
            enabled = rule_config.get('enabled', False)
            severity = rule_config.get('severity', 'N/A')
            status = "✓ 启用" if enabled else "✗ 禁用"
            print(f"  - {rule_name}: {status}, 严重程度={severity}")
    
    # 通知配置
    if 'notifications' in rules:
        print("\n📧 通知配置:")
        notif_config = rules['notifications']
        for method, config in notif_config.items():
            enabled = config.get('enabled', False)
            status = "✓ 启用" if enabled else "✗ 禁用"
            levels = config.get('severity_levels', [])
            print(f"  - {method}: {status}, 通知级别={levels}")


def verify_alert_rules(rules: Dict[str, Any]) -> bool:
    """验证告警规则配置"""
    print("\n" + "=" * 60)
    print("验证告警规则配置")
    print("=" * 60)
    
    issues = []
    
    # 检查必需的规则
    required_categories = ['performance', 'system', 'services']
    for category in required_categories:
        if category not in rules:
            issues.append(f"缺少 {category} 告警规则配置")
    
    # 检查性能告警阈值
    if 'performance' in rules:
        perf_rules = rules['performance']
        if 'api_response_time' in perf_rules:
            threshold = perf_rules['api_response_time'].get('threshold_ms')
            if not threshold or threshold <= 0:
                issues.append("API响应时间阈值无效")
    
    # 检查系统资源阈值
    if 'system' in rules:
        sys_rules = rules['system']
        for rule_name, rule_config in sys_rules.items():
            threshold = rule_config.get('threshold_percent')
            if threshold and (threshold < 0 or threshold > 100):
                issues.append(f"{rule_name} 阈值无效 (应在0-100之间)")
    
    if issues:
        print("\n⚠ 发现配置问题:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n✓ 告警规则配置验证通过")
        return True


def main():
    """主函数"""
    print("=" * 60)
    print("告警规则配置工具")
    print("=" * 60)
    
    # 加载规则
    rules = load_alert_rules()
    if not rules:
        print("❌ 无法加载告警规则")
        return 1
    
    # 打印摘要
    print_alert_rules_summary(rules)
    
    # 验证规则
    is_valid = verify_alert_rules(rules)
    
    # 输出建议
    print("\n" + "=" * 60)
    print("配置建议")
    print("=" * 60)
    print("""
1. 根据实际需求调整告警阈值
2. 配置通知渠道（邮件/Telegram/Webhook）
3. 定期检查告警规则的有效性
4. 根据系统负载调整检查间隔

告警规则文件位置: admin-backend/app/config/alert_rules.yaml
    """)
    
    return 0 if is_valid else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)

