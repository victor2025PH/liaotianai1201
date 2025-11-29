#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 SSH 连接并将结果写入文件
"""

import subprocess
import sys
from datetime import datetime

output_file = "deploy/SSH测试结果_详细.txt"

def run_test(cmd, description, f):
    """执行测试并写入文件"""
    f.write(f"\n{'='*60}\n")
    f.write(f"{description}\n")
    f.write(f"{'='*60}\n")
    f.write(f"命令: {cmd}\n")
    f.write("-" * 60 + "\n")
    f.flush()
    
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
        
        f.write(f"退出码: {result.returncode}\n\n")
        
        if result.stdout:
            f.write("标准输出:\n")
            f.write(result.stdout)
            f.write("\n")
        else:
            f.write("标准输出: (空)\n")
        
        if result.stderr:
            f.write("\n错误输出:\n")
            f.write(result.stderr)
            f.write("\n")
        else:
            f.write("错误输出: (空)\n")
        
        f.flush()
        return result.returncode == 0, result.stdout, result.stderr
        
    except Exception as e:
        error_msg = f"执行失败: {e}\n"
        f.write(error_msg)
        f.flush()
        return False, "", str(e)

def main():
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("SSH 连接测试结果\n")
        f.write("="*60 + "\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Python 版本: {sys.version}\n\n")
        f.flush()
        
        results = []
        
        tests = [
            ("echo 'SSH 连接测试成功 - TEST123'", "测试 1: 基本连接"),
            ("whoami", "测试 2: 当前用户"),
            ("hostname", "测试 3: 主机名"),
            ("pwd", "测试 4: 当前目录"),
            ("sudo nginx -t 2>&1", "测试 5: Nginx 配置语法"),
            ("sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1", "测试 6: WebSocket 配置"),
            ("sudo systemctl is-active nginx 2>&1", "测试 7: Nginx 服务状态"),
            ("sudo systemctl is-active liaotian-backend 2>&1", "测试 8: 后端服务状态"),
            ("sudo journalctl -u liaotian-backend -n 5 --no-pager 2>&1", "测试 9: 后端日志"),
        ]
        
        for cmd, desc in tests:
            success, stdout, stderr = run_test(cmd, desc, f)
            results.append((desc, success, stdout, stderr))
        
        # 总结
        f.write("\n" + "="*60 + "\n")
        f.write("测试总结\n")
        f.write("="*60 + "\n")
        f.write(f"{'测试项':<25} {'成功':<8} {'有输出':<8}\n")
        f.write("-" * 60 + "\n")
        
        for desc, success, stdout, stderr in results:
            status = "✓" if success else "✗"
            has_output = "✓" if (stdout or stderr) else "✗"
            f.write(f"{desc:<25} {status:<8} {has_output:<8}\n")
        
        f.write("="*60 + "\n")
        f.write("测试完成\n")
        f.write("="*60 + "\n")
        f.flush()
    
    # 读取并显示文件内容
    print(f"测试结果已保存到: {output_file}")
    print("\n" + "="*60)
    print("测试结果:")
    print("="*60)
    
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    except Exception as e:
        print(f"读取结果文件失败: {e}")

if __name__ == "__main__":
    main()

