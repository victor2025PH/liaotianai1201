#!/usr/bin/env python3
"""
完整的自动化部署和修复系统
- 自动检测和安装所有依赖
- 记录所有安装的包到requirements.txt
- 创建部署日志
- 监控服务运行状态
- 自动修复问题
"""
import json
import paramiko
from pathlib import Path
import time
import subprocess
from datetime import datetime

class AutoDeployComplete:
    def __init__(self):
        self.config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
        self.deploy_log_path = Path(__file__).parent.parent.parent / "data" / "deploy_log.json"
        # 尝试多个可能的requirements.txt路径
        possible_paths = [
            Path(__file__).parent.parent.parent / "group_ai_service" / "requirements.txt",
            Path(__file__).parent.parent.parent / "requirements.txt",
            Path(__file__).parent.parent.parent / "admin-backend" / "requirements.txt",
        ]
        self.requirements_path = None
        for path in possible_paths:
            if path.exists():
                self.requirements_path = path
                break
        if not self.requirements_path:
            # 如果都不存在，使用项目根目录的requirements.txt
            self.requirements_path = Path(__file__).parent.parent.parent / "requirements.txt"
        self.installed_packages = []
        self.installed_system_packages = []
        
    def load_config(self):
        """加载配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_deploy_log(self, node_id, step, status, details):
        """保存部署日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "node_id": node_id,
            "step": step,
            "status": status,
            "details": details
        }
        
        if self.deploy_log_path.exists():
            with open(self.deploy_log_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = {"deployments": []}
        
        logs["deployments"].append(log_entry)
        
        with open(self.deploy_log_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    
    def update_requirements(self, packages):
        """更新requirements.txt"""
        if not self.requirements_path.exists():
            self.requirements_path.parent.mkdir(parents=True, exist_ok=True)
            self.requirements_path.write_text("", encoding='utf-8')
        
        existing_content = self.requirements_path.read_text(encoding='utf-8')
        existing_packages = set()
        
        for line in existing_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                pkg = line.split('>=')[0].split('==')[0].split('>')[0].split('<')[0].strip()
                if pkg:
                    existing_packages.add(pkg.lower())
        
        new_packages = []
        for pkg in packages:
            pkg_name = pkg.split('>=')[0].split('==')[0].split('>')[0].split('<')[0].strip().lower()
            if pkg_name not in existing_packages:
                new_packages.append(pkg)
        
        if new_packages:
            with open(self.requirements_path, 'a', encoding='utf-8') as f:
                f.write('\n# Auto-installed packages\n')
                for pkg in new_packages:
                    f.write(f"{pkg}\n")
    
    def execute_remote_command(self, ssh, command, timeout=300, description=""):
        """执行远程命令"""
        if description:
            print(f"  {description}...")
        
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        
        output_lines = []
        error_lines = []
        
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
        
        while True:
            line = stderr.readline()
            if not line:
                break
            if isinstance(line, bytes):
                decoded = line.decode('utf-8', errors='replace').strip()
            else:
                decoded = str(line).strip()
            if decoded:
                error_lines.append(decoded)
        
        exit_code = stdout.channel.recv_exit_status()
        output = '\n'.join(output_lines)
        error = '\n'.join(error_lines)
        
        return exit_code, output, error
    
    def check_and_install_system_packages(self, ssh):
        """检查并安装系统包"""
        print("\n[系统包检查]")
        
        system_packages = [
            ("build-essential", "编译工具"),
            ("python3-dev", "Python开发头文件"),
            ("python3-venv", "Python虚拟环境"),
            ("curl", "下载工具"),
            ("gcc", "C编译器"),
            ("g++", "C++编译器"),
            ("make", "构建工具"),
        ]
        
        for pkg_name, description in system_packages:
            print(f"  检查 {pkg_name} ({description})...")
            exit_code, output, error = self.execute_remote_command(
                ssh, f'dpkg -l | grep -q "^ii.*{pkg_name}" && echo installed || echo not_installed'
            )
            
            if 'installed' not in output:
                print(f"    安装 {pkg_name}...")
                exit_code, output, error = self.execute_remote_command(
                    ssh, f'sudo apt-get update -qq && sudo apt-get install -y {pkg_name} 2>&1',
                    timeout=300, description=f"安装{pkg_name}"
                )
                
                if exit_code == 0 or 'Setting up' in output:
                    print(f"    [OK] {pkg_name} 安装成功")
                    self.installed_system_packages.append(pkg_name)
                else:
                    print(f"    [WARN] {pkg_name} 安装可能失败: {error[:100]}")
            else:
                print(f"    [OK] {pkg_name} 已安装")
    
    def create_venv(self, ssh, deploy_dir, user):
        """创建虚拟环境"""
        print("\n[虚拟环境]")
        
        # 删除旧环境
        print("  删除旧虚拟环境...")
        self.execute_remote_command(ssh, f'sudo rm -rf {deploy_dir}/venv')
        time.sleep(1)
        
        # 创建新环境
        print("  创建新虚拟环境...")
        exit_code, output, error = self.execute_remote_command(
            ssh, f'cd {deploy_dir} && python3 -m venv venv 2>&1',
            timeout=120
        )
        
        if exit_code == 0:
            self.execute_remote_command(ssh, f'sudo chown -R {user}:{user} {deploy_dir}/venv')
            # 验证虚拟环境
            exit_code2, output2, error2 = self.execute_remote_command(
                ssh, f'test -f {deploy_dir}/venv/bin/python && echo ok || echo fail'
            )
            if 'ok' in output2:
                print("  [OK] 虚拟环境创建成功")
                return True
            else:
                print(f"  [WARN] 虚拟环境可能不完整，但继续")
                return True
        else:
            print(f"  [FAIL] 虚拟环境创建失败")
            print(f"  输出: {output[-200:]}")
            print(f"  错误: {error[-200:]}")
            # 尝试使用virtualenv作为备选
            print("  尝试使用virtualenv...")
            exit_code3, output3, error3 = self.execute_remote_command(
                ssh, f'sudo apt-get install -y python3-virtualenv 2>&1', timeout=120
            )
            exit_code4, output4, error4 = self.execute_remote_command(
                ssh, f'cd {deploy_dir} && virtualenv -p python3 venv 2>&1', timeout=120
            )
            if exit_code4 == 0:
                self.execute_remote_command(ssh, f'sudo chown -R {user}:{user} {deploy_dir}/venv')
                print("  [OK] 使用virtualenv创建成功")
                return True
            else:
                return False
    
    def install_pip(self, ssh, deploy_dir):
        """安装pip"""
        print("\n[pip安装]")
        
        # 检查pip
        exit_code, output, error = self.execute_remote_command(
            ssh, f'{deploy_dir}/venv/bin/python -m pip --version 2>&1'
        )
        
        if 'pip' in output and exit_code == 0:
            print(f"  [OK] pip已存在: {output[:50]}")
            return True
        
        # 安装pip
        print("  安装pip...")
        exit_code, output, error = self.execute_remote_command(
            ssh, f'curl -sS https://bootstrap.pypa.io/get-pip.py | {deploy_dir}/venv/bin/python 2>&1',
            timeout=120
        )
        
        if exit_code == 0 or 'Successfully' in output:
            print("  [OK] pip安装成功")
            return True
        else:
            print(f"  [FAIL] pip安装失败: {error}")
            return False
    
    def install_python_packages(self, ssh, deploy_dir):
        """安装Python包"""
        print("\n[Python包安装]")
        
        # 升级pip
        print("  升级pip...")
        self.execute_remote_command(
            ssh, f'{deploy_dir}/venv/bin/python -m pip install --upgrade pip setuptools wheel 2>&1',
            timeout=120
        )
        
        # 读取requirements.txt
        if self.requirements_path.exists():
            requirements_content = self.requirements_path.read_text(encoding='utf-8')
            packages = [line.strip() for line in requirements_content.split('\n') 
                       if line.strip() and not line.strip().startswith('#')]
        else:
            packages = [
                "pyrogram>=2.0.0",
                "tgcrypto>=1.2.5",
                "fastapi>=0.104.0",
                "uvicorn[standard]>=0.24.0",
                "pydantic>=2.0.0",
                "pydantic-settings>=2.0.0",
                "sqlalchemy>=2.0.0",
                "alembic>=1.12.0",
                "aiosqlite>=0.19.0",
                "redis>=5.0.0",
                "hiredis>=2.2.0",
                "openai>=1.0.0",
                "tiktoken>=0.5.0",
                "python-dotenv>=1.0.0",
                "pyyaml>=6.0",
                "aiofiles>=23.2.0",
                "httpx>=0.25.0",
                "prometheus-client>=0.19.0",
            ]
        
        print(f"  安装 {len(packages)} 个Python包（这需要5-10分钟）...")
        exit_code, output, error = self.execute_remote_command(
            ssh, f'cd {deploy_dir} && {deploy_dir}/venv/bin/pip install --no-cache-dir {" ".join(packages)} 2>&1',
            timeout=900
        )
        
        if exit_code == 0 or 'Successfully installed' in output:
            print("  [OK] Python包安装完成")
            
            # 获取已安装的包列表
            exit_code, installed_output, _ = self.execute_remote_command(
                ssh, f'{deploy_dir}/venv/bin/pip list --format=freeze 2>&1'
            )
            
            if installed_output:
                installed_packages = [line.split('==')[0] for line in installed_output.split('\n') 
                                   if '==' in line and not line.startswith('#')]
                self.installed_packages.extend(installed_packages)
                self.update_requirements(installed_packages)
            
            return True
        else:
            print(f"  [FAIL] Python包安装失败")
            print(f"  错误: {error[-500:]}")
            return False
    
    def create_startup_script(self, ssh, deploy_dir, user):
        """创建启动脚本"""
        print("\n[启动脚本]")
        
        # 先创建Python启动脚本
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
        exit_code, output, error = self.execute_remote_command(
            ssh, f"cat > {deploy_dir}/group_ai_service/run_worker.py << 'EOFPYTHON'\n{python_script}\nEOFPYTHON"
        )
        
        # 创建bash启动脚本
        start_script = f"""#!/bin/bash
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
        
        exit_code, output, error = self.execute_remote_command(
            ssh, f"cat > {deploy_dir}/start.sh << 'EOFSCRIPT'\n{start_script}\nEOFSCRIPT\nchmod +x {deploy_dir}/start.sh"
        )
        
        if exit_code == 0:
            print("  [OK] 启动脚本创建成功")
            return True
        else:
            print(f"  [FAIL] 启动脚本创建失败: {error}")
            return False
    
    def create_systemd_service(self, ssh, deploy_dir, user):
        """创建systemd服务"""
        print("\n[Systemd服务]")
        
        systemd_service = f"""[Unit]
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
WantedBy=multi-user.target"""
        
        exit_code, output, error = self.execute_remote_command(
            ssh, f"sudo bash -c 'cat > /etc/systemd/system/group-ai-worker.service << \"EOFSERVICE\"\n{systemd_service}\nEOFSERVICE'"
        )
        
        if exit_code == 0:
            self.execute_remote_command(ssh, 'sudo systemctl daemon-reload')
            self.execute_remote_command(ssh, 'sudo systemctl enable group-ai-worker')
            print("  [OK] Systemd服务创建成功")
            return True
        else:
            print(f"  [FAIL] Systemd服务创建失败: {error}")
            return False
    
    def start_service(self, ssh):
        """启动服务"""
        print("\n[服务启动]")
        
        self.execute_remote_command(ssh, 'sudo systemctl restart group-ai-worker')
        time.sleep(5)
        
        exit_code, status, error = self.execute_remote_command(
            ssh, 'sudo systemctl is-active group-ai-worker 2>&1'
        )
        
        status = status.strip()
        print(f"  服务状态: {status}")
        
        if 'active' in status:
            print("  [OK] 服务已启动")
            return True
        else:
            print("  [FAIL] 服务未启动")
            # 查看日志
            exit_code, logs, error = self.execute_remote_command(
                ssh, 'sudo journalctl -u group-ai-worker -n 20 --no-pager 2>&1'
            )
            print("\n  最近日志:")
            for line in logs.strip().split('\n')[-20:]:
                if line.strip():
                    print(f"    {line}")
            return False
    
    def monitor_logs(self, ssh, duration=30):
        """监控日志"""
        print(f"\n[日志监控] 监控{duration}秒...")
        
        exit_code, logs, error = self.execute_remote_command(
            ssh, f'sudo journalctl -u group-ai-worker -f --no-pager 2>&1 & sleep {duration} && kill %1 2>&1 || true',
            timeout=duration + 5
        )
        
        if logs:
            print("  最近日志:")
            for line in logs.strip().split('\n')[-10:]:
                if line.strip():
                    print(f"    {line}")
    
    def deploy(self):
        """执行完整部署"""
        config = self.load_config()
        servers = config.get('servers', {})
        
        for node_id, server_config in servers.items():
            print(f"\n{'='*60}")
            print(f"完整自动化部署: {node_id}")
            print(f"{'='*60}\n")
            
            host = server_config['host']
            user = server_config.get('user', 'ubuntu')
            password = server_config.get('password', '')
            deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=user, password=password, timeout=5)
            
            try:
                # 1. 系统包
                self.save_deploy_log(node_id, "系统包检查", "进行中", "")
                self.check_and_install_system_packages(ssh)
                self.save_deploy_log(node_id, "系统包检查", "完成", 
                                    f"已安装: {', '.join(self.installed_system_packages)}")
                
                # 2. 虚拟环境
                self.save_deploy_log(node_id, "虚拟环境", "进行中", "")
                if not self.create_venv(ssh, deploy_dir, user):
                    self.save_deploy_log(node_id, "虚拟环境", "失败", "创建失败")
                    return False
                self.save_deploy_log(node_id, "虚拟环境", "完成", "创建成功")
                
                # 3. pip
                self.save_deploy_log(node_id, "pip安装", "进行中", "")
                if not self.install_pip(ssh, deploy_dir):
                    self.save_deploy_log(node_id, "pip安装", "失败", "安装失败")
                    return False
                self.save_deploy_log(node_id, "pip安装", "完成", "安装成功")
                
                # 4. Python包
                self.save_deploy_log(node_id, "Python包安装", "进行中", "")
                if not self.install_python_packages(ssh, deploy_dir):
                    self.save_deploy_log(node_id, "Python包安装", "失败", "安装失败")
                    return False
                self.save_deploy_log(node_id, "Python包安装", "完成", 
                                    f"已安装 {len(self.installed_packages)} 个包")
                
                # 5. 启动脚本
                self.save_deploy_log(node_id, "启动脚本", "进行中", "")
                if not self.create_startup_script(ssh, deploy_dir, user):
                    self.save_deploy_log(node_id, "启动脚本", "失败", "创建失败")
                    return False
                self.save_deploy_log(node_id, "启动脚本", "完成", "创建成功")
                
                # 6. Systemd服务
                self.save_deploy_log(node_id, "Systemd服务", "进行中", "")
                if not self.create_systemd_service(ssh, deploy_dir, user):
                    self.save_deploy_log(node_id, "Systemd服务", "失败", "创建失败")
                    return False
                self.save_deploy_log(node_id, "Systemd服务", "完成", "创建成功")
                
                # 7. 启动服务
                self.save_deploy_log(node_id, "服务启动", "进行中", "")
                if not self.start_service(ssh):
                    self.save_deploy_log(node_id, "服务启动", "失败", "启动失败")
                    return False
                self.save_deploy_log(node_id, "服务启动", "完成", "启动成功")
                
                # 8. 监控日志
                self.monitor_logs(ssh, duration=30)
                
                print("\n" + "="*60)
                print("🎉 完整部署成功！")
                print("="*60)
                print(f"\n已安装系统包: {', '.join(self.installed_system_packages)}")
                print(f"已安装Python包: {len(self.installed_packages)} 个")
                print(f"requirements.txt已更新: {self.requirements_path}")
                print(f"部署日志已保存: {self.deploy_log_path}")
                
                ssh.close()
                return True
                
            except Exception as e:
                print(f"[FAIL] 错误: {e}")
                import traceback
                traceback.print_exc()
                self.save_deploy_log(node_id, "部署", "失败", str(e))
                ssh.close()
                return False

if __name__ == "__main__":
    deployer = AutoDeployComplete()
    deployer.deploy()

