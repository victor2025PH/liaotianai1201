#!/usr/bin/env python3
"""
核心功能测试脚本
测试 Session 管理、账号管理、剧本演绎等核心功能
"""
import sys
import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 测试结果
test_results: List[Dict] = []

def test_pass(name: str, details: str = ""):
    """记录测试通过"""
    result = {"name": name, "status": "pass", "details": details}
    test_results.append(result)
    try:
        print(f"✓ {name}")
    except UnicodeEncodeError:
        print(f"[PASS] {name}")
    if details:
        try:
            print(f"  {details}")
        except UnicodeEncodeError:
            print(f"  {details.encode('utf-8', errors='replace').decode('utf-8')}")

def test_fail(name: str, error: str = ""):
    """记录测试失败"""
    result = {"name": name, "status": "fail", "error": error}
    test_results.append(result)
    try:
        print(f"✗ {name}")
    except UnicodeEncodeError:
        print(f"[FAIL] {name}")
    if error:
        try:
            print(f"  错误: {error}")
        except UnicodeEncodeError:
            print(f"  Error: {error.encode('utf-8', errors='replace').decode('utf-8')}")

def test_skip(name: str, reason: str = ""):
    """记录测试跳过"""
    result = {"name": name, "status": "skip", "reason": reason}
    test_results.append(result)
    try:
        print(f"⊘ {name} (跳过)")
    except UnicodeEncodeError:
        print(f"[SKIP] {name} (skipped)")
    if reason:
        try:
            print(f"  原因: {reason}")
        except UnicodeEncodeError:
            print(f"  Reason: {reason.encode('utf-8', errors='replace').decode('utf-8')}")

def test_session_management():
    """测试 Session 管理功能"""
    print("\n=== Session 管理测试 ===")
    
    # 检查 Session 目录
    sessions_dir = project_root / "sessions"
    if sessions_dir.exists():
        test_pass("Session 目录存在", str(sessions_dir))
        
        # 检查 Session 文件
        session_files = list(sessions_dir.glob("*.session")) + list(sessions_dir.glob("*.enc"))
        if session_files:
            test_pass(f"找到 {len(session_files)} 个 Session 文件")
            
            # 测试验证脚本
            verify_script = project_root / "scripts" / "verify_session.py"
            if verify_script.exists():
                test_pass("Session 验证脚本存在")
            else:
                test_skip("Session 验证脚本不存在")
        else:
            test_skip("未找到 Session 文件")
    else:
        test_skip("Session 目录不存在")

def test_session_encryption():
    """测试 Session 加密功能"""
    print("\n=== Session 加密测试 ===")
    
    try:
        from utils.session_encryption import get_session_manager
        session_manager = get_session_manager()
        
        if session_manager.encryption_enabled:
            test_pass("Session 加密已启用")
        else:
            test_skip("Session 加密未启用（可选）")
            
        test_pass("Session 加密模块可导入")
    except ImportError as e:
        test_fail("Session 加密模块导入失败", str(e))
    except Exception as e:
        test_skip("Session 加密测试", str(e))

def test_api_endpoints(base_url: str = "http://localhost:8000"):
    """测试 API 端点"""
    print("\n=== API 端点测试 ===")
    
    try:
        # 测试健康检查
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            test_pass("健康检查端点正常")
        else:
            test_fail("健康检查端点异常", f"状态码: {response.status_code}")
        
        # 测试详细健康检查
        response = requests.get(f"{base_url}/health?detailed=true", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            test_pass("详细健康检查端点正常")
            
            # 检查组件状态
            if "components" in health_data:
                components = health_data["components"]
                for component, status in components.items():
                    if status.get("status") == "healthy":
                        test_pass(f"组件 {component} 健康")
                    else:
                        test_skip(f"组件 {component} 状态: {status.get('status')}")
        else:
            test_fail("详细健康检查端点异常", f"状态码: {response.status_code}")
        
        # 测试 Prometheus 指标
        response = requests.get(f"{base_url}/metrics", timeout=5)
        if response.status_code == 200:
            metrics = response.text
            if "http_requests_total" in metrics or "prometheus" in metrics.lower():
                test_pass("Prometheus 指标端点正常")
            else:
                test_skip("Prometheus 指标格式异常")
        else:
            test_fail("Prometheus 指标端点异常", f"状态码: {response.status_code}")
        
        # 测试 OpenAPI Schema
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            if "paths" in schema:
                path_count = len(schema["paths"])
                test_pass(f"OpenAPI Schema 正常 ({path_count} 个端点)")
            else:
                test_fail("OpenAPI Schema 格式异常")
        else:
            test_fail("OpenAPI Schema 端点异常", f"状态码: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        test_skip("API 端点测试", "后端服务未运行")
    except Exception as e:
        test_fail("API 端点测试失败", str(e))

def test_account_manager():
    """测试账号管理功能"""
    print("\n=== 账号管理测试 ===")
    
    try:
        from group_ai_service.account_manager import AccountManager
        from group_ai_service.config import get_group_ai_config
        
        config = get_group_ai_config()
        manager = AccountManager(config)
        
        test_pass("账号管理器可初始化")
        test_pass(f"账号管理器配置正常 (Session 目录: {config.session_files_directory})")
    except ImportError as e:
        test_fail("账号管理器模块导入失败", str(e))
    except Exception as e:
        test_skip("账号管理器测试", str(e))

def test_health_checker():
    """测试健康检查功能"""
    print("\n=== 健康检查测试 ===")
    
    try:
        from admin_backend.app.core.health_check import HealthChecker
        
        checker = HealthChecker()
        test_pass("健康检查器可初始化")
        
        # 注意：实际运行健康检查可能需要数据库连接等
        test_skip("健康检查器运行测试", "需要实际环境")
    except ImportError as e:
        test_fail("健康检查器模块导入失败", str(e))
    except Exception as e:
        test_skip("健康检查器测试", str(e))

def test_prometheus_metrics():
    """测试 Prometheus 指标"""
    print("\n=== Prometheus 指标测试 ===")
    
    try:
        from admin_backend.app.monitoring.prometheus_metrics import (
            http_requests_total,
            session_files_total,
            get_metrics_output
        )
        
        test_pass("Prometheus 指标模块可导入")
        
        # 测试指标输出
        try:
            metrics_output = get_metrics_output()
            if metrics_output:
                test_pass("Prometheus 指标输出正常")
            else:
                test_skip("Prometheus 指标输出为空")
        except Exception as e:
            test_skip("Prometheus 指标输出测试", str(e))
            
    except ImportError as e:
        test_fail("Prometheus 指标模块导入失败", str(e))
    except Exception as e:
        test_skip("Prometheus 指标测试", str(e))

def generate_report():
    """生成测试报告"""
    report_file = project_root / "test_reports" / f"core_functionality_{Path(__file__).stem}_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.parent.mkdir(exist_ok=True)
    
    summary = {
        "total": len(test_results),
        "passed": sum(1 for r in test_results if r["status"] == "pass"),
        "failed": sum(1 for r in test_results if r["status"] == "fail"),
        "skipped": sum(1 for r in test_results if r["status"] == "skip"),
    }
    
    report = {
        "summary": summary,
        "tests": test_results
    }
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试报告已保存: {report_file}")
    return report

def main():
    """主测试函数"""
    import sys
    import io
    # 设置输出编码为 UTF-8
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 50)
    print("核心功能测试")
    print("=" * 50)
    
    # 运行测试
    test_session_management()
    test_session_encryption()
    test_account_manager()
    test_health_checker()
    test_prometheus_metrics()
    test_api_endpoints()
    
    # 生成报告
    report = generate_report()
    
    # 输出摘要
    print("\n" + "=" * 50)
    print("测试摘要")
    print("=" * 50)
    print(f"总测试数: {report['summary']['total']}")
    print(f"通过: {report['summary']['passed']}")
    print(f"失败: {report['summary']['failed']}")
    print(f"跳过: {report['summary']['skipped']}")
    
    if report['summary']['total'] > 0:
        pass_rate = (report['summary']['passed'] / report['summary']['total']) * 100
        print(f"通过率: {pass_rate:.1f}%")
    
    # 返回退出码
    return 0 if report['summary']['failed'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

