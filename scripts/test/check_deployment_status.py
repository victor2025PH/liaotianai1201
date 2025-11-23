#!/usr/bin/env python3
"""
檢查部署狀態
"""
import json
import paramiko
from pathlib import Path

def check_deployment():
    """檢查部署狀態"""
    # 讀取配置
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"檢查服務器: {node_id}")
        print(f"{'='*60}")
        
        host = server_config.get('host')
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=user, password=password, timeout=5)
            
            # 檢查目錄
            stdin, stdout, stderr = ssh.exec_command(f'ls -la {deploy_dir} 2>&1 | head -5')
            dir_status = stdout.read().decode('utf-8')
            print(f"\n[1] 部署目錄狀態:")
            if 'No such file' in dir_status:
                print("  ❌ 目錄不存在")
            else:
                print("  ✅ 目錄存在")
                print(f"  {dir_status[:200]}")
            
            # 檢查服務
            stdin, stdout, stderr = ssh.exec_command('systemctl list-unit-files --type=service | grep group-ai-worker')
            service_list = stdout.read().decode('utf-8')
            print(f"\n[2] Systemd服務狀態:")
            if service_list.strip():
                print("  ✅ 服務已創建")
                print(f"  {service_list.strip()}")
                
                # 檢查服務狀態
                stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active group-ai-worker 2>&1')
                active_status = stdout.read().decode('utf-8').strip()
                print(f"\n[3] 服務運行狀態:")
                if 'active' in active_status:
                    print(f"  ✅ 服務正在運行: {active_status}")
                else:
                    print(f"  ⚠️  服務未運行: {active_status}")
                
                # 檢查服務日誌
                stdin, stdout, stderr = ssh.exec_command('sudo journalctl -u group-ai-worker -n 5 --no-pager 2>&1')
                logs = stdout.read().decode('utf-8')
                if logs.strip():
                    print(f"\n[4] 最近日誌:")
                    print(f"  {logs[:300]}")
            else:
                print("  ❌ 服務尚未創建")
            
            # 檢查虛擬環境
            stdin, stdout, stderr = ssh.exec_command(f'test -d {deploy_dir}/venv && echo "exists" || echo "not_found"')
            venv_status = stdout.read().decode('utf-8').strip()
            print(f"\n[5] 虛擬環境:")
            if venv_status == 'exists':
                print("  ✅ 虛擬環境存在")
            else:
                print("  ❌ 虛擬環境不存在")
            
            ssh.close()
            
        except Exception as e:
            print(f"  ❌ 連接失敗: {e}")

if __name__ == "__main__":
    check_deployment()

