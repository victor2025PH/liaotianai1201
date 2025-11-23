#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查验证码发送问题
"""
import requests
import json
import sys
from datetime import datetime

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

def check_recent_registrations(token, phone=None):
    """检查最近的注册记录"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("=" * 80)
    print("Checking Recent Registration Records")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if phone:
        print(f"Phone: {phone}")
    print("=" * 80)
    print()
    
    # Try to get registrations via API (if available)
    # Otherwise check database directly
    
    try:
        import sqlite3
        from pathlib import Path
        
        db_paths = [
            Path("admin-backend/admin.db"),
            Path("admin-backend/data/admin.db"),
            Path("data/admin.db"),
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
        
        # Get recent registrations
        if phone:
            cursor.execute("""
                SELECT id, phone, status, phone_code_hash, created_at, updated_at, 
                       error_message, retry_count, node_id
                FROM user_registrations
                WHERE phone = ? OR phone = ?
                ORDER BY created_at DESC
                LIMIT 10
            """, (phone, phone.replace('+', '')))
        else:
            cursor.execute("""
                SELECT id, phone, status, phone_code_hash, created_at, updated_at, 
                       error_message, retry_count, node_id
                FROM user_registrations
                ORDER BY created_at DESC
                LIMIT 10
            """)
        
        records = cursor.fetchall()
        
        if not records:
            print("No recent registration records found")
        else:
            print(f"Found {len(records)} recent registration records:")
            print()
            
            for record in records:
                reg_id, reg_phone, status, phone_code_hash, created_at, updated_at, error_message, retry_count, node_id = record
                
                print(f"Registration ID: {reg_id}")
                print(f"  Phone: {reg_phone}")
                print(f"  Node ID: {node_id}")
                print(f"  Status: {status}")
                print(f"  Phone Code Hash: {phone_code_hash}")
                print(f"  Created At: {created_at}")
                print(f"  Updated At: {updated_at}")
                print(f"  Retry Count: {retry_count}")
                if error_message:
                    print(f"  Error: {error_message}")
                
                # Check if code was sent
                if status == 'code_sent' and phone_code_hash:
                    print(f"  ✅ Verification code was sent successfully")
                elif status == 'pending':
                    print(f"  ⚠️  Status is 'pending', code may not have been sent")
                elif status == 'failed':
                    print(f"  ❌ Registration failed: {error_message}")
                
                print()
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

def check_server_code_sending(node_id):
    """检查服务器上的验证码发送脚本"""
    print("=" * 80)
    print(f"Checking Code Sending on Server: {node_id}")
    print("=" * 80)
    
    try:
        import json
        from pathlib import Path
        
        config_path = Path("data/master_config.json")
        if not config_path.exists():
            print("ERROR: Server config file not found")
            return
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        servers = config.get('servers', {})
        server_config = servers.get(node_id)
        
        if not server_config:
            print(f"ERROR: Server {node_id} not found in config")
            return
        
        host = server_config.get('host', '')
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        
        print(f"Server: {node_id}")
        print(f"  Host: {host}")
        print(f"  User: {user}")
        print()
        
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=user, password=password, timeout=10)
            
            # Check recent send_code scripts
            stdin, stdout, stderr = ssh.exec_command(
                "ls -lt /tmp/send_code_*.py 2>/dev/null | head -5"
            )
            scripts = stdout.read().decode('utf-8').strip()
            
            if scripts:
                print("Recent send_code scripts:")
                for line in scripts.split('\n'):
                    if line.strip() and '.py' in line:
                        print(f"  {line.strip()}")
            else:
                print("No send_code scripts found")
            
            # Check for errors in script execution
            stdin, stdout, stderr = ssh.exec_command(
                "grep -r 'ERROR' /tmp/send_code_*.py 2>/dev/null | head -10 || echo 'No errors found'"
            )
            errors = stdout.read().decode('utf-8').strip()
            if errors and 'No errors found' not in errors:
                print(f"\nErrors in scripts:")
                print(errors)
            
            ssh.close()
            
        except ImportError:
            print("ERROR: paramiko not installed")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    token = login()
    if not token:
        print("ERROR: Failed to login")
        sys.exit(1)
    
    phone = sys.argv[1] if len(sys.argv) > 1 else None
    node_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    check_recent_registrations(token, phone)
    
    if node_id:
        print()
        check_server_code_sending(node_id)

