#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务状态报告 - 分析服务运行状态和错误
"""

import requests
import sys
import time
from pathlib import Path
import json

# 设置 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent
backend_dir = project_root / "admin-backend"
frontend_dir = project_root / "saas-demo"

def check_backend():
    """检查后端服务"""
    status = {
        'running': False,
        'health': None,
        'errors': [],
        'warnings': []
    }
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            status['running'] = True
            status['health'] = response.json()
        else:
            status['warnings'].append(f"健康检查返回异常状态码: {response.status_code}")
    except requests.exceptions.ConnectionError:
        status['errors'].append("无法连接到后端服务 (http://localhost:8000)")
    except Exception as e:
        status['errors'].append(f"检查后端服务时出错: {e}")
    
    # 检查日志
    log_file = backend_dir / "backend_local.log"
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            errors = [line for line in lines if any(kw in line.lower() for kw in ['error', 'exception', 'failed', 'traceback'])]
            if errors:
                status['errors'].extend([line.rstrip() for line in errors[-5:]])
    
    return status

def check_frontend():
    """检查前端服务"""
    status = {
        'running': False,
        'port': None,
        'errors': [],
        'warnings': []
    }
    
    # 检查端口 3000
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            status['running'] = True
            status['port'] = 3000
        else:
            status['warnings'].append(f"前端服务响应异常: {response.status_code}")
    except requests.exceptions.ConnectionError:
        status['warnings'].append("端口 3000 不可访问")
    
    # 检查端口 3001
    try:
        response = requests.get("http://localhost:3001", timeout=5)
        if response.status_code == 200:
            status['running'] = True
            status['port'] = 3001
        else:
            status['warnings'].append(f"端口 3001 响应异常: {response.status_code}")
    except requests.exceptions.ConnectionError:
        pass
    
    # 检查日志
    log_file = frontend_dir / "frontend_local.log"
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            errors = [line for line in lines if any(kw in line.lower() for kw in ['error', 'exception', 'failed', 'traceback'])]
            if errors:
                status['errors'].extend([line.rstrip() for line in errors[-5:]])
    
    return status

def check_api_endpoints():
    """检查API端点"""
    endpoints = {
        '/health': '健康检查',
        '/docs': 'API文档',
        '/api/v1/users/me': '当前用户信息',
        '/api/v1/auth/login': '登录端点',
    }
    
    results = {}
    for endpoint, desc in endpoints.items():
        try:
            url = f"http://localhost:8000{endpoint}"
            response = requests.get(url, timeout=3)
            results[endpoint] = {
                'status': response.status_code,
                'description': desc,
                'accessible': response.status_code < 500
            }
        except Exception as e:
            results[endpoint] = {
                'status': 'error',
                'description': desc,
                'accessible': False,
                'error': str(e)
            }
    
    return results

def main():
    print("=" * 70)
    print("服务状态报告")
    print("=" * 70)
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 检查后端
    print("后端服务:")
    backend_status = check_backend()
    if backend_status['running']:
        print("  ✓ 运行正常")
        if backend_status['health']:
            print(f"    状态: {backend_status['health'].get('status', 'unknown')}")
    else:
        print("  ✗ 未运行或无法访问")
    
    if backend_status['errors']:
        print(f"\n  发现 {len(backend_status['errors'])} 个错误:")
        for error in backend_status['errors'][:5]:
            print(f"    - {error}")
    
    if backend_status['warnings']:
        print(f"\n  发现 {len(backend_status['warnings'])} 个警告:")
        for warning in backend_status['warnings'][:3]:
            print(f"    - {warning}")
    
    # 检查前端
    print("\n前端服务:")
    frontend_status = check_frontend()
    if frontend_status['running']:
        print(f"  ✓ 运行正常 (端口: {frontend_status['port']})")
    else:
        print("  ✗ 未运行或无法访问")
    
    if frontend_status['errors']:
        print(f"\n  发现 {len(frontend_status['errors'])} 个错误:")
        for error in frontend_status['errors'][:5]:
            print(f"    - {error}")
    
    if frontend_status['warnings']:
        print(f"\n  发现 {len(frontend_status['warnings'])} 个警告:")
        for warning in frontend_status['warnings'][:3]:
            print(f"    - {warning}")
    
    # 检查API端点
    print("\nAPI端点:")
    api_results = check_api_endpoints()
    for endpoint, result in api_results.items():
        if result['accessible']:
            print(f"  ✓ {endpoint:30s} - {result['description']} ({result['status']})")
        else:
            print(f"  ✗ {endpoint:30s} - {result['description']} ({result.get('error', result['status'])})")
    
    # 总结
    print("\n" + "=" * 70)
    print("总结")
    print("=" * 70)
    
    total_errors = len(backend_status['errors']) + len(frontend_status['errors'])
    total_warnings = len(backend_status['warnings']) + len(frontend_status['warnings'])
    
    if total_errors == 0 and total_warnings == 0:
        print("✓ 所有服务运行正常，未发现错误或警告")
    else:
        print(f"发现 {total_errors} 个错误，{total_warnings} 个警告")
        if not backend_status['running']:
            print("\n建议:")
            print("  1. 检查后端服务是否已启动")
            print("  2. 查看后端日志: admin-backend/backend_local.log")
        if not frontend_status['running']:
            print("\n建议:")
            print("  1. 检查前端服务是否已启动")
            print("  2. 检查端口 3000 或 3001 是否被占用")
            print("  3. 查看前端日志: saas-demo/frontend_local.log")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()

