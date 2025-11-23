#!/usr/bin/env python3
"""
啟動所有已部署的服務器
"""

import sys
import subprocess
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from master_controller import MasterController


def start_all_servers():
    """啟動所有已部署的服務器"""
    controller = MasterController()
    
    print("=" * 60)
    print("啟動所有已部署的服務器")
    print("=" * 60)
    print()
    
    if not controller.servers:
        print("沒有已配置的服務器")
        return
    
    results = {}
    for node_id, config in controller.servers.items():
        print(f"啟動服務器: {node_id} ({config.host})...")
        
        # 優先使用paramiko（更可靠）
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(config.host, username=config.user, password=config.password, timeout=10)
            
            # 檢查服務是否存在
            stdin, stdout, stderr = ssh.exec_command('systemctl list-units --type=service | grep group-ai-worker || echo "not_found"')
            service_exists = "group-ai-worker" in stdout.read().decode('utf-8')
            
            if not service_exists:
                print(f"[WARN] {node_id}: 服務尚未部署，請先執行部署")
                results[node_id] = False
                ssh.close()
                continue
            
            # 啟動服務
            stdin, stdout, stderr = ssh.exec_command('systemctl start group-ai-worker')
            exit_code = stdout.channel.recv_exit_status()
            
            if exit_code == 0:
                # 檢查狀態
                stdin, stdout, stderr = ssh.exec_command('systemctl is-active group-ai-worker')
                status = stdout.read().decode('utf-8').strip()
                
                if status == "active":
                    print(f"[OK] {node_id} 啟動成功")
                    results[node_id] = True
                else:
                    print(f"[WARN] {node_id} 啟動命令執行，但狀態為: {status}")
                    results[node_id] = False
            else:
                error = stderr.read().decode('utf-8')
                print(f"[FAIL] {node_id} 啟動失敗: {error}")
                results[node_id] = False
            
            ssh.close()
        except ImportError:
            # 如果paramiko不可用，嘗試使用sshpass
            try:
                cmd = [
                    'sshpass', '-p', config.password,
                    'ssh', '-o', 'StrictHostKeyChecking=accept-new',
                    f'{config.user}@{config.host}',
                    'systemctl start group-ai-worker && systemctl is-active group-ai-worker'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and "active" in result.stdout:
                    print(f"[OK] {node_id} 啟動成功")
                    results[node_id] = True
                else:
                    print(f"[FAIL] {node_id} 啟動失敗: {result.stderr}")
                    results[node_id] = False
            except FileNotFoundError:
                print(f"[FAIL] {node_id}: 需要安裝 paramiko 或 sshpass")
                results[node_id] = False
        except Exception as e:
            print(f"[FAIL] {node_id} 啟動失敗: {e}")
            results[node_id] = False
        
        time.sleep(2)
    
    print()
    print("=" * 60)
    print("啟動完成:")
    for node_id, success in results.items():
        status = "[OK]" if success else "[FAIL]"
        print(f"  {status} {node_id}")
    print("=" * 60)


if __name__ == '__main__':
    start_all_servers()

