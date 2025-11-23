#!/usr/bin/env python3
"""
最终修复：修复启动脚本并安装pyrogram
"""
import json
import paramiko
from pathlib import Path
import time

def final_fix():
    """最终修复"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"最终修复: {node_id}")
        print(f"{'='*60}\n")
        
        host = server_config['host']
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=5)
        
        try:
            # 1. 修复启动脚本
            print("[1/3] 修复启动脚本...")
            start_script = f"""#!/bin/bash
cd {deploy_dir}
source {deploy_dir}/venv/bin/activate
export PYTHONPATH={deploy_dir}:$PYTHONPATH

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
                print("  [OK] 启动脚本已修复")
            else:
                error = stderr.read().decode('utf-8')
                print(f"  [FAIL] 启动脚本修复失败: {error}")
                return False
            
            # 2. 重新安装pyrogram
            print("\n[2/3] 重新安装pyrogram（这需要3-5分钟）...")
            stdin, stdout, stderr = ssh.exec_command(
                f'cd {deploy_dir} && {deploy_dir}/venv/bin/pip uninstall -y pyrogram tgcrypto 2>&1'
            )
            time.sleep(2)
            
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
                    if 'Installing' in decoded or 'Successfully' in decoded or 'Collecting' in decoded:
                        print(f"  {decoded[:100]}")
            
            exit_code = stdout.channel.recv_exit_status()
            output = '\n'.join(output_lines)
            
            if exit_code == 0 or 'Successfully installed' in output:
                print("  [OK] pyrogram安装完成")
            else:
                error = stderr.read().decode('utf-8')
                print(f"  [WARN] 可能有问题: {error[-200:]}")
            
            # 3. 验证并重启
            print("\n[3/3] 验证pyrogram并重启服务...")
            stdin, stdout, stderr = ssh.exec_command(
                f'{deploy_dir}/venv/bin/python -c "import pyrogram; print(pyrogram.__version__)" 2>&1'
            )
            result = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()
            
            if result and 'version' not in error.lower() and 'ModuleNotFoundError' not in error:
                print(f"  [OK] pyrogram版本: {result}")
            else:
                print(f"  [FAIL] pyrogram验证失败")
                print(f"  错误: {error}")
                # 列出已安装的包
                stdin, stdout, stderr = ssh.exec_command(f'{deploy_dir}/venv/bin/pip list | grep -i pyro')
                packages = stdout.read().decode('utf-8')
                print(f"  已安装的pyro相关包: {packages}")
                return False
            
            # 重启服务
            print("\n重启服务...")
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl restart group-ai-worker 2>&1')
            time.sleep(5)
            
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active group-ai-worker 2>&1')
            status = stdout.read().decode('utf-8').strip()
            print(f"  服务状态: {status}")
            
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
    final_fix()

