#!/usr/bin/env python3
"""
快速修复并完成部署
"""
import json
import paramiko
from pathlib import Path
import time

def quick_fix():
    """快速修复部署"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"快速修复部署: {node_id}")
        print(f"{'='*60}\n")
        
        host = server_config['host']
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=5)
        
        try:
            # 执行完整的部署命令序列
            commands = f"""
# 1. 安装python3-venv
sudo apt-get update -qq
sudo apt-get install -y python3-venv || sudo apt-get install -y python3.12-venv || true

# 2. 删除并重新创建虚拟环境
sudo rm -rf {deploy_dir}/venv
cd {deploy_dir}
python3 -m venv venv || virtualenv -p python3 venv
sudo chown -R {user}:{user} {deploy_dir}/venv

# 3. 升级pip
{deploy_dir}/venv/bin/python -m pip install --upgrade pip || {deploy_dir}/venv/bin/pip install --upgrade pip || true

# 4. 安装依赖
cd {deploy_dir}
{deploy_dir}/venv/bin/pip install -r requirements.txt

# 5. 创建启动脚本
cat > {deploy_dir}/start.sh << 'EOFSCRIPT'
#!/bin/bash
cd {deploy_dir}
source venv/bin/activate
export PYTHONPATH={deploy_dir}:$PYTHONPATH

if [ -d "group_ai_service" ]; then
    cd group_ai_service
    {deploy_dir}/venv/bin/python -c "from service_manager import ServiceManager; sm = ServiceManager(); sm.start()"
else
    echo "Worker service placeholder - waiting..."
    sleep infinity
fi
EOFSCRIPT
chmod +x {deploy_dir}/start.sh

# 6. 创建systemd服务
sudo bash -c 'cat > /etc/systemd/system/group-ai-worker.service << "EOFSERVICE"
[Unit]
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
WantedBy=multi-user.target
EOFSERVICE'

# 7. 重新加载并启用服务
sudo systemctl daemon-reload
sudo systemctl enable group-ai-worker
sudo systemctl start group-ai-worker

# 8. 等待并检查状态
sleep 3
sudo systemctl is-active group-ai-worker
sudo systemctl is-enabled group-ai-worker
"""
            
            print("执行完整部署脚本...")
            stdin, stdout, stderr = ssh.exec_command(commands, timeout=900)
            
            # 实时输出
            output_lines = []
            while True:
                line = stdout.readline()
                if not line:
                    break
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded:
                    output_lines.append(decoded)
                    print(f"  {decoded}")
            
            exit_code = stdout.channel.recv_exit_status()
            
            # 检查关键输出
            output_text = '\n'.join(output_lines)
            
            if 'active' in output_text or 'enabled' in output_text:
                print("\n" + "="*60)
                print("🎉 部署完成！")
                print("="*60)
                
                # 查看日志
                print("\n最近服务日志:")
                stdin, stdout, stderr = ssh.exec_command('sudo journalctl -u group-ai-worker -n 10 --no-pager 2>&1')
                logs = stdout.read().decode('utf-8')
                for line in logs.strip().split('\n')[:10]:
                    if line.strip():
                        print(f"  {line}")
            else:
                print("\n" + "="*60)
                print(f"⚠️  部署可能未完全成功，退出码: {exit_code}")
                print("="*60)
            
            ssh.close()
            return True
            
        except Exception as e:
            print(f"[FAIL] 错误: {e}")
            import traceback
            traceback.print_exc()
            ssh.close()
            return False

if __name__ == "__main__":
    quick_fix()

