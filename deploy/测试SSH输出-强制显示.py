#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 SSH 连接并强制显示输出
"""

import subprocess
import sys
import os
from datetime import datetime

# 强制刷新输出
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 禁用 Python 的输出缓冲
os.environ['PYTHONUNBUFFERED'] = '1'

def run_test(cmd, description):
    """执行测试并强制输出"""
    print(f"\n{'='*60}", flush=True)
    print(f"{description}", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"命令: {cmd}", flush=True)
    print("-" * 60, flush=True)
    
    full_cmd = f'ssh ubuntu@165.154.233.55 "{cmd}"'
    
    try:
        # 使用 Popen 实时输出
        process = subprocess.Popen(
            full_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1
        )
        
        stdout_lines = []
        stderr_lines = []
        
        # 实时读取输出
        import select
        import threading
        
        def read_output(pipe, lines, label):
            try:
                for line in iter(pipe.readline, ''):
                    if line:
                        line = line.rstrip()
                        lines.append(line)
                        print(f"[{label}] {line}", flush=True)
            except Exception as e:
                print(f"[{label} 错误] {e}", flush=True)
        
        stdout_thread = threading.Thread(target=read_output, args=(process.stdout, stdout_lines, "STDOUT"))
        stderr_thread = threading.Thread(target=read_output, args=(process.stderr, stderr_lines, "STDERR"))
        
        stdout_thread.start()
        stderr_thread.start()
        
        # 等待进程完成
        return_code = process.wait()
        
        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)
        
        stdout = '\n'.join(stdout_lines)
        stderr = '\n'.join(stderr_lines)
        
        print("-" * 60, flush=True)
        print(f"退出码: {return_code}", flush=True)
        print(f"标准输出行数: {len(stdout_lines)}", flush=True)
        print(f"错误输出行数: {len(stderr_lines)}", flush=True)
        
        if not stdout and not stderr:
            print("⚠️  警告: 没有任何输出", flush=True)
        
        return return_code == 0, stdout, stderr
        
    except Exception as e:
        error_msg = f"执行失败: {e}"
        print(error_msg, flush=True)
        import traceback
        traceback.print_exc()
        return False, "", str(e)

def main():
    print("="*60, flush=True)
    print("SSH 连接测试 - 强制显示输出", flush=True)
    print("="*60, flush=True)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"Python 版本: {sys.version}", flush=True)
    print(f"编码: {sys.stdout.encoding}", flush=True)
    print()
    
    results = []
    
    # 测试列表
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
    
    for cmd, desc in tests:
        success, stdout, stderr = run_test(cmd, desc)
        results.append((desc, success, stdout, stderr))
        print()  # 空行分隔
    
    # 总结
    print("\n" + "="*60, flush=True)
    print("测试总结", flush=True)
    print("="*60, flush=True)
    print(f"{'测试项':<25} {'成功':<8} {'有输出':<8}", flush=True)
    print("-" * 60, flush=True)
    
    all_success = True
    for desc, success, stdout, stderr in results:
        status = "✓" if success else "✗"
        has_output = "✓" if (stdout or stderr) else "✗"
        print(f"{desc:<25} {status:<8} {has_output:<8}", flush=True)
        if not success:
            all_success = False
    
    print("-" * 60, flush=True)
    
    if all_success:
        print("\n✅ 所有测试通过！", flush=True)
    else:
        print("\n⚠️  部分测试失败", flush=True)
    
    print("\n" + "="*60, flush=True)
    print("测试完成", flush=True)
    print("="*60, flush=True)
    
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())

