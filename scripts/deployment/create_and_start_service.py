#!/usr/bin/env python3
"""
创建并启动systemd服务
"""
import json
import paramiko
from pathlib import Path

def create_and_start_service():
    """创建并启动服务"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"创建并启动服务: {node_id}")
        print(f"{'='*60}\n")
        
        host = server_config['host']
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=5)
        
        try:
            # 1. 检查虚拟环境
            print("[1/5] 检查虚拟环境...")
            stdin, stdout, stderr = ssh.exec_command(f'test -f {deploy_dir}/venv/bin/python && echo yes || echo no')
            venv_ok = stdout.read().decode('utf-8').strip() == 'yes'
            
            if not venv_ok:
                print("  重新创建虚拟环境...")
                stdin, stdout, stderr = ssh.exec_command(
                    f'sudo rm -rf {deploy_dir}/venv && cd {deploy_dir} && python3 -m venv venv && sudo chown -R {user}:{user} {deploy_dir}/venv'
                )
                exit_code = stdout.channel.recv_exit_status()
                if exit_code == 0:
                    print("  [OK] 虚拟环境创建成功")
                else:
                    error = stderr.read().decode('utf-8')
                    print(f"  [FAIL] 失败: {error}")
                    return False
            else:
                print("  [OK] 虚拟环境可用")
            
            # 2. 检查并安装依赖
            print("\n[2/5] 检查Python依赖...")
            stdin, stdout, stderr = ssh.exec_command(
                f'{deploy_dir}/venv/bin/pip list | grep -q fastapi && echo installed || echo not_installed'
            )
            deps_installed = stdout.read().decode('utf-8').strip() == 'installed'
            
            if not deps_installed:
                print("  安装Python依赖（这可能需要5-10分钟）...")
                stdin, stdout, stderr = ssh.exec_command(
                    f'cd {deploy_dir} && {deploy_dir}/venv/bin/pip install -r requirements.txt',
                    timeout=600
                )
                exit_code = stdout.channel.recv_exit_status()
                if exit_code == 0:
                    print("  [OK] 依赖安装完成")
                else:
                    error = stderr.read().decode('utf-8')
                    print(f"  [FAIL] 依赖安装失败: {error[:200]}")
                    return False
            else:
                print("  [OK] 依赖已安装")
            
            # 3. 创建启动脚本
            print("\n[3/5] 创建启动脚本...")
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
            
            # 4. 创建systemd服务
            print("\n[4/5] 创建systemd服务...")
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
            exit_code = stdout.channel.recv_exit_status()
            if exit_code != 0:
                print("  [WARN] daemon-reload失败，但继续执行")
            
            # 启用服务
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl enable group-ai-worker')
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  [OK] 服务已创建并启用")
            else:
                print("  [WARN] 服务启用可能失败，但继续执行")
            
            # 5. 启动服务
            print("\n[5/5] 启动服务...")
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl start group-ai-worker 2>&1')
            start_output = stdout.read().decode('utf-8')
            start_error = stderr.read().decode('utf-8')
            
            if not start_output and not start_error:
                print("  [OK] 服务启动命令执行成功")
            elif 'Failed' not in start_output and 'Failed' not in start_error:
                print("  [OK] 服务启动成功")
            else:
                print(f"  [WARN] 启动信息: {start_output}{start_error}")
            
            # 等待一下让服务启动
            import time
            time.sleep(3)
            
            # 检查服务状态
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active group-ai-worker 2>&1')
            status = stdout.read().decode('utf-8').strip()
            print(f"  服务运行状态: {status}")
            
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-enabled group-ai-worker 2>&1')
            enabled = stdout.read().decode('utf-8').strip()
            print(f"  开机自启状态: {enabled}")
            
            # 查看服务日志
            stdin, stdout, stderr = ssh.exec_command('sudo journalctl -u group-ai-worker -n 10 --no-pager 2>&1')
            logs = stdout.read().decode('utf-8')
            if logs.strip():
                print(f"\n  最近日志:")
                print(f"  {logs[:300]}")
            
            print(f"\n{'='*60}")
            if 'active' in status:
                print(f"🎉 服务创建并启动成功！")
            else:
                print(f"⚠️  服务已创建，但状态: {status}")
            print(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            print(f"[FAIL] 错误: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            ssh.close()

if __name__ == "__main__":
    create_and_start_service()

