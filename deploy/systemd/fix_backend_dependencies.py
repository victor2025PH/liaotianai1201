#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复后端依赖问题 - 安装缺失的模块
"""

import json
import paramiko
import sys
import time
from pathlib import Path

# 设置 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def load_config():
    """加载服务器配置"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    config_path = project_root / "data" / "master_config.json"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    manila_config = config.get('servers', {}).get('manila', {})
    
    return {
        'host': manila_config.get('host', '165.154.233.55'),
        'user': manila_config.get('user', 'ubuntu'),
        'password': manila_config.get('password', 'Along2025!!!'),
    }

def connect_server(host, user, password):
    """连接服务器"""
    print(f"连接服务器: {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    print("[OK] 连接成功")
    return ssh

def execute_command(ssh, command, description, show_output=True):
    """执行命令"""
    if show_output:
        print(f"\n{description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='replace').strip()
    error = stderr.read().decode('utf-8', errors='replace').strip()
    
    if show_output:
        if output:
            for line in output.split('\n')[:50]:
                if line.strip():
                    print(f"  {line}")
        if error and exit_status != 0:
            for line in error.split('\n')[:20]:
                if line.strip():
                    print(f"  [ERROR] {line}")
    
    return exit_status == 0, output, error

def main():
    config = load_config()
    
    print("=" * 70)
    print("修复后端依赖 - 安装缺失的模块")
    print("=" * 70)
    
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        backend_dir = "/home/ubuntu/admin-backend"
        
        # 步骤1: 安装缺失的依赖
        print("\n" + "=" * 70)
        print("步骤 1: 安装缺失的依赖")
        print("=" * 70)
        
        # 安装 pyrogram 和其他可能缺失的依赖
        install_cmd = f"""
        cd {backend_dir}
        source .venv/bin/activate
        pip install pyrogram pyyaml openai 2>&1 | tail -30
        """
        execute_command(ssh, install_cmd, "安装缺失的依赖")
        
        # 检查是否还有其他缺失的依赖
        print("\n检查 requirements.txt 中的所有依赖...")
        check_cmd = f"""
        cd {backend_dir}
        source .venv/bin/activate
        pip install -r requirements.txt 2>&1 | grep -E 'ERROR|error|Failed|Successfully' | tail -20
        """
        execute_command(ssh, check_cmd, "检查所有依赖")
        
        # 步骤2: 验证安装
        print("\n" + "=" * 70)
        print("步骤 2: 验证安装")
        print("=" * 70)
        
        verify_cmd = f"""
        cd {backend_dir}
        source .venv/bin/activate
        python3 -c "import pyrogram; print('pyrogram version:', pyrogram.__version__)" 2>&1
        """
        success, output, error = execute_command(ssh, verify_cmd, "验证 pyrogram 安装")
        
        if success and 'version' in output.lower():
            print("  [OK] pyrogram 已成功安装")
        else:
            print("  [WARNING] pyrogram 验证可能有问题")
        
        # 步骤3: 测试应用启动
        print("\n" + "=" * 70)
        print("步骤 3: 测试应用启动")
        print("=" * 70)
        
        test_cmd = f"""
        cd {backend_dir}
        source .venv/bin/activate
        timeout 5 python3 -c "from app.main import app; print('Import successful')" 2>&1 || echo "Import failed or timeout"
        """
        success, output, error = execute_command(ssh, test_cmd, "测试应用导入")
        
        if 'successful' in output.lower():
            print("  [OK] 应用可以正常导入")
        else:
            print("  [WARNING] 应用导入可能有问题")
            if error:
                print("  错误信息:")
                for line in error.split('\n')[:10]:
                    if line.strip():
                        print(f"    {line}")
        
        # 步骤4: 重启服务
        print("\n" + "=" * 70)
        print("步骤 4: 重启后端服务")
        print("=" * 70)
        
        execute_command(ssh, "sudo systemctl restart admin-backend", "重启服务")
        time.sleep(5)
        
        success, output, _ = execute_command(ssh, "systemctl is-active admin-backend", "检查服务状态", show_output=False)
        if 'active' in output:
            print("  [OK] 后端服务已启动")
        else:
            print("  [WARNING] 后端服务可能未启动")
            print("  查看最新日志:")
            execute_command(ssh, "sudo journalctl -u admin-backend -n 30 --no-pager", "查看服务日志")
        
        # 步骤5: 验证服务
        print("\n" + "=" * 70)
        print("步骤 5: 验证服务")
        print("=" * 70)
        
        execute_command(ssh, "sudo ss -tlnp | grep 8000", "检查端口监听")
        
        success, output, _ = execute_command(ssh, "curl -s http://localhost:8000/health", "后端健康检查", show_output=False)
        if 'ok' in output.lower():
            print("  [OK] 后端健康检查通过")
        else:
            print(f"  [WARNING] 后端健康检查: {output}")
        
        print("\n" + "=" * 70)
        print("修复完成！")
        print("=" * 70)
        print(f"\n如果服务已启动，访问:")
        print(f"  后端: http://{config['host']}:8000")
        print(f"  API 文档: http://{config['host']}:8000/docs")
        
    except Exception as e:
        print(f"\n[ERROR] 修复过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()


