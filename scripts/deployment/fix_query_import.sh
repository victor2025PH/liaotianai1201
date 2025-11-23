#!/bin/bash
# 修复 Query 导入

cd /home/ubuntu/admin-backend

echo "=== 修复 Query 导入 ==="
sed -i '1s/from fastapi import FastAPI, Request$/from fastapi import FastAPI, Request, Query/' app/main.py

echo "=== 验证修复 ==="
head -1 app/main.py

echo "✓ Query 导入已修复"


