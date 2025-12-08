#!/usr/bin/env python3
"""
性能基准测试脚本
建立系统性能基线，用于后续性能对比
"""
import sys
import os
import time
import statistics
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import json

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "admin-backend"))

import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 测试用的认证token
AUTH_TOKEN = None


def login() -> str:
    """登录获取token"""
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        response = requests.post(
            f"{API_BASE}/auth/login",
            data={
                "username": settings.admin_default_email,
                "password": settings.admin_default_password
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            logger.warning(f"登录失败: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"登录异常: {e}")
        return None


def benchmark_endpoint(
    method: str,
    endpoint: str,
    headers: dict = None,
    data: dict = None,
    iterations: int = 10
) -> Dict[str, Any]:
    """基准测试单个端点"""
    times = []
    errors = 0
    
    for i in range(iterations):
        try:
            start = time.time()
            if method.upper() == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", headers=headers, json=data, timeout=10)
            else:
                continue
            
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            if response.status_code >= 400:
                errors += 1
                
        except Exception as e:
            logger.warning(f"请求失败: {e}")
            errors += 1
    
    if not times:
        return {
            "endpoint": endpoint,
            "method": method,
            "error": "所有请求都失败"
        }
    
    return {
        "endpoint": endpoint,
        "method": method,
        "iterations": iterations,
        "success_count": len(times),
        "error_count": errors,
        "min_ms": min(times),
        "max_ms": max(times),
        "avg_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "p95_ms": sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0],
        "p99_ms": sorted(times)[int(len(times) * 0.99)] if len(times) > 1 else times[0],
        "std_dev": statistics.stdev(times) if len(times) > 1 else 0
    }


def run_benchmark_suite(token: str) -> Dict[str, Any]:
    """运行完整的基准测试套件"""
    print("\n" + "=" * 60)
    print("运行性能基准测试")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "endpoints": []
    }
    
    # 测试端点列表
    test_endpoints = [
        ("GET", "/health", None, None),
        ("GET", "/healthz", None, None),
        ("GET", "/api/v1/group-ai/dashboard", headers, None),
        ("GET", "/api/v1/group-ai/scripts", headers, None),
        ("GET", "/api/v1/group-ai/accounts", headers, None),
        ("GET", "/api/v1/group-ai/monitor/accounts/metrics", headers, None),
        ("GET", "/api/v1/system/performance", headers, None),
    ]
    
    for method, endpoint, endpoint_headers, data in test_endpoints:
        print(f"\n测试: {method} {endpoint}")
        result = benchmark_endpoint(method, endpoint, endpoint_headers, data, iterations=10)
        results["endpoints"].append(result)
        
        if "error" in result:
            print(f"  ✗ {result['error']}")
        else:
            print(f"  ✓ 平均响应时间: {result['avg_ms']:.2f}ms")
            print(f"    最小: {result['min_ms']:.2f}ms, 最大: {result['max_ms']:.2f}ms")
            print(f"    P95: {result['p95_ms']:.2f}ms, P99: {result['p99_ms']:.2f}ms")
    
    return results


def save_benchmark_results(results: Dict[str, Any], output_file: Path):
    """保存基准测试结果"""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ 基准测试结果已保存: {output_file}")


def compare_with_baseline(current: Dict[str, Any], baseline_file: Path) -> Dict[str, Any]:
    """与基线对比"""
    if not baseline_file.exists():
        print("\n⚠ 未找到基线文件，跳过对比")
        return {}
    
    try:
        with open(baseline_file, 'r', encoding='utf-8') as f:
            baseline = json.load(f)
        
        print("\n" + "=" * 60)
        print("与基线对比")
        print("=" * 60)
        
        comparison = {}
        
        # 创建端点映射
        baseline_map = {ep["endpoint"]: ep for ep in baseline.get("endpoints", [])}
        current_map = {ep["endpoint"]: ep for ep in current.get("endpoints", [])}
        
        for endpoint, current_result in current_map.items():
            if endpoint not in baseline_map:
                continue
            
            baseline_result = baseline_map[endpoint]
            if "error" in current_result or "error" in baseline_result:
                continue
            
            current_avg = current_result.get("avg_ms", 0)
            baseline_avg = baseline_result.get("avg_ms", 0)
            
            if baseline_avg > 0:
                diff_percent = ((current_avg - baseline_avg) / baseline_avg) * 100
                comparison[endpoint] = {
                    "baseline_ms": baseline_avg,
                    "current_ms": current_avg,
                    "diff_percent": diff_percent,
                    "status": "improved" if diff_percent < -5 else "degraded" if diff_percent > 5 else "stable"
                }
                
                status_icon = "✓" if diff_percent < -5 else "✗" if diff_percent > 5 else "="
                print(f"\n{status_icon} {endpoint}")
                print(f"  基线: {baseline_avg:.2f}ms")
                print(f"  当前: {current_avg:.2f}ms")
                print(f"  变化: {diff_percent:+.1f}%")
        
        return comparison
        
    except Exception as e:
        logger.error(f"对比失败: {e}", exc_info=True)
        return {}


def main():
    """主函数"""
    print("=" * 60)
    print("性能基准测试")
    print("=" * 60)
    
    # 登录获取token
    print("\n正在登录...")
    token = login()
    if not token:
        print("⚠ 无法获取认证token，部分测试将跳过")
        token = None
    
    # 运行基准测试
    results = run_benchmark_suite(token)
    
    # 保存结果
    output_dir = Path(__file__).parent.parent.parent / "admin-backend" / "benchmarks"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"benchmark_{timestamp}.json"
    save_benchmark_results(results, output_file)
    
    # 查找基线文件
    baseline_file = output_dir / "baseline.json"
    
    # 如果不存在基线，询问是否设置为基线
    if not baseline_file.exists():
        set_baseline = input("\n是否将此结果设置为基线? (yes/no): ").strip().lower()
        if set_baseline in ['yes', 'y']:
            baseline_file.parent.mkdir(parents=True, exist_ok=True)
            with open(baseline_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"✓ 已设置为基线: {baseline_file}")
    else:
        # 与基线对比
        comparison = compare_with_baseline(results, baseline_file)
        
        # 询问是否更新基线
        update_baseline = input("\n是否更新基线? (yes/no): ").strip().lower()
        if update_baseline in ['yes', 'y']:
            with open(baseline_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"✓ 基线已更新: {baseline_file}")
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    total_endpoints = len(results["endpoints"])
    successful = sum(1 for ep in results["endpoints"] if "error" not in ep)
    
    print(f"\n测试端点数: {total_endpoints}")
    print(f"成功: {successful}")
    print(f"失败: {total_endpoints - successful}")
    
    if successful > 0:
        avg_times = [ep["avg_ms"] for ep in results["endpoints"] if "error" not in ep]
        overall_avg = statistics.mean(avg_times)
        print(f"\n总体平均响应时间: {overall_avg:.2f}ms")
    
    print(f"\n结果文件: {output_file}")
    if baseline_file.exists():
        print(f"基线文件: {baseline_file}")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)

