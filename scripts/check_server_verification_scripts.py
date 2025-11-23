#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查服务器上的验证脚本
"""
import json
import sys
from pathlib import Path
from datetime import datetime

def check_verification_scripts():
    """检查服务器上的验证脚本"""
    print("=" * 80)
    print("Checking Verification Scripts on Servers")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Load server config
    config_path = Path("data/master_config.json")
    if not config_path.exists():
        print("ERROR: Server config file not found")
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        host = server_config.get('host', '')
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        
        print(f"Server: {node_id} ({host})")
        print("-" * 80)
        
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=user, password=password, timeout=10)
            
            # List recent verification scripts
            stdin, stdout, stderr = ssh.exec_command(
                "ls -lt /tmp/verify_session_*.py 2>/dev/null | head -10"
            )
            scripts = stdout.read().decode('utf-8').strip()
            
            if scripts:
                print("Recent verification scripts:")
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
                    if 'PHONE_CODE_HASH' in script_content:
                        for line in script_content.split('\n'):
                            if 'PHONE_CODE_HASH' in line or 'CODE =' in line or 'PHONE =' in line:
                                print(f"  {line.strip()}")
                    
                    # Check if script was executed
                    script_name = Path(latest_script).stem
                    stdin, stdout, stderr = ssh.exec_command(
                        f"grep -r '{script_name}' /var/log/ 2>/dev/null | tail -5 || echo 'No logs found'"
                    )
                    execution_logs = stdout.read().decode('utf-8').strip()
                    if execution_logs and 'No logs found' not in execution_logs:
                        print(f"\nExecution logs:")
                        print(execution_logs)
            else:
                print("No verification scripts found")
            
            # Check for Python processes related to verification
            stdin, stdout, stderr = ssh.exec_command(
                "ps aux | grep -E 'verify_session|sign_in' | grep -v grep || echo 'No verification processes'"
            )
            processes = stdout.read().decode('utf-8').strip()
            if processes and 'No verification processes' not in processes:
                print(f"\nRunning verification processes:")
                print(processes)
            
            ssh.close()
        except ImportError:
            print("ERROR: paramiko not installed")
        except Exception as e:
            print(f"ERROR: {e}")
        
        print()
    
    print("=" * 80)
    print("Check Complete")
    print("=" * 80)

if __name__ == "__main__":
    check_verification_scripts()

