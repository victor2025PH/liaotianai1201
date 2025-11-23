#!/usr/bin/env python3
"""
立即安装依赖
"""
import json
import paramiko
from pathlib import Path
import time

def install_deps():
    """安装依赖"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"安装依赖: {node_id}")
        print(f"{'='*60}\n")
        
        host = server_config['host']
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=5)
        
        try:
            # 使用python -m pip安装
            print("使用python -m pip安装依赖...")
            stdin, stdout, stderr = ssh.exec_command(
                f'cd {deploy_dir} && {deploy_dir}/venv/bin/python -m pip install -r requirements.txt 2>&1',
                timeout=900
            )
            
            # 读取输出
            output_lines = []
            while True:
                line = stdout.readline()
                if not line:
                    break
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded:
                    output_lines.append(decoded)
                    if 'Installing' in decoded or 'Successfully' in decoded:
                        print(f"  {decoded[:80]}")
            
            exit_code = stdout.channel.recv_exit_status()
            output = '\n'.join(output_lines)
            
            if exit_code == 0 or 'Successfully installed' in output:
                print("\n[OK] 依赖安装完成")
                
                # 验证pyrogram
                print("\n验证pyrogram...")
                stdin, stdout, stderr = ssh.exec_command(f'{deploy_dir}/venv/bin/python -c "import pyrogram; print(pyrogram.__version__)" 2>&1')
                result = stdout.read().decode('utf-8').strip()
                if result:
                    print(f"  pyrogram版本: {result}")
                else:
                    error = stderr.read().decode('utf-8')
                    print(f"  [FAIL] pyrogram未安装: {error}")
                
                # 重启服务
                print("\n重启服务...")
                stdin, stdout, stderr = ssh.exec_command('sudo systemctl restart group-ai-worker 2>&1')
                time.sleep(5)
                
                stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active group-ai-worker 2>&1')
                status = stdout.read().decode('utf-8').strip()
                print(f"服务状态: {status}")
                
                if 'active' in status:
                    print("\n" + "="*60)
                    print("🎉 服务已启动！")
                    print("="*60)
                else:
                    print("\n查看日志...")
                    stdin, stdout, stderr = ssh.exec_command('sudo journalctl -u group-ai-worker -n 10 --no-pager 2>&1')
                    logs = stdout.read().decode('utf-8')
                    for line in logs.strip().split('\n')[:10]:
                        if line.strip():
                            print(f"  {line}")
                
                ssh.close()
                return True
            else:
                error = stderr.read().decode('utf-8')
                print(f"\n[FAIL] 安装失败")
                print(f"错误: {error[-500:]}")
                ssh.close()
                return False
                
        except Exception as e:
            print(f"[FAIL] 错误: {e}")
            import traceback
            traceback.print_exc()
            ssh.close()
            return False

if __name__ == "__main__":
    install_deps()

