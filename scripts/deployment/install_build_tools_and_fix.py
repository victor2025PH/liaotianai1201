#!/usr/bin/env python3
"""
安装编译工具并修复虚拟环境
"""
import json
import paramiko
from pathlib import Path
import time

def install_build_tools_and_fix():
    """安装编译工具并修复"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"安装编译工具并修复: {node_id}")
        print(f"{'='*60}\n")
        
        host = server_config['host']
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=5)
        
        try:
            # 1. 安装编译工具
            print("[1/5] 安装编译工具（gcc, build-essential）...")
            stdin, stdout, stderr = ssh.exec_command(
                'sudo apt-get update -qq && sudo apt-get install -y build-essential python3-dev 2>&1',
                timeout=300
            )
            
            output_lines = []
            while True:
                line = stdout.readline()
                if not line:
                    break
                if isinstance(line, bytes):
                    decoded = line.decode('utf-8', errors='replace').strip()
                else:
                    decoded = str(line).strip()
                if decoded and ('Setting up' in decoded or 'Unpacking' in decoded):
                    output_lines.append(decoded)
                    print(f"  {decoded[:100]}")
            
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  [OK] 编译工具安装完成")
            else:
                print("  [WARN] 编译工具安装可能有问题，但继续")
            
            # 2. 重新创建虚拟环境
            print("\n[2/5] 重新创建虚拟环境...")
            ssh.exec_command(f'sudo rm -rf {deploy_dir}/venv')
            time.sleep(1)
            
            stdin, stdout, stderr = ssh.exec_command(f'cd {deploy_dir} && python3 -m venv venv 2>&1')
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                ssh.exec_command(f'sudo chown -R {user}:{user} {deploy_dir}/venv')
                print("  [OK] 虚拟环境创建成功")
            else:
                error = stderr.read().decode('utf-8')
                print(f"  [FAIL] 虚拟环境创建失败: {error}")
                return False
            
            # 3. 安装pip
            print("\n[3/5] 安装pip...")
            stdin, stdout, stderr = ssh.exec_command(
                f'curl -sS https://bootstrap.pypa.io/get-pip.py | {deploy_dir}/venv/bin/python 2>&1',
                timeout=120
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  [OK] pip安装完成")
            else:
                print("  [WARN] pip安装可能有问题，但继续")
            
            # 4. 升级pip
            print("\n[4/5] 升级pip...")
            stdin, stdout, stderr = ssh.exec_command(
                f'{deploy_dir}/venv/bin/python -m pip install --upgrade pip setuptools wheel 2>&1',
                timeout=120
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  [OK] pip升级完成")
            
            # 5. 安装pyrogram和tgcrypto
            print("\n[5/5] 安装pyrogram和tgcrypto（这需要3-5分钟）...")
            stdin, stdout, stderr = ssh.exec_command(
                f'cd {deploy_dir} && {deploy_dir}/venv/bin/pip install --no-cache-dir pyrogram tgcrypto 2>&1',
                timeout=600
            )
            
            output_lines = []
            while True:
                line = stdout.readline()
                if not line:
                    break
                if isinstance(line, bytes):
                    decoded = line.decode('utf-8', errors='replace').strip()
                else:
                    decoded = str(line).strip()
                if decoded:
                    output_lines.append(decoded)
                    if 'Installing' in decoded or 'Successfully' in decoded or 'Building' in decoded:
                        print(f"  {decoded[:100]}")
            
            exit_code = stdout.channel.recv_exit_status()
            output = '\n'.join(output_lines)
            
            if exit_code == 0 or 'Successfully installed' in output:
                print("  [OK] pyrogram安装完成")
            else:
                error = stderr.read().decode('utf-8')
                print(f"  [FAIL] pyrogram安装失败")
                print(f"  错误: {error[-500:]}")
                return False
            
            # 验证
            print("\n验证pyrogram...")
            stdin, stdout, stderr = ssh.exec_command(
                f'{deploy_dir}/venv/bin/python -c "import pyrogram; print(pyrogram.__version__)" 2>&1'
            )
            result = stdout.read().decode('utf-8').strip()
            if result and 'version' not in result.lower():
                print(f"  [OK] pyrogram版本: {result}")
            else:
                print(f"  [FAIL] pyrogram验证失败")
                return False
            
            # 安装其他关键依赖
            print("\n安装其他关键依赖...")
            stdin, stdout, stderr = ssh.exec_command(
                f'cd {deploy_dir} && {deploy_dir}/venv/bin/pip install fastapi uvicorn sqlalchemy aiosqlite pydantic 2>&1',
                timeout=300
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  [OK] 关键依赖安装完成")
            
            # 重启服务
            print("\n重启服务...")
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl restart group-ai-worker 2>&1')
            time.sleep(5)
            
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active group-ai-worker 2>&1')
            status = stdout.read().decode('utf-8').strip()
            print(f"服务状态: {status}")
            
            if 'active' in status:
                print("\n" + "="*60)
                print("🎉 修复完成！服务已启动！")
                print("="*60)
            else:
                print("\n查看服务日志...")
                stdin, stdout, stderr = ssh.exec_command('sudo journalctl -u group-ai-worker -n 15 --no-pager 2>&1')
                logs = stdout.read().decode('utf-8')
                print("最近日志:")
                for line in logs.strip().split('\n')[-15:]:
                    if line.strip():
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
    install_build_tools_and_fix()

