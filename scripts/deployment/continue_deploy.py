#!/usr/bin/env python3
"""
繼續完成部署（跳過基礎環境）
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from auto_deploy import AutoDeployer
import json

def continue_deployment():
    """繼續完成部署"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"繼續部署: {node_id}")
        print(f"{'='*60}\n")
        
        deployer = AutoDeployer(
            remote_host=server_config['host'],
            remote_user=server_config.get('user', 'ubuntu'),
            remote_password=server_config.get('password', ''),
            node_id=server_config.get('node_id', node_id),
            deploy_dir=server_config.get('deploy_dir', '/opt/group-ai'),
            max_accounts=server_config.get('max_accounts', 5)
        )
        
        # 跳過基礎環境部署，直接進行後續步驟
        print("[跳過] 基礎環境部署（已完成）")
        
        # 步驟2: 上傳項目文件（已存在，跳過）
        print("[跳過] 項目文件上傳（已存在）")
        
        # 步驟3: 創建虛擬環境
        print("[3/10] 創建虛擬環境...")
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            server_config['host'],
            username=server_config.get('user', 'ubuntu'),
            password=server_config.get('password', ''),
            timeout=5
        )
        
        deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
        
        # 檢查虛擬環境是否存在
        stdin, stdout, stderr = ssh.exec_command(f'test -d {deploy_dir}/venv && echo exists || echo not_exists')
        venv_exists = stdout.read().decode('utf-8').strip() == 'exists'
        
        if not venv_exists:
            # 創建虛擬環境
            print("  創建虛擬環境...")
            stdin, stdout, stderr = ssh.exec_command(
                f'cd {deploy_dir} && python3.11 -m venv venv 2>&1 || python3 -m venv venv 2>&1'
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code != 0:
                error = stderr.read().decode('utf-8')
                print(f"  創建失敗: {error}")
                ssh.close()
                return False
            print("  虛擬環境創建成功")
        
        # 升級pip
        print("  升級pip...")
        stdin, stdout, stderr = ssh.exec_command(
            f'{deploy_dir}/venv/bin/pip install --upgrade pip setuptools wheel 2>&1'
        )
        exit_code = stdout.channel.recv_exit_status()
        if exit_code != 0:
            error = stderr.read().decode('utf-8')
            print(f"  升級pip失敗: {error}")
            ssh.close()
            return False
        print("  pip升級成功")
        print("[OK] 虛擬環境創建完成")
        
        # 步驟4: 安裝依賴
        if deployer.install_dependencies():
            print("[OK] Python依賴安裝完成")
        else:
            print("[FAIL] Python依賴安裝失敗")
            ssh.close()
            return False
        
        # 步驟5: 創建配置文件
        if deployer.create_config_files(
            telegram_api_id=server_config.get('telegram_api_id', ''),
            telegram_api_hash=server_config.get('telegram_api_hash', ''),
            openai_api_key=server_config.get('openai_api_key', '')
        ):
            print("[OK] 配置文件創建完成")
        else:
            print("[FAIL] 配置文件創建失敗")
            return False
        
        # 步驟6: 創建啟動腳本和systemd服務
        if deployer.create_startup_scripts():
            print("[OK] 啟動腳本和服務創建完成")
            
            # 啟動服務（使用現有的SSH連接）
            
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl start group-ai-worker 2>&1')
            start_result = stdout.read().decode('utf-8')
            if 'Failed' not in start_result:
                print("[OK] 服務已啟動")
            else:
                print(f"[WARN] 服務啟動: {start_result}")
            
            ssh.close()
        else:
            print("[FAIL] 啟動腳本創建失敗")
            return False
        
        print(f"\n{'='*60}")
        print(f"[OK] 部署完成！節點ID: {node_id}")
        print(f"{'='*60}\n")
        return True

if __name__ == "__main__":
    continue_deployment()

