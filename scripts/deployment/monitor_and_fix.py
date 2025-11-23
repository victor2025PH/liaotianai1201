#!/usr/bin/env python3
"""
监控服务日志并自动修复问题
"""
import json
import paramiko
from pathlib import Path
import time
import re

class ServiceMonitor:
    def __init__(self):
        self.config_path = Path(__file__).parent.parent.parent / "data" / "master_config.json"
        self.fix_log_path = Path(__file__).parent.parent.parent / "data" / "fix_log.json"
        
    def load_config(self):
        """加载配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_service_logs(self, ssh, lines=50):
        """获取服务日志"""
        stdin, stdout, stderr = ssh.exec_command(
            f'sudo journalctl -u group-ai-worker -n {lines} --no-pager 2>&1'
        )
        logs = stdout.read().decode('utf-8')
        return logs
    
    def detect_missing_module(self, logs):
        """检测缺失的模块"""
        pattern = r"ModuleNotFoundError: No module named '([^']+)'"
        matches = re.findall(pattern, logs)
        return matches
    
    def install_missing_package(self, ssh, deploy_dir, package_name):
        """安装缺失的包"""
        print(f"  安装缺失的包: {package_name}...")
        stdin, stdout, stderr = ssh.exec_command(
            f'cd {deploy_dir} && {deploy_dir}/venv/bin/pip install {package_name} 2>&1',
            timeout=300
        )
        
        output = stdout.read().decode('utf-8')
        exit_code = stdout.channel.recv_exit_status()
        
        if exit_code == 0 or 'Successfully installed' in output:
            print(f"    [OK] {package_name} 安装成功")
            return True
        else:
            error = stderr.read().decode('utf-8')
            print(f"    [FAIL] {package_name} 安装失败: {error[-200:]}")
            return False
    
    def restart_service(self, ssh):
        """重启服务"""
        print("  重启服务...")
        ssh.exec_command('sudo systemctl restart group-ai-worker')
        time.sleep(5)
        
        stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active group-ai-worker 2>&1')
        status = stdout.read().decode('utf-8').strip()
        return status
    
    def monitor_and_fix(self, duration=300):
        """监控并自动修复"""
        config = self.load_config()
        servers = config.get('servers', {})
        
        for node_id, server_config in servers.items():
            print(f"\n{'='*60}")
            print(f"监控并修复服务: {node_id}")
            print(f"{'='*60}\n")
            
            host = server_config['host']
            user = server_config.get('user', 'ubuntu')
            password = server_config.get('password', '')
            deploy_dir = server_config.get('deploy_dir', '/opt/group-ai')
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=user, password=password, timeout=5)
            
            try:
                start_time = time.time()
                fix_count = 0
                
                while time.time() - start_time < duration:
                    # 获取日志
                    logs = self.get_service_logs(ssh, lines=30)
                    
                    # 检测缺失的模块
                    missing_modules = self.detect_missing_module(logs)
                    
                    if missing_modules:
                        print(f"\n检测到缺失的模块: {', '.join(missing_modules)}")
                        
                        for module in missing_modules:
                            # 将模块名转换为包名
                            package_name = module.replace('_', '-')
                            
                            if self.install_missing_package(ssh, deploy_dir, package_name):
                                fix_count += 1
                                
                                # 更新requirements.txt
                                requirements_path = Path(__file__).parent.parent.parent / "requirements.txt"
                                if requirements_path.exists():
                                    content = requirements_path.read_text(encoding='utf-8')
                                    if package_name not in content:
                                        with open(requirements_path, 'a', encoding='utf-8') as f:
                                            f.write(f"\n{package_name}\n")
                                
                                # 重启服务
                                status = self.restart_service(ssh)
                                print(f"  服务状态: {status}")
                                
                                if 'active' in status:
                                    print(f"  [OK] 服务已启动")
                                    break
                    else:
                        # 检查服务状态
                        stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active group-ai-worker 2>&1')
                        status = stdout.read().decode('utf-8').strip()
                        
                        if 'active' in status:
                            print(f"\n[OK] 服务运行正常 (状态: {status})")
                            break
                        else:
                            print(f"\n服务状态: {status}")
                            print("等待服务启动...")
                            time.sleep(10)
                
                print(f"\n修复完成，共修复 {fix_count} 个问题")
                
                # 最终状态
                logs = self.get_service_logs(ssh, lines=20)
                print("\n最近日志:")
                for line in logs.strip().split('\n')[-10:]:
                    if line.strip():
                        print(f"  {line}")
                
                ssh.close()
                
            except Exception as e:
                print(f"[FAIL] 错误: {e}")
                import traceback
                traceback.print_exc()
                ssh.close()

if __name__ == "__main__":
    monitor = ServiceMonitor()
    monitor.monitor_and_fix(duration=300)

