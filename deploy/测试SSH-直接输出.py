#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys
import io

# 设置标准输出为无缓冲
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

print("="*60)
print("SSH 连接测试 - 直接输出")
print("="*60)
print()

# 测试 1
print("测试 1: 基本连接")
print("-" * 60)
proc = subprocess.Popen(
    'ssh ubuntu@165.154.233.55 "echo TEST123"',
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8',
    bufsize=0
)
stdout, stderr = proc.communicate()
print(f"退出码: {proc.returncode}")
print(f"输出: {stdout}")
if stderr:
    print(f"错误: {stderr}")
print()

# 测试 2
print("测试 2: 系统信息")
print("-" * 60)
proc = subprocess.Popen(
    'ssh ubuntu@165.154.233.55 "whoami && hostname"',
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8',
    bufsize=0
)
stdout, stderr = proc.communicate()
print(f"退出码: {proc.returncode}")
print(f"输出: {stdout}")
if stderr:
    print(f"错误: {stderr}")
print()

# 测试 3
print("测试 3: Nginx 配置")
print("-" * 60)
proc = subprocess.Popen(
    'ssh ubuntu@165.154.233.55 "sudo nginx -t"',
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8',
    bufsize=0
)
stdout, stderr = proc.communicate()
print(f"退出码: {proc.returncode}")
print(f"输出: {stdout}")
if stderr:
    print(f"错误: {stderr}")
print()

# 测试 4
print("测试 4: WebSocket 配置")
print("-" * 60)
proc = subprocess.Popen(
    'ssh ubuntu@165.154.233.55 "sudo grep -A 10 location /api/v1/notifications/ws /etc/nginx/sites-available/aikz.usdt2026.cc"',
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8',
    bufsize=0
)
stdout, stderr = proc.communicate()
print(f"退出码: {proc.returncode}")
if stdout:
    print(f"输出:\n{stdout}")
else:
    print("输出: (未找到配置)")
if stderr:
    print(f"错误: {stderr}")
print()

print("="*60)
print("测试完成")
print("="*60)

