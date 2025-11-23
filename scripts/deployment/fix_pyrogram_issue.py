#!/usr/bin/env python3
"""
修复pyrogram依赖问题
"""
import json
import paramiko
from pathlib import Path
import time

def fix_pyrogram():
    """修复pyrogram依赖"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"修复pyrogram依赖: {node_id}")
        print(f"{'='*60}\n")
        
        host = server_config['host']
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=5)
        
        try:
            # 1. 检查Python和pip
            print("[1/5] 检查Python环境...")
            stdin, stdout, stderr = ssh.exec_command(f'{deploy_dir}/venv/bin/python --version 2>&1')
            python_version = stdout.read().decode('utf-8').strip()
            print(f"  Python版本: {python_version}")
            
            # 检查pip
            stdin, stdout, stderr = ssh.exec_command(f'{deploy_dir}/venv/bin/python -m pip --version 2>&1')
            pip_version = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()
            
            if pip_version and 'pip' in pip_version:
                print(f"  pip可用: {pip_version[:50]}")
            else:
                print("  安装pip...")
                stdin, stdout, stderr = ssh.exec_command(f'{deploy_dir}/venv/bin/python -m ensurepip --upgrade 2>&1', timeout=120)
                exit_code = stdout.channel.recv_exit_status()
                output = stdout.read().decode('utf-8')
                if exit_code == 0 or 'Successfully' in output:
                    print("  [OK] pip已安装")
                else:
                    print(f"  [WARN] pip安装可能失败: {error[:100]}")
                    # 尝试使用get-pip.py
                    print("  尝试使用get-pip.py安装pip...")
                    stdin, stdout, stderr = ssh.exec_command('curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py 2>&1', timeout=60)
                    stdin, stdout, stderr = ssh.exec_command(f'{deploy_dir}/venv/bin/python /tmp/get-pip.py 2>&1', timeout=120)
                    exit_code = stdout.channel.recv_exit_status()
                    if exit_code == 0:
                        print("  [OK] pip已通过get-pip.py安装")
                    else:
                        print("  [FAIL] pip安装失败")
                        return False
            
            # 2. 升级pip
            print("\n[2/5] 升级pip...")
            stdin, stdout, stderr = ssh.exec_command(
                f'{deploy_dir}/venv/bin/python -m pip install --upgrade pip setuptools wheel 2>&1',
                timeout=120
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  [OK] pip升级完成")
            else:
                print("  [WARN] pip升级可能失败，但继续")
            
            # 3. 安装pyrogram和tgcrypto
            print("\n[3/5] 安装pyrogram和tgcrypto...")
            stdin, stdout, stderr = ssh.exec_command(
                f'cd {deploy_dir} && {deploy_dir}/venv/bin/python -m pip install pyrogram tgcrypto 2>&1',
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
                    if 'Installing' in decoded or 'Successfully' in decoded:
                        print(f"  {decoded[:80]}")
            
            exit_code = stdout.channel.recv_exit_status()
            output = '\n'.join(output_lines)
            
            if exit_code == 0 or 'Successfully installed' in output:
                print("  [OK] pyrogram安装完成")
            else:
                error = stderr.read().decode('utf-8')
                print(f"  [FAIL] pyrogram安装失败")
                print(f"  错误: {error[-300:]}")
                return False
            
            # 4. 验证安装
            print("\n[4/5] 验证pyrogram安装...")
            stdin, stdout, stderr = ssh.exec_command(
                f'{deploy_dir}/venv/bin/python -c "import pyrogram; print(f\"pyrogram版本: {{pyrogram.__version__}}\")" 2>&1'
            )
            result = stdout.read().decode('utf-8').strip()
            if result and 'version' in result:
                print(f"  {result}")
            else:
                error = stderr.read().decode('utf-8')
                print(f"  [FAIL] pyrogram验证失败: {error}")
                return False
            
            # 5. 安装其他关键依赖
            print("\n[5/5] 安装其他关键依赖...")
            stdin, stdout, stderr = ssh.exec_command(
                f'cd {deploy_dir} && {deploy_dir}/venv/bin/python -m pip install fastapi uvicorn sqlalchemy aiosqlite 2>&1',
                timeout=300
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  [OK] 关键依赖安装完成")
            else:
                print("  [WARN] 部分依赖可能未安装，但继续")
            
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
    fix_pyrogram()

