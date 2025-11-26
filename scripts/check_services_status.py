#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查服务状态并分析错误
"""

import requests
import sys
import time
from pathlib import Path

# 设置 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_backend():
    """检查后端服务"""
    print("=" * 70)
    print("检查后端服务")
    print("=" * 70)
    
    try:
        # 健康检查
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("[OK] 后端服务运行正常")
            print(f"    响应: {response.json()}")
        else:
            print(f"[WARNING] 后端服务响应异常: {response.status_code}")
            print(f"    响应内容: {response.text[:200]}")
    except requests.exceptions.ConnectionError:
        print("[ERROR] 无法连接到后端服务 (http://localhost:8000)")
        print("        可能原因:")
        print("        1. 后端服务未启动")
        print("        2. 端口被占用")
        print("        3. 服务启动失败")
    except Exception as e:
        print(f"[ERROR] 检查后端服务时出错: {e}")
    
    # 检查日志文件
    log_file = Path(__file__).parent.parent / "admin-backend" / "backend_local.log"
    if log_file.exists():
        print(f"\n后端日志文件: {log_file}")
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            if lines:
                print(f"    最后10行日志:")
                for line in lines[-10:]:
                    print(f"    {line.rstrip()}")
                
                # 查找错误
                errors = [line for line in lines if any(kw in line.lower() for kw in ['error', 'exception', 'failed', 'traceback'])]
                if errors:
                    print(f"\n    [发现 {len(errors)} 个错误]")
                    for error in errors[-5:]:
                        print(f"    {error.rstrip()}")
            else:
                print("    日志文件为空")

def check_frontend():
    """检查前端服务"""
    print("\n" + "=" * 70)
    print("检查前端服务")
    print("=" * 70)
    
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("[OK] 前端服务运行正常")
        else:
            print(f"[WARNING] 前端服务响应异常: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("[ERROR] 无法连接到前端服务 (http://localhost:3000)")
        print("        可能原因:")
        print("        1. 前端服务未启动")
        print("        2. 端口被占用")
        print("        3. 服务启动失败")
    except Exception as e:
        print(f"[ERROR] 检查前端服务时出错: {e}")
    
    # 检查日志文件
    log_file = Path(__file__).parent.parent / "saas-demo" / "frontend_local.log"
    if log_file.exists():
        print(f"\n前端日志文件: {log_file}")
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            if lines:
                print(f"    最后10行日志:")
                for line in lines[-10:]:
                    print(f"    {line.rstrip()}")
                
                # 查找错误
                errors = [line for line in lines if any(kw in line.lower() for kw in ['error', 'exception', 'failed', 'traceback'])]
                if errors:
                    print(f"\n    [发现 {len(errors)} 个错误]")
                    for error in errors[-5:]:
                        print(f"    {error.rstrip()}")
            else:
                print("    日志文件为空")

def check_api_endpoints():
    """检查API端点"""
    print("\n" + "=" * 70)
    print("检查API端点")
    print("=" * 70)
    
    endpoints = [
        ("/health", "健康检查"),
        ("/docs", "API文档"),
        ("/api/auth/me", "用户信息"),
    ]
    
    for endpoint, desc in endpoints:
        try:
            url = f"http://localhost:8000{endpoint}"
            response = requests.get(url, timeout=3)
            status = "✓" if response.status_code < 400 else "✗"
            print(f"  {status} {endpoint:30s} ({desc}) - {response.status_code}")
        except Exception as e:
            print(f"  ✗ {endpoint:30s} ({desc}) - 无法访问: {e}")

def main():
    print("=" * 70)
    print("服务状态检查")
    print("=" * 70)
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    check_backend()
    check_frontend()
    check_api_endpoints()
    
    print("\n" + "=" * 70)
    print("检查完成")
    print("=" * 70)

if __name__ == "__main__":
    main()

