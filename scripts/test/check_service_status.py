#!/usr/bin/env python3
"""
检查远程服务状态
"""
import json
import paramiko
from pathlib import Path

def check_service_status():
    """检查服务状态"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"检查服务器: {node_id}")
        print(f"{'='*60}\n")
        
        host = server_config['host']
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=user, password=password, timeout=5)
            
            # 检查部署目录
            stdin, stdout, stderr = ssh.exec_command(f'test -d {deploy_dir} && echo yes || echo no')
            dir_exists = stdout.read().decode('utf-8').strip() == 'yes'
            print(f"部署目录: {'[OK]' if dir_exists else '[FAIL]'}")
            
            # 检查虚拟环境
            stdin, stdout, stderr = ssh.exec_command(f'test -f {deploy_dir}/venv/bin/python && echo yes || echo no')
            venv_ok = stdout.read().decode('utf-8').strip() == 'yes'
            print(f"虚拟环境: {'[OK]' if venv_ok else '[FAIL]'}")
            
            # 检查pip
            stdin, stdout, stderr = ssh.exec_command(f'test -f {deploy_dir}/venv/bin/pip && echo yes || echo no')
            pip_ok = stdout.read().decode('utf-8').strip() == 'yes'
            print(f"pip工具: {'[OK]' if pip_ok else '[FAIL]'}")
            
            # 检查systemd服务文件
            stdin, stdout, stderr = ssh.exec_command('test -f /etc/systemd/system/group-ai-worker.service && echo yes || echo no')
            service_file = stdout.read().decode('utf-8').strip() == 'yes'
            print(f"服务文件: {'[OK]' if service_file else '[FAIL]'}")
            
            # 检查服务状态
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active group-ai-worker 2>&1')
            service_status = stdout.read().decode('utf-8').strip()
            if 'active' in service_status:
                print(f"服务状态: [OK] {service_status}")
            elif 'inactive' in service_status:
                print(f"服务状态: [OFFLINE] {service_status}")
            else:
                print(f"服务状态: [FAIL] {service_status}")
            
            # 检查服务是否启用
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-enabled group-ai-worker 2>&1')
            enabled = stdout.read().decode('utf-8').strip()
            print(f"开机自启: {'[OK]' if 'enabled' in enabled else '[FAIL]'} {enabled}")
            
            # 查看最近日志
            if service_file:
                print("\n最近服务日志:")
                stdin, stdout, stderr = ssh.exec_command('sudo journalctl -u group-ai-worker -n 5 --no-pager 2>&1')
                logs = stdout.read().decode('utf-8')
                if logs.strip():
                    for line in logs.strip().split('\n')[:5]:
                        print(f"  {line}")
                else:
                    print("  (无日志)")
            
            ssh.close()
            
        except Exception as e:
            print(f"[FAIL] 连接错误: {e}")

if __name__ == "__main__":
    check_service_status()

