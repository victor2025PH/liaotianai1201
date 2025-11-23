#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断验证码发送问题
"""
import requests
import json
import sys
from datetime import datetime
from pathlib import Path

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

def check_server_send_code_script(node_id):
    """检查服务器上的发送验证码脚本"""
    print("=" * 80)
    print(f"Checking Send Code Script on Server: {node_id}")
    print("=" * 80)
    
    try:
        config_path = Path("data/master_config.json")
        if not config_path.exists():
            print("ERROR: Server config file not found")
            return
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        servers = config.get('servers', {})
        server_config = servers.get(node_id)
        
        if not server_config:
            print(f"ERROR: Server {node_id} not found")
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
                "ls -lt /tmp/send_code_*.py 2>/dev/null | head -3"
            )
            scripts = stdout.read().decode('utf-8').strip()
            
            if scripts:
                print("Recent send_code scripts:")
                script_files = []
                for line in scripts.split('\n'):
                    if line.strip() and '.py' in line:
                        parts = line.split()
                        if len(parts) >= 9:
                            script_file = parts[-1]
                            script_files.append(script_file)
                            print(f"  {script_file}")
                
                # Check the most recent script
                if script_files:
                    latest_script = script_files[0]
                    print(f"\nChecking latest script: {latest_script}")
                    
                    # Read script content
                    stdin, stdout, stderr = ssh.exec_command(
                        f"cat {latest_script} 2>/dev/null"
                    )
                    script_content = stdout.read().decode('utf-8', errors='ignore')
                    
                    # Extract key information
                    print("\nScript key information:")
                    for line in script_content.split('\n'):
                        if any(keyword in line for keyword in ['API_ID', 'API_HASH', 'PHONE', 'SESSION_NAME']):
                            print(f"  {line.strip()}")
                    
                    # Try to execute and see output
                    print(f"\nAttempting to execute script to see what happens...")
                    stdin, stdout, stderr = ssh.exec_command(
                        f"cd /home/ubuntu && timeout 30 python3 {latest_script} 2>&1"
                    )
                    output = stdout.read().decode('utf-8', errors='ignore')
                    error_output = stderr.read().decode('utf-8', errors='ignore')
                    
                    if output:
                        print("Script Output:")
                        print(output)
                    
                    if error_output:
                        print("Script Errors:")
                        print(error_output)
            else:
                print("No send_code scripts found")
                print("This means no verification code has been sent recently")
            
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

def check_database_for_pending(node_id=None):
    """检查数据库中的pending记录"""
    print("=" * 80)
    print("Checking Database for Pending Registrations")
    print("=" * 80)
    
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
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        if node_id:
            cursor.execute("""
                SELECT id, phone, status, phone_code_hash, created_at, updated_at, 
                       error_message, retry_count, node_id
                FROM user_registrations
                WHERE node_id = ? AND status = 'pending'
                ORDER BY created_at DESC
                LIMIT 10
            """, (node_id,))
        else:
            cursor.execute("""
                SELECT id, phone, status, phone_code_hash, created_at, updated_at, 
                       error_message, retry_count, node_id
                FROM user_registrations
                WHERE status = 'pending'
                ORDER BY created_at DESC
                LIMIT 10
            """)
        
        records = cursor.fetchall()
        
        if records:
            print(f"Found {len(records)} pending registrations:")
            print()
            for record in records:
                reg_id, reg_phone, status, phone_code_hash, created_at, updated_at, error_message, retry_count, reg_node_id = record
                print(f"  Registration ID: {reg_id}")
                print(f"    Phone: {reg_phone}")
                print(f"    Node ID: {reg_node_id}")
                print(f"    Status: {status}")
                print(f"    Created At: {created_at}")
                print(f"    Error: {error_message or 'None'}")
                print()
                print("  WARNING: Status is 'pending', verification code may not have been sent!")
        else:
            print("No pending registrations found")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    node_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("=" * 80)
    print("Diagnosing Code Sending Issue")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if node_id:
        print(f"Node ID: {node_id}")
    print("=" * 80)
    print()
    
    # Check database
    check_database_for_pending(node_id)
    print()
    
    # Check server scripts
    if node_id:
        check_server_send_code_script(node_id)
    else:
        # Check all servers
        try:
            config_path = Path("data/master_config.json")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                servers = config.get('servers', {})
                for server_node_id in servers.keys():
                    print()
                    check_server_send_code_script(server_node_id)
        except Exception as e:
            print(f"ERROR: {e}")

