#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析验证码验证时间线
"""
import requests
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin@example.com"
PASSWORD = "changeme123"

def login():
    """登录获取token"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": USERNAME, "password": PASSWORD},
            timeout=5
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Login failed: {e}")
        return None

def get_all_registrations(token, phone):
    """获取所有注册记录"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 尝试通过数据库查询（如果有API）
    # 这里我们需要直接查询数据库或通过其他方式获取
    
    # 先尝试获取最近的注册记录
    registrations = []
    
    # 由于没有直接的list API，我们需要通过其他方式
    # 或者检查数据库文件
    
    return registrations

def analyze_timing(phone="+639542360349"):
    """分析验证时间线"""
    print("=" * 80)
    print("Verification Timing Analysis")
    print("=" * 80)
    print(f"Phone: {phone}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    token = login()
    if not token:
        print("ERROR: Failed to login")
        return
    
    print("OK: Login successful")
    print()
    
    # Check database directly
    print("=" * 80)
    print("Checking Database Records")
    print("=" * 80)
    
    try:
        import sqlite3
        from pathlib import Path
        
        # Find database file
        db_paths = [
            Path("admin-backend/data/app.db"),
            Path("admin-backend/app.db"),
            Path("data/app.db"),
        ]
        
        db_path = None
        for path in db_paths:
            if path.exists():
                db_path = path
                break
        
        if not db_path:
            print("ERROR: Database file not found")
            return
        
        print(f"Database: {db_path}")
        print()
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all registrations for this phone
        cursor.execute("""
            SELECT id, phone, status, phone_code_hash, created_at, updated_at, error_message, retry_count
            FROM user_registrations
            WHERE phone = ? OR phone = ?
            ORDER BY created_at DESC
            LIMIT 10
        """, (phone, phone.replace('+', '')))
        
        records = cursor.fetchall()
        
        if not records:
            print(f"No registration records found for {phone}")
        else:
            print(f"Found {len(records)} registration records:")
            print()
            
            for record in records:
                reg_id, reg_phone, status, phone_code_hash, created_at, updated_at, error_message, retry_count = record
                
                print(f"Registration ID: {reg_id}")
                print(f"  Phone: {reg_phone}")
                print(f"  Status: {status}")
                print(f"  Phone Code Hash: {phone_code_hash}")
                print(f"  Created At: {created_at}")
                print(f"  Updated At: {updated_at}")
                print(f"  Retry Count: {retry_count}")
                if error_message:
                    print(f"  Error: {error_message}")
                
                # Calculate time difference
                if created_at and updated_at:
                    try:
                        created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        time_diff = (updated - created).total_seconds()
                        print(f"  Time Difference: {time_diff:.1f} seconds ({time_diff/60:.2f} minutes)")
                    except:
                        pass
                
                print()
        
        # Check for multiple code_sent records
        cursor.execute("""
            SELECT COUNT(*) 
            FROM user_registrations
            WHERE (phone = ? OR phone = ?) AND status = 'code_sent'
        """, (phone, phone.replace('+', '')))
        
        code_sent_count = cursor.fetchone()[0]
        if code_sent_count > 1:
            print(f"WARNING: Found {code_sent_count} records with status 'code_sent'")
            print("This suggests multiple 'start registration' clicks!")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("Analysis Complete")
    print("=" * 80)

if __name__ == "__main__":
    phone = sys.argv[1] if len(sys.argv) > 1 else "+639542360349"
    analyze_timing(phone)

