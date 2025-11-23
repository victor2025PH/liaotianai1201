#!/usr/bin/env python3
"""
完成剩餘部署步驟
"""
import sys
import json
import paramiko
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from auto_deploy import AutoDeployer

def complete_remaining():
    """完成剩餘部署步驟"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"完成剩餘部署步驟: {node_id}")
        print(f"{'='*60}\n")
        
        host = server_config['host']
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
        
        deployer = AutoDeployer(
            remote_host=host,
            remote_user=user,
            remote_password=password,
            node_id=server_config.get('node_id', node_id),
            deploy_dir=deploy_dir,
            max_accounts=server_config.get('max_accounts', 5)
        )
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=5)
        
        try:
            # 檢查虛擬環境是否可用
            print("[1/4] 檢查虛擬環境...")
            stdin, stdout, stderr = ssh.exec_command(f'test -f {deploy_dir}/venv/bin/python && echo yes || echo no')
            venv_ok = stdout.read().decode('utf-8').strip() == 'yes'
            
            if not venv_ok:
                print("  虛擬環境不完整，重新創建...")
                stdin, stdout, stderr = ssh.exec_command(
                    f'cd {deploy_dir} && rm -rf venv && python3 -m venv venv'
                )
                exit_code = stdout.channel.recv_exit_status()
                if exit_code == 0:
                    print("  ✅ 虛擬環境重新創建成功")
                else:
                    print("  ⚠️  虛擬環境創建可能失敗，但繼續執行")
            else:
                print("  ✅ 虛擬環境可用")
            
            # 升級pip（不檢查結果）
            print("  升級pip...")
            ssh.exec_command(f'{deploy_dir}/venv/bin/pip install --upgrade pip setuptools wheel > /dev/null 2>&1')
            
            # 2. 安裝依賴
            print("\n[2/4] 安裝Python依賴（這可能需要5-10分鐘）...")
            if deployer.install_dependencies():
                print("  ✅ 依賴安裝完成")
            else:
                print("  ❌ 依賴安裝失敗")
                ssh.close()
                return False
            
            # 3. 創建配置文件
            print("\n[3/4] 創建配置文件...")
            if deployer.create_config_files(
                telegram_api_id=server_config.get('telegram_api_id', ''),
                telegram_api_hash=server_config.get('telegram_api_hash', ''),
                openai_api_key=server_config.get('openai_api_key', '')
            ):
                print("  ✅ 配置文件創建完成")
            else:
                print("  ⚠️  配置文件創建失敗，但繼續執行")
            
            # 4. 創建systemd服務
            print("\n[4/4] 創建systemd服務...")
            if deployer.create_startup_scripts():
                print("  ✅ 服務創建完成")
                
                # 啟動服務
                print("  啟動服務...")
                stdin, stdout, stderr = ssh.exec_command('sudo systemctl start group-ai-worker 2>&1')
                start_output = stdout.read().decode('utf-8')
                start_error = stderr.read().decode('utf-8')
                
                if not start_output and not start_error:
                    print("  ✅ 服務已啟動")
                elif 'Failed' not in start_output and 'Failed' not in start_error:
                    print("  ✅ 服務已啟動")
                else:
                    print(f"  ⚠️  服務啟動信息: {start_output}{start_error}")
                
                # 檢查服務狀態
                stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active group-ai-worker 2>&1')
                status = stdout.read().decode('utf-8').strip()
                print(f"  服務狀態: {status}")
                
                if 'active' in status:
                    print("\n🎉 部署完全成功！服務正在運行！")
                else:
                    print(f"\n⚠️  服務已創建但未運行，狀態: {status}")
                
            else:
                print("  ❌ 服務創建失敗")
                ssh.close()
                return False
            
            print(f"\n{'='*60}")
            print(f"✅ 部署完成！節點ID: {node_id}")
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
    complete_remaining()

