#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 SSH 连接并保存结果到文件
"""

import subprocess
import sys
from datetime import datetime

def run_test(cmd, description):
    """执行测试并返回结果"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"命令: {cmd}")
    
    full_cmd = f'ssh ubuntu@165.154.233.55 "{cmd}"'
    
    try:
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=30
        )
        
        output = f"""
{'='*60}
{description}
{'='*60}
命令: {cmd}
退出码: {result.returncode}

标准输出:
{result.stdout if result.stdout else '(空)'}

错误输出:
{result.stderr if result.stderr else '(空)'}
"""
        print(output)
        return result.returncode == 0, result.stdout, result.stderr, output
        
    except Exception as e:
        error_msg = f"执行失败: {e}"
        print(error_msg)
        return False, "", str(e), error_msg

def main():
    print("="*60)
    print("SSH 连接和配置测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = []
    
    # 测试列表
    tests = [
        ("echo 'SSH 连接测试成功'", "测试 1: 基本连接"),
        ("whoami && hostname", "测试 2: 系统信息"),
        ("sudo nginx -t", "测试 3: Nginx 配置语法"),
        ("sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc", "测试 4: WebSocket 配置"),
        ("sudo systemctl is-active nginx", "测试 5: Nginx 服务状态"),
        ("sudo systemctl is-active liaotian-backend", "测试 6: 后端服务状态"),
        ("sudo journalctl -u liaotian-backend -n 10 --no-pager | tail -5", "测试 7: 后端日志"),
    ]
    
    for cmd, desc in tests:
        success, stdout, stderr, output = run_test(cmd, desc)
        all_results.append((desc, success, stdout, stderr, output))
    
    # 保存结果到文件
    result_file = "deploy/SSH测试结果.txt"
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("SSH 连接和配置测试结果\n")
        f.write("="*60 + "\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for desc, success, stdout, stderr, output in all_results:
            f.write(output)
            f.write("\n")
        
        # 总结
        f.write("\n" + "="*60 + "\n")
        f.write("测试总结\n")
        f.write("="*60 + "\n")
        for desc, success, stdout, stderr, _ in all_results:
            status = "✓ 成功" if success else "✗ 失败"
            f.write(f"{desc}: {status}\n")
    
    print(f"\n结果已保存到: {result_file}")
    
    # 读取并显示文件内容
    print("\n" + "="*60)
    print("测试结果摘要")
    print("="*60)
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    except Exception as e:
        print(f"读取结果文件失败: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

