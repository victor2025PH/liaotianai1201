#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查验证脚本执行结果
"""
import json
from pathlib import Path
from datetime import datetime

def check_script_execution():
    """检查验证脚本执行结果"""
    print("=" * 80)
    print("Checking Verification Script Execution Results")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Load server config
    config_path = Path("data/master_config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    # Focus on los-angeles server where the script was found
    server_config = servers.get('los-angeles')
    if not server_config:
        print("ERROR: los-angeles server config not found")
        return
    
    host = server_config.get('host', '')
    user = server_config.get('user', 'ubuntu')
    password = server_config.get('password', '')
    
    print(f"Server: los-angeles ({host})")
    print("-" * 80)
    
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=10)
        
        # Check the specific script
        script_path = "/tmp/verify_session_5657c7ca-63df-43d5-b1ea-e28302d9be9a.py"
        
        print(f"Checking script: {script_path}")
        print()
        
        # Read full script content
        stdin, stdout, stderr = ssh.exec_command(f"cat {script_path} 2>/dev/null")
        script_content = stdout.read().decode('utf-8', errors='ignore')
        
        print("Script Content (key parts):")
        print("-" * 80)
        for line in script_content.split('\n'):
            if any(keyword in line for keyword in ['PHONE', 'PHONE_CODE_HASH', 'CODE', 'sign_in', 'ERROR', 'SUCCESS']):
                print(line)
        print()
        
        # Try to execute the script and see what happens
        print("Attempting to check script execution...")
        print("-" * 80)
        
        # Check if there are any error logs
        stdin, stdout, stderr = ssh.exec_command(
            f"python3 {script_path} 2>&1 | head -50"
        )
        output = stdout.read().decode('utf-8', errors='ignore')
        error_output = stderr.read().decode('utf-8', errors='ignore')
        
        if output:
            print("Script Output:")
            print(output)
        
        if error_output:
            print("Script Errors:")
            print(error_output)
        
        # Check for session files
        stdin, stdout, stderr = ssh.exec_command(
            "ls -lt /home/ubuntu/sessions/*.session 2>/dev/null | head -5"
        )
        sessions = stdout.read().decode('utf-8').strip()
        if sessions:
            print("\nRecent Session Files:")
            print(sessions)
        
        ssh.close()
        
    except ImportError:
        print("ERROR: paramiko not installed")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("Check Complete")
    print("=" * 80)

if __name__ == "__main__":
    check_script_execution()

