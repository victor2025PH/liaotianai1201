#!/usr/bin/env python3
"""
修复pip并安装依赖
"""
import json
import paramiko
from pathlib import Path
import time

def fix_pip_and_install():
    """修复pip并安装依赖"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"修复pip并安装依赖: {node_id}")
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
            print("[1/4] 检查虚拟环境...")
            stdin, stdout, stderr = ssh.exec_command(f'test -f {deploy_dir}/venv/bin/python && echo yes || echo no')
            venv_ok = stdout.read().decode('utf-8').strip() == 'yes'
            
            if not venv_ok:
                print("  重新创建虚拟环境...")
                ssh.exec_command(f'sudo rm -rf {deploy_dir}/venv')
                stdin, stdout, stderr = ssh.exec_command(f'cd {deploy_dir} && python3 -m venv venv 2>&1')
                exit_code = stdout.channel.recv_exit_status()
                if exit_code != 0:
                    print("  尝试安装python3-venv...")
                    ssh.exec_command('sudo apt-get install -y python3-venv 2>&1')
                    stdin, stdout, stderr = ssh.exec_command(f'cd {deploy_dir} && python3 -m venv venv 2>&1')
                    exit_code = stdout.channel.recv_exit_status()
                
                if exit_code == 0:
                    ssh.exec_command(f'sudo chown -R {user}:{user} {deploy_dir}/venv')
                    print("  [OK] 虚拟环境创建成功")
                else:
                    print("  [FAIL] 虚拟环境创建失败")
                    return False
            else:
                print("  [OK] 虚拟环境存在")
            
            # 2. 检查并修复pip
            print("\n[2/4] 检查pip...")
            stdin, stdout, stderr = ssh.exec_command(f'test -f {deploy_dir}/venv/bin/pip && echo yes || echo no')
            pip_ok = stdout.read().decode('utf-8').strip() == 'yes'
            
            if not pip_ok:
                print("  修复pip...")
                # 使用ensurepip安装pip
                stdin, stdout, stderr = ssh.exec_command(
                    f'{deploy_dir}/venv/bin/python -m ensurepip --upgrade 2>&1',
                    timeout=120
                )
                exit_code = stdout.channel.recv_exit_status()
                if exit_code == 0:
                    print("  [OK] pip已修复")
                else:
                    print("  [FAIL] pip修复失败")
                    return False
            else:
                print("  [OK] pip存在")
            
            # 3. 升级pip
            print("\n[3/4] 升级pip...")
            stdin, stdout, stderr = ssh.exec_command(
                f'{deploy_dir}/venv/bin/python -m pip install --upgrade pip 2>&1',
                timeout=120
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  [OK] pip升级完成")
            else:
                print("  [WARN] pip升级可能失败，但继续")
            
            # 4. 安装依赖
            print("\n[4/4] 安装Python依赖（这需要5-10分钟）...")
            stdin, stdout, stderr = ssh.exec_command(
                f'cd {deploy_dir} && {deploy_dir}/venv/bin/pip install -r requirements.txt 2>&1',
                timeout=900
            )
            
            # 实时输出进度
            output_lines = []
            while True:
                line = stdout.readline()
                if not line:
                    break
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded and ('Installing' in decoded or 'Successfully' in decoded or 'Requirement' in decoded):
                    output_lines.append(decoded)
                    if len(output_lines) % 10 == 0:
                        print(f"  ... {decoded[:80]}")
            
            exit_code = stdout.channel.recv_exit_status()
            output = '\n'.join(output_lines)
            
            if exit_code == 0 or 'Successfully installed' in output:
                print("  [OK] 依赖安装完成")
                
                # 验证关键包
                print("\n验证关键包...")
                stdin, stdout, stderr = ssh.exec_command(f'{deploy_dir}/venv/bin/pip list | grep -E "(pyrogram|fastapi|uvicorn)"')
                packages = stdout.read().decode('utf-8')
                print(f"  已安装: {packages.strip()}")
                
                # 重启服务
                print("\n重启服务...")
                stdin, stdout, stderr = ssh.exec_command('sudo systemctl restart group-ai-worker 2>&1')
                time.sleep(5)
                
                stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active group-ai-worker 2>&1')
                status = stdout.read().decode('utf-8').strip()
                print(f"  服务状态: {status}")
                
                if 'active' in status:
                    print("\n" + "="*60)
                    print("🎉 部署完成！服务已启动！")
                    print("="*60)
                else:
                    print("\n查看服务日志...")
                    stdin, stdout, stderr = ssh.exec_command('sudo journalctl -u group-ai-worker -n 10 --no-pager 2>&1')
                    logs = stdout.read().decode('utf-8')
                    for line in logs.strip().split('\n')[:10]:
                        if line.strip():
                            print(f"  {line}")
                
                ssh.close()
                return True
            else:
                error = stderr.read().decode('utf-8')
                print(f"  [FAIL] 依赖安装失败")
                print(f"  错误: {error[-500:]}")
                ssh.close()
                return False
                
        except Exception as e:
            print(f"[FAIL] 错误: {e}")
            import traceback
            traceback.print_exc()
            ssh.close()
            return False

if __name__ == "__main__":
    fix_pip_and_install()

