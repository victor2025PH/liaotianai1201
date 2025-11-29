#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys

print("开始测试...")
print("=" * 60)

# 测试 1
print("\n测试 1: 基本连接")
r1 = subprocess.run('ssh ubuntu@165.154.233.55 "echo TEST123"', shell=True, capture_output=True, text=True, encoding='utf-8')
print(f"退出码: {r1.returncode}")
print(f"输出: {repr(r1.stdout)}")
print(f"错误: {repr(r1.stderr)}")

# 测试 2
print("\n测试 2: Nginx 配置")
r2 = subprocess.run('ssh ubuntu@165.154.233.55 "sudo nginx -t"', shell=True, capture_output=True, text=True, encoding='utf-8')
print(f"退出码: {r2.returncode}")
print(f"输出: {r2.stdout[:500] if r2.stdout else '(空)'}")
print(f"错误: {r2.stderr[:500] if r2.stderr else '(空)'}")

# 测试 3
print("\n测试 3: WebSocket 配置")
r3 = subprocess.run('ssh ubuntu@165.154.233.55 "sudo grep -A 10 location /api/v1/notifications/ws /etc/nginx/sites-available/aikz.usdt2026.cc"', shell=True, capture_output=True, text=True, encoding='utf-8')
print(f"退出码: {r3.returncode}")
print(f"输出: {r3.stdout if r3.stdout else '(未找到)'}")
print(f"错误: {r3.stderr if r3.stderr else '(无)'}")

print("\n" + "=" * 60)
print("测试完成")

