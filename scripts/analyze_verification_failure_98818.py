#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析验证码 98818 验证失败的原因
"""
import sqlite3
import sys
import io
from pathlib import Path
from datetime import datetime

# 设置标准输出为UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 项目根目录
project_root = Path(__file__).parent.parent
db_path = project_root / "admin-backend" / "admin.db"

phone = "+639542360349"
code = "98818"

print("=" * 70)
print("  分析验证码验证失败原因")
print("=" * 70)
print(f"\n问题信息：")
print(f"   - 验证码: {code}")
print(f"   - 手机号: {phone}")
print(f"   - 选择的服务器: 第二个服务器")
print(f"   - 错误: 验证码无效")
print("\n正在查询数据库记录...\n")

if not db_path.exists():
    print(f"❌ 数据库文件不存在: {db_path}")
    sys.exit(1)

conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 查询所有相关记录
cursor.execute("""
    SELECT 
        id,
        phone,
        node_id,
        status,
        phone_code_hash,
        error_message,
        retry_count,
        created_at,
        updated_at
    FROM user_registrations
    WHERE phone = ?
    ORDER BY created_at DESC
    LIMIT 10
""", (phone,))

records = cursor.fetchall()

if not records:
    print(f"未找到手机号 {phone} 的注册记录")
    conn.close()
    sys.exit(1)

print(f"找到 {len(records)} 条记录：\n")
print("-" * 70)

for i, record in enumerate(records, 1):
    print(f"\n记录 #{i}:")
    print(f"   ID: {record['id']}")
    print(f"   手机号: {record['phone']}")
    print(f"   服务器: {record['node_id']}")
    print(f"   状态: {record['status']}")
    print(f"   phone_code_hash: {record['phone_code_hash']}")
    print(f"   错误信息: {record['error_message'] or '(无)'}")
    print(f"   重试次数: {record['retry_count']}")
    print(f"   创建时间: {record['created_at']}")
    print(f"   更新时间: {record['updated_at']}")
    
    # 计算时间差
    if record['updated_at']:
        try:
            updated = datetime.fromisoformat(record['updated_at'].replace('Z', '+00:00'))
            now = datetime.utcnow()
            if updated.tzinfo:
                now = datetime.now(updated.tzinfo)
            diff = (now - updated.replace(tzinfo=None)).total_seconds() / 60
            print(f"   距离现在: {diff:.1f} 分钟")
        except:
            pass

print("\n" + "=" * 70)
print("  分析结果")
print("=" * 70)

# 分析最新记录
latest = records[0]
print(f"\n最新记录分析：")
print(f"   - 服务器: {latest['node_id']}")
print(f"   - 状态: {latest['status']}")
print(f"   - phone_code_hash: {latest['phone_code_hash']}")

# 检查是否有多个服务器的记录
servers = set(r['node_id'] for r in records if r['node_id'])
if len(servers) > 1:
    print(f"\n[警告] 发现多个服务器的记录：")
    for server in servers:
        server_records = [r for r in records if r['node_id'] == server]
        latest_server = max(server_records, key=lambda x: x['created_at'])
        print(f"   - {server}: {len(server_records)} 条记录, 最新状态={latest_server['status']}, hash={latest_server['phone_code_hash']}")
    
    # 检查是否有 code_sent 状态的记录
    code_sent_records = [r for r in records if r['status'] == 'code_sent' and r['phone_code_hash']]
    if code_sent_records:
        print(f"\n[发现] {len(code_sent_records)} 条 code_sent 状态的记录：")
        for r in code_sent_records:
            print(f"   - 服务器: {r['node_id']}, hash: {r['phone_code_hash']}, 更新时间: {r['updated_at']}")
        
        # 检查是否在错误的服务器上验证
        if latest['status'] != 'code_sent' or latest['node_id'] != code_sent_records[0]['node_id']:
            print(f"\n[错误] 可能的问题：")
            print(f"   - 验证码是在服务器 {code_sent_records[0]['node_id']} 上发送的")
            print(f"   - 但验证是在服务器 {latest['node_id']} 上进行的")
            print(f"   - phone_code_hash 不匹配，导致验证失败")
    else:
        print(f"\n[警告] 没有找到 code_sent 状态的记录")
        print(f"   - 可能所有记录都已过期或失败")

# 检查错误信息
if latest['error_message']:
    print(f"\n[错误] 错误信息: {latest['error_message']}")

# 检查时间
if latest['updated_at']:
    try:
        updated = datetime.fromisoformat(latest['updated_at'].replace('Z', '+00:00'))
        now = datetime.utcnow()
        if updated.tzinfo:
            now = datetime.now(updated.tzinfo)
        diff = (now - updated.replace(tzinfo=None)).total_seconds() / 60
        if diff > 10:
            print(f"\n[警告] 记录已过期: {diff:.1f} 分钟前更新（超过10分钟）")
    except:
        pass

print("\n" + "=" * 70)
conn.close()

