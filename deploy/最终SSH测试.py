#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终 SSH 测试 - 直接输出到控制台
"""

import subprocess
import sys
import os

# 确保使用 UTF-8 编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 禁用缓冲
os.environ['PYTHONUNBUFFERED'] = '1'

def test_ssh(cmd, description):
    """执行 SSH 测试"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"命令: {cmd}")
    print("-" * 60)
    sys.stdout.flush()
    
    full_cmd = f'ssh ubuntu@165.154.233.55 "{cmd}"'
    
    try:
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=30
        )
        
        print(f"退出码: {result.returncode}")
        sys.stdout.flush()
        
        if result.stdout:
            print("标准输出:")
            print(result.stdout)
            sys.stdout.flush()
        else:
            print("标准输出: (空)")
            sys.stdout.flush()
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
            sys.stdout.flush()
        else:
            print("错误输出: (空)")
            sys.stdout.flush()
        
        return result.returncode == 0, result.stdout, result.stderr
        
    except Exception as e:
        print(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        return False, "", str(e)

if __name__ == "__main__":
    print("="*60)
    print("SSH 连接测试 - 最终版本")
    print("="*60)
    print(f"Python 版本: {sys.version}")
    print(f"编码: {sys.stdout.encoding}")
    print()
    sys.stdout.flush()
    
    tests = [
        ("echo 'SSH 连接测试成功 - TEST123'", "测试 1: 基本连接"),
        ("whoami", "测试 2: 当前用户"),
        ("hostname", "测试 3: 主机名"),
        ("pwd", "测试 4: 当前目录"),
        ("sudo nginx -t 2>&1", "测试 5: Nginx 配置语法"),
        ("sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1", "测试 6: WebSocket 配置"),
        ("sudo systemctl is-active nginx 2>&1", "测试 7: Nginx 服务状态"),
        ("sudo systemctl is-active liaotian-backend 2>&1", "测试 8: 后端服务状态"),
    ]
    
    results = []
    for cmd, desc in tests:
        success, stdout, stderr = test_ssh(cmd, desc)
        results.append((desc, success, bool(stdout or stderr)))
    
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"{'测试项':<25} {'成功':<8} {'有输出':<8}")
    print("-" * 60)
    for desc, success, has_output in results:
        status = "✓" if success else "✗"
        output_status = "✓" if has_output else "✗"
        print(f"{desc:<25} {status:<8} {output_status:<8}")
    print("="*60)
    sys.stdout.flush()

