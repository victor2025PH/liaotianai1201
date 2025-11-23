#!/usr/bin/env python3
"""
安装pip并安装依赖
"""
import json
import paramiko
from pathlib import Path
import time

def install_pip_and_deps():
    """安装pip并安装依赖"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"安装pip并依赖: {node_id}")
        print(f"{'='*60}\n")
        
        host = server_config['host']
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=5)
        
        try:
            # 执行完整的安装命令
            commands = f"""
# 1. 下载并安装pip
curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
{deploy_dir}/venv/bin/python /tmp/get-pip.py

# 2. 升级pip
{deploy_dir}/venv/bin/python -m pip install --upgrade pip setuptools wheel

# 3. 安装pyrogram和tgcrypto
{deploy_dir}/venv/bin/python -m pip install pyrogram tgcrypto

# 4. 安装其他关键依赖
cd {deploy_dir}
{deploy_dir}/venv/bin/python -m pip install fastapi uvicorn sqlalchemy aiosqlite pydantic

# 5. 验证安装
{deploy_dir}/venv/bin/python -c "import pyrogram; print('pyrogram OK')"

# 6. 重启服务
sudo systemctl restart group-ai-worker
sleep 5
sudo systemctl is-active group-ai-worker
"""
            
            print("执行安装命令...")
            stdin, stdout, stderr = ssh.exec_command(commands, timeout=900)
            
            # 读取输出
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
                    if 'Installing' in decoded or 'Successfully' in decoded or 'OK' in decoded or 'active' in decoded:
                        print(f"  {decoded[:100]}")
            
            exit_code = stdout.channel.recv_exit_status()
            output = '\n'.join(output_lines)
            
            # 检查结果
            if 'pyrogram OK' in output:
                print("\n[OK] pyrogram安装成功")
            else:
                print("\n[WARN] 可能未完全成功，检查状态...")
            
            # 检查服务状态
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active group-ai-worker 2>&1')
            status = stdout.read().decode('utf-8').strip()
            print(f"\n服务状态: {status}")
            
            if 'active' in status:
                print("\n" + "="*60)
                print("🎉 安装完成！服务已启动！")
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
    install_pip_and_deps()

