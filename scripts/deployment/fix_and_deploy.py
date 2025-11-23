#!/usr/bin/env python3
"""
修复并完成部署
"""
import json
import paramiko
from pathlib import Path
import time

def fix_and_deploy():
    """修复并完成部署"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"修复并部署: {node_id}")
        print(f"{'='*60}\n")
        
        host = server_config['host']
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=5)
        
        try:
            # 1. 重新创建虚拟环境
            print("[1/6] 重新创建虚拟环境...")
            ssh.exec_command(f'sudo rm -rf {deploy_dir}/venv')
            time.sleep(1)
            
            stdin, stdout, stderr = ssh.exec_command(f'cd {deploy_dir} && python3 -m venv venv 2>&1')
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if exit_code == 0:
                ssh.exec_command(f'sudo chown -R {user}:{user} {deploy_dir}/venv')
                print("  [OK] 虚拟环境创建成功")
            else:
                print(f"  [FAIL] 创建失败: {output}{error}")
                return False
            
            # 2. 升级pip
            print("\n[2/6] 升级pip...")
            stdin, stdout, stderr = ssh.exec_command(
                f'{deploy_dir}/venv/bin/python -m pip install --upgrade pip 2>&1',
                timeout=60
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  [OK] pip升级完成")
            else:
                error = stderr.read().decode('utf-8')
                print(f"  [WARN] pip升级可能失败: {error[:100]}")
            
            # 3. 安装依赖
            print("\n[3/6] 安装Python依赖（这需要5-10分钟）...")
            stdin, stdout, stderr = ssh.exec_command(
                f'cd {deploy_dir} && {deploy_dir}/venv/bin/pip install -r requirements.txt 2>&1',
                timeout=600
            )
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if exit_code == 0:
                print("  [OK] 依赖安装完成")
            else:
                print(f"  [FAIL] 依赖安装失败")
                print(f"  错误: {error[:300]}")
                return False
            
            # 4. 创建启动脚本
            print("\n[4/6] 创建启动脚本...")
            start_script = f"""#!/bin/bash
cd {deploy_dir}
source venv/bin/activate
export PYTHONPATH={deploy_dir}:$PYTHONPATH

# 检查是否有group_ai_service目录
if [ -d "group_ai_service" ]; then
    cd group_ai_service
    {deploy_dir}/venv/bin/python -c "from service_manager import ServiceManager; sm = ServiceManager(); sm.start()"
else
    echo "Worker service placeholder - waiting..."
    sleep infinity
fi"""
            
            stdin, stdout, stderr = ssh.exec_command(
                f"cat > {deploy_dir}/start.sh << 'EOFSCRIPT'\n{start_script}\nEOFSCRIPT\nchmod +x {deploy_dir}/start.sh"
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  [OK] 启动脚本创建成功")
            else:
                error = stderr.read().decode('utf-8')
                print(f"  [FAIL] 启动脚本创建失败: {error}")
                return False
            
            # 5. 创建systemd服务
            print("\n[5/6] 创建systemd服务...")
            systemd_service = f"""[Unit]
Description=Group AI Worker Node Service
After=network.target

[Service]
Type=simple
User={user}
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
            
            stdin, stdout, stderr = ssh.exec_command(
                f"sudo bash -c 'cat > /etc/systemd/system/group-ai-worker.service << \"EOFSERVICE\"\n{systemd_service}\nEOFSERVICE'"
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code != 0:
                error = stderr.read().decode('utf-8')
                print(f"  [FAIL] 服务文件创建失败: {error}")
                return False
            
            # 重新加载systemd
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl daemon-reload')
            print("  [OK] systemd已重新加载")
            
            # 启用服务
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl enable group-ai-worker')
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  [OK] 服务已启用")
            else:
                print("  [WARN] 服务启用可能失败")
            
            # 6. 启动服务
            print("\n[6/6] 启动服务...")
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl start group-ai-worker 2>&1')
            start_output = stdout.read().decode('utf-8')
            start_error = stderr.read().decode('utf-8')
            
            time.sleep(3)
            
            # 检查服务状态
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active group-ai-worker 2>&1')
            status = stdout.read().decode('utf-8').strip()
            
            print(f"  服务状态: {status}")
            
            if 'active' in status:
                print("\n" + "="*60)
                print("🎉 部署完成！服务已启动！")
                print("="*60)
            else:
                print("\n" + "="*60)
                print(f"⚠️  服务已创建，但状态: {status}")
                print("="*60)
            
            # 查看日志
            stdin, stdout, stderr = ssh.exec_command('sudo journalctl -u group-ai-worker -n 10 --no-pager 2>&1')
            logs = stdout.read().decode('utf-8')
            if logs.strip():
                print("\n最近日志:")
                for line in logs.strip().split('\n')[:10]:
                    print(f"  {line}")
            
            ssh.close()
            return True
            
        except Exception as e:
            print(f"[FAIL] 错误: {e}")
            import traceback
            traceback.print_exc()
            ssh.close()
            return False

if __name__ == "__main__":
    fix_and_deploy()

