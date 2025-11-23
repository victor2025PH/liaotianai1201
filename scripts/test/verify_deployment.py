#!/usr/bin/env python3
"""
驗證部署狀態
"""
import json
import paramiko
from pathlib import Path

def verify_deployment():
    """驗證部署狀態"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"驗證服務器: {node_id}")
        print(f"{'='*60}\n")
        
        host = server_config.get('host')
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
        
        checks = {
            '目錄存在': False,
            '虛擬環境': False,
            '項目文件': False,
            'Systemd服務': False,
            '服務運行': False,
            '服務啟用': False
        }
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=user, password=password, timeout=5)
            
            # 檢查目錄
            stdin, stdout, stderr = ssh.exec_command(f'test -d {deploy_dir} && echo yes || echo no')
            if stdout.read().decode('utf-8').strip() == 'yes':
                checks['目錄存在'] = True
                print("✅ 部署目錄存在")
            else:
                print("❌ 部署目錄不存在")
            
            # 檢查虛擬環境
            stdin, stdout, stderr = ssh.exec_command(f'test -d {deploy_dir}/venv && echo yes || echo no')
            if stdout.read().decode('utf-8').strip() == 'yes':
                checks['虛擬環境'] = True
                print("✅ 虛擬環境存在")
            else:
                print("❌ 虛擬環境不存在")
            
            # 檢查項目文件
            stdin, stdout, stderr = ssh.exec_command(f'test -d {deploy_dir}/group_ai_service && echo yes || echo no')
            if stdout.read().decode('utf-8').strip() == 'yes':
                checks['項目文件'] = True
                print("✅ 項目文件存在")
            else:
                print("❌ 項目文件不存在")
            
            # 檢查systemd服務
            stdin, stdout, stderr = ssh.exec_command('systemctl list-unit-files --type=service | grep group-ai-worker')
            service_list = stdout.read().decode('utf-8')
            if service_list.strip():
                checks['Systemd服務'] = True
                print("✅ Systemd服務已創建")
                
                # 檢查服務狀態
                stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active group-ai-worker 2>&1')
                active_status = stdout.read().decode('utf-8').strip()
                if 'active' in active_status:
                    checks['服務運行'] = True
                    print(f"✅ 服務正在運行: {active_status}")
                else:
                    print(f"⚠️  服務未運行: {active_status}")
                
                # 檢查開機自啟
                stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-enabled group-ai-worker 2>&1')
                enabled_status = stdout.read().decode('utf-8').strip()
                if 'enabled' in enabled_status:
                    checks['服務啟用'] = True
                    print(f"✅ 開機自啟已啟用")
                else:
                    print(f"⚠️  開機自啟未啟用: {enabled_status}")
            else:
                print("❌ Systemd服務尚未創建")
            
            ssh.close()
            
            # 總結
            print(f"\n{'='*60}")
            print("部署狀態總結:")
            print(f"{'='*60}")
            total = len(checks)
            passed = sum(1 for v in checks.values() if v)
            
            for key, value in checks.items():
                status = "✅" if value else "❌"
                print(f"{status} {key}")
            
            print(f"\n總體進度: {passed}/{total} ({passed*100//total}%)")
            
            if passed == total:
                print("\n🎉 部署完全成功！")
                return True
            elif checks['Systemd服務']:
                print("\n⚠️  部署部分成功，服務已創建但未運行")
                return False
            else:
                print("\n❌ 部署未完成，需要繼續部署")
                return False
                
        except Exception as e:
            print(f"❌ 連接失敗: {e}")
            return False

if __name__ == "__main__":
    verify_deployment()

