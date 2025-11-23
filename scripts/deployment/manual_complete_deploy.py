#!/usr/bin/env python3
"""
手動完成部署
"""
import json
import paramiko
from pathlib import Path

def manual_complete():
    """手動完成部署"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"手動完成部署: {node_id}")
        print(f"{'='*60}\n")
        
        host = server_config['host']
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=5)
        
        try:
            # 1. 重新創建虛擬環境
            print("[1/5] 重新創建虛擬環境...")
            stdin, stdout, stderr = ssh.exec_command(
                f'sudo rm -rf {deploy_dir}/venv && cd {deploy_dir} && python3 -m venv venv && sudo chown -R {user}:{user} {deploy_dir}/venv'
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  ✅ 虛擬環境創建成功")
            else:
                error = stderr.read().decode('utf-8')
                print(f"  ❌ 失敗: {error}")
                return False
            
            # 2. 升級pip
            print("[2/5] 升級pip...")
            stdin, stdout, stderr = ssh.exec_command(
                f'{deploy_dir}/venv/bin/pip install --upgrade pip setuptools wheel'
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  ✅ pip升級成功")
            else:
                print("  ⚠️  pip升級失敗，但繼續執行")
            
            # 3. 安裝依賴
            print("[3/5] 安裝Python依賴（這可能需要5-10分鐘）...")
            stdin, stdout, stderr = ssh.exec_command(
                f'cd {deploy_dir} && {deploy_dir}/venv/bin/pip install -r requirements.txt',
                timeout=600
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  ✅ 依賴安裝完成")
            else:
                error = stderr.read().decode('utf-8')
                print(f"  ❌ 依賴安裝失敗: {error[:200]}")
                return False
            
            # 4. 創建啟動腳本
            print("[4/5] 創建啟動腳本和systemd服務...")
            start_script = f"""#!/bin/bash
cd {deploy_dir}
source venv/bin/activate
export PYTHONPATH={deploy_dir}:$PYTHONPATH

if [ -d "admin-backend/app" ]; then
    cd admin-backend
    {deploy_dir}/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    echo "Worker service placeholder"
    sleep infinity
fi"""
            
            systemd_service = f"""[Unit]
Description=Group AI Worker Node Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory={deploy_dir}
Environment="PATH={deploy_dir}/venv/bin"
Environment="PYTHONPATH={deploy_dir}"
ExecStart={deploy_dir}/start.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target"""
            
            # 創建啟動腳本
            stdin, stdout, stderr = ssh.exec_command(
                f"cat > {deploy_dir}/start.sh << 'EOFSCRIPT'\n{start_script}\nEOFSCRIPT\nchmod +x {deploy_dir}/start.sh"
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code != 0:
                print("  ❌ 啟動腳本創建失敗")
                return False
            
            # 創建systemd服務
            stdin, stdout, stderr = ssh.exec_command(
                f"sudo bash -c 'cat > /etc/systemd/system/group-ai-worker.service << \"EOFSERVICE\"\n{systemd_service}\nEOFSERVICE'"
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code != 0:
                print("  ❌ systemd服務文件創建失敗")
                return False
            
            # 重新加載systemd並啟用服務
            stdin, stdout, stderr = ssh.exec_command(
                'sudo systemctl daemon-reload && sudo systemctl enable group-ai-worker'
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  ✅ systemd服務創建並啟用成功")
            else:
                print("  ⚠️  服務啟用可能失敗，但繼續執行")
            
            # 5. 啟動服務
            print("[5/5] 啟動服務...")
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl start group-ai-worker 2>&1')
            start_output = stdout.read().decode('utf-8')
            start_error = stderr.read().decode('utf-8')
            
            if not start_output and not start_error:
                print("  ✅ 服務已啟動")
            elif 'Failed' not in start_output and 'Failed' not in start_error:
                print("  ✅ 服務已啟動")
            else:
                print(f"  ⚠️  服務啟動: {start_output}{start_error}")
            
            # 檢查服務狀態
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active group-ai-worker 2>&1')
            status = stdout.read().decode('utf-8').strip()
            print(f"  服務運行狀態: {status}")
            
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-enabled group-ai-worker 2>&1')
            enabled = stdout.read().decode('utf-8').strip()
            print(f"  開機自啟狀態: {enabled}")
            
            print(f"\n{'='*60}")
            if 'active' in status:
                print(f"🎉 部署完全成功！服務正在運行！")
            else:
                print(f"⚠️  部署完成，但服務狀態: {status}")
            print(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            ssh.close()

if __name__ == "__main__":
    manual_complete()

