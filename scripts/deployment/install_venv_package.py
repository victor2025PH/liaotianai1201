#!/usr/bin/env python3
"""
安装python3-venv包
"""
import json
import paramiko
from pathlib import Path

def install_venv():
    """安装python3-venv"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"安装python3-venv: {node_id}")
        print(f"{'='*60}\n")
        
        host = server_config['host']
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=5)
        
        try:
            print("检查Python版本...")
            stdin, stdout, stderr = ssh.exec_command('python3 --version')
            version = stdout.read().decode('utf-8').strip()
            print(f"  {version}")
            
            print("\n更新apt包列表...")
            stdin, stdout, stderr = ssh.exec_command('sudo apt-get update -qq', timeout=120)
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  [OK] apt更新完成")
            else:
                error = stderr.read().decode('utf-8')
                print(f"  [WARN] apt更新可能有问题: {error[:100]}")
            
            print("\n安装python3-venv...")
            stdin, stdout, stderr = ssh.exec_command('sudo apt-get install -y python3.12-venv 2>&1', timeout=120)
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if exit_code == 0 or 'Setting up' in output:
                print("  [OK] python3-venv安装成功")
            else:
                # 尝试通用版本
                print("  尝试安装通用版本...")
                stdin, stdout, stderr = ssh.exec_command('sudo apt-get install -y python3-venv 2>&1', timeout=120)
                exit_code = stdout.channel.recv_exit_status()
                output = stdout.read().decode('utf-8')
                if exit_code == 0 or 'Setting up' in output:
                    print("  [OK] python3-venv安装成功")
                else:
                    print(f"  [FAIL] 安装失败: {error[:200]}")
                    return False
            
            ssh.close()
            return True
            
        except Exception as e:
            print(f"[FAIL] 错误: {e}")
            import traceback
            traceback.print_exc()
            ssh.close()
            return False

if __name__ == "__main__":
    install_venv()

