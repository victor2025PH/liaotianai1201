#!/usr/bin/env python3
"""修复 Query 导入"""
import sys
import os

main_file = "/home/ubuntu/admin-backend/app/main.py"

if not os.path.exists(main_file):
    print(f"✗ 文件不存在: {main_file}")
    sys.exit(1)

with open(main_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

if len(lines) == 0:
    print("✗ 文件为空")
    sys.exit(1)

first_line = lines[0]
print(f"当前第一行: {first_line.strip()}")

if "Query" not in first_line:
    lines[0] = first_line.replace(
        "from fastapi import FastAPI, Request",
        "from fastapi import FastAPI, Request, Query"
    )
    with open(main_file, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("✓ Query 已添加")
    print(f"新第一行: {lines[0].strip()}")
else:
    print("✓ Query 已存在")
    print(f"第一行: {first_line.strip()}")

