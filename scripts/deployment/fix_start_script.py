#!/usr/bin/env python3
"""
修复启动脚本
"""
import json
import paramiko
from pathlib import Path

def fix_start_script():
    """修复启动脚本"""
    config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"修复启动脚本: {node_id}")
        print(f"{'='*60}\n")
        
        host = server_config['host']
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=5)
        
        try:
            # 创建Python启动脚本
            python_script = """import asyncio
import logging
from service_manager import ServiceManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info('初始化ServiceManager...')
    sm = ServiceManager()
    logger.info('ServiceManager初始化完成，保持运行...')
    # 保持运行
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
"""
            
            # 写入Python脚本
            stdin, stdout, stderr = ssh.exec_command(
                f"cat > {deploy_dir}/group_ai_service/run_worker.py << 'EOFPYTHON'\n{python_script}\nEOFPYTHON"
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  [OK] Python启动脚本创建成功")
            else:
                error = stderr.read().decode('utf-8')
                print(f"  [FAIL] Python启动脚本创建失败: {error}")
                return False
            
            # 创建bash启动脚本
            bash_script = f"""#!/bin/bash
cd {deploy_dir}
source {deploy_dir}/venv/bin/activate
export PYTHONPATH={deploy_dir}:$PYTHONPATH

if [ -d "group_ai_service" ]; then
    cd group_ai_service
    {deploy_dir}/venv/bin/python run_worker.py
else
    echo "Worker service placeholder - waiting..."
    sleep infinity
fi"""
            
            stdin, stdout, stderr = ssh.exec_command(
                f"cat > {deploy_dir}/start.sh << 'EOFBASH'\n{bash_script}\nEOFBASH\nchmod +x {deploy_dir}/start.sh"
            )
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print("  [OK] Bash启动脚本更新成功")
            else:
                error = stderr.read().decode('utf-8')
                print(f"  [FAIL] Bash启动脚本更新失败: {error}")
                return False
            
            # 重启服务
            print("\n重启服务...")
            ssh.exec_command('sudo systemctl restart group-ai-worker')
            import time
            time.sleep(5)
            
            stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active group-ai-worker 2>&1')
            status = stdout.read().decode('utf-8').strip()
            print(f"  服务状态: {status}")
            
            if 'active' in status:
                print("\n" + "="*60)
                print("🎉 启动脚本修复成功！服务已启动！")
                print("="*60)
            else:
                print("\n查看服务日志...")
                stdin, stdout, stderr = ssh.exec_command('sudo journalctl -u group-ai-worker -n 20 --no-pager 2>&1')
                logs = stdout.read().decode('utf-8')
                print("最近日志:")
                for line in logs.strip().split('\n')[-20:]:
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
    fix_start_script()

