#!/usr/bin/env python3
"""修复 Query 导入"""
import sys

main_file = sys.argv[1] if len(sys.argv) > 1 else "app/main.py"

with open(main_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

if "Query" not in lines[0]:
    lines[0] = lines[0].replace(
        "from fastapi import FastAPI, Request",
        "from fastapi import FastAPI, Request, Query"
    )
    with open(main_file, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("✓ Query 已添加")
    print(f"第一行: {lines[0].strip()}")
else:
    print("✓ Query 已存在")
    print(f"第一行: {lines[0].strip()}")


