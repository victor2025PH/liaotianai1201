#!/usr/bin/env python3
"""
调试并修复pyrogram安装问题
"""
import json
import paramiko
from pathlib import Path
import time

def debug_and_fix():
    """调试并修复"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"调试并修复: {node_id}")
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
            stdin, stdout, stderr = ssh.exec_command(f'ls -la {deploy_dir}/venv/bin/ | head -10')
            venv_bin = stdout.read().decode('utf-8')
            print(f"虚拟环境bin目录:\n{venv_bin}")
            
            # 2. 检查Python路径
            print("\n[2/5] 检查Python路径...")
            stdin, stdout, stderr = ssh.exec_command(f'{deploy_dir}/venv/bin/python -c "import sys; print(sys.executable); print(sys.path[:3])"')
            python_info = stdout.read().decode('utf-8')
            print(f"Python信息:\n{python_info}")
            
            # 3. 检查已安装的包
            print("\n[3/5] 检查已安装的包...")
            stdin, stdout, stderr = ssh.exec_command(f'{deploy_dir}/venv/bin/pip list | grep -E "(pyrogram|tgcrypto|pip|setuptools)"')
            installed = stdout.read().decode('utf-8')
            print(f"已安装的相关包:\n{installed}")
            
            # 4. 尝试安装pyrogram（使用详细输出）
            print("\n[4/5] 安装pyrogram（详细模式）...")
            stdin, stdout, stderr = ssh.exec_command(
                f'cd {deploy_dir} && {deploy_dir}/venv/bin/pip install -v pyrogram tgcrypto 2>&1 | tail -50',
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
                    print(f"  {decoded[:120]}")
            
            exit_code = stdout.channel.recv_exit_status()
            
            # 5. 再次验证
            print("\n[5/5] 验证安装...")
            stdin, stdout, stderr = ssh.exec_command(f'{deploy_dir}/venv/bin/pip list | grep pyrogram')
            pyrogram_check = stdout.read().decode('utf-8')
            print(f"pip list中的pyrogram: {pyrogram_check}")
            
            stdin, stdout, stderr = ssh.exec_command(f'{deploy_dir}/venv/bin/python -c "import sys; sys.path.insert(0, \'{deploy_dir}\'); import pyrogram; print(pyrogram.__version__)" 2>&1')
            import_result = stdout.read().decode('utf-8')
            import_error = stderr.read().decode('utf-8')
            print(f"导入结果: {import_result}")
            if import_error:
                print(f"导入错误: {import_error}")
            
            # 如果还是失败，尝试使用系统Python安装
            if 'ModuleNotFoundError' in import_error or not import_result:
                print("\n尝试使用系统Python安装到虚拟环境...")
                stdin, stdout, stderr = ssh.exec_command(f'python3 -m pip install --target={deploy_dir}/venv/lib/python3.12/site-packages pyrogram tgcrypto 2>&1', timeout=600)
                install_output = stdout.read().decode('utf-8')
                print(f"安装输出: {install_output[-500:]}")
            
            ssh.close()
            return True
            
        except Exception as e:
            print(f"[FAIL] 错误: {e}")
            import traceback
            traceback.print_exc()
            ssh.close()
            return False

if __name__ == "__main__":
    debug_and_fix()

