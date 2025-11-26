#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传 utils 模块到服务器
"""

import json
import paramiko
import sys
import time
import tarfile
import io
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

def upload_directory(sftp, local_dir, remote_dir, ssh):
    """上传目录"""
    local_path = Path(local_dir)
    
    print(f"\n准备上传: {local_path} -> {remote_dir}")
    
    # 创建远程目录
    ssh.exec_command(f"mkdir -p {remote_dir}")
    
    # 使用 tar 压缩并上传
    print("  创建压缩包...")
    tar_buffer = io.BytesIO()
    
    with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
        tar.add(local_path, arcname=local_path.name, recursive=True)
    
    tar_buffer.seek(0)
    tar_size = len(tar_buffer.getvalue())
    print(f"  压缩包大小: {tar_size / 1024:.2f} KB")
    
    # 上传压缩包
    remote_tar = f"{remote_dir}/utils.tar.gz"
    print(f"  上传到: {remote_tar}")
    
    with sftp.open(remote_tar, 'wb') as f:
        f.write(tar_buffer.getvalue())
    
    print("  [OK] 上传完成")
    
    # 解压
    print("  解压...")
    stdin, stdout, stderr = ssh.exec_command(f"cd {remote_dir} && tar -xzf utils.tar.gz && rm -f utils.tar.gz")
    stdout.channel.recv_exit_status()
    
    return f"{remote_dir}/{local_path.name}"

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
            for line in output.split('\n')[:30]:
                if line.strip():
                    print(f"  {line}")
        if error and exit_status != 0:
            for line in error.split('\n')[:10]:
                if line.strip():
                    print(f"  [ERROR] {line}")
    
    return exit_status == 0, output, error

def main():
    config = load_config()
    
    print("=" * 70)
    print("上传 utils 模块到服务器")
    print("=" * 70)
    
    # 检查本地 utils 目录
    project_root = Path(__file__).parent.parent.parent
    utils_dir = project_root / "utils"
    
    if not utils_dir.exists():
        print(f"[ERROR] utils 目录不存在: {utils_dir}")
        return
    
    print(f"\n本地 utils 目录: {utils_dir}")
    
    ssh = connect_server(config['host'], config['user'], config['password'])
    sftp = ssh.open_sftp()
    
    try:
        backend_dir = "/home/ubuntu/admin-backend"
        
        # 上传 utils 目录到后端目录
        print("\n" + "=" * 70)
        print("上传 utils 模块")
        print("=" * 70)
        
        remote_utils = upload_directory(sftp, utils_dir, backend_dir, ssh)
        print(f"[OK] utils 模块已上传到: {remote_utils}")
        
        # 验证文件
        print("\n验证上传的文件...")
        execute_command(ssh, f"ls -la {remote_utils}/", "检查 utils 目录内容")
        execute_command(ssh, f"test -f {remote_utils}/session_encryption.py && echo 'exists' || echo 'not found'", "检查 session_encryption.py", show_output=False)
        execute_command(ssh, f"test -f {remote_utils}/session_permissions.py && echo 'exists' || echo 'not found'", "检查 session_permissions.py", show_output=False)
        execute_command(ssh, f"test -f {remote_utils}/session_audit.py && echo 'exists' || echo 'not found'", "检查 session_audit.py", show_output=False)
        
        # 测试导入
        print("\n测试 Python 导入...")
        test_cmd = f"""
        cd {backend_dir}
        source .venv/bin/activate
        python3 -c "import sys; sys.path.insert(0, '{backend_dir}'); from utils.session_encryption import get_session_manager; print('Import successful')" 2>&1
        """
        success, output, error = execute_command(ssh, test_cmd, "测试 utils 模块导入")
        
        if 'successful' in output.lower():
            print("  [OK] utils 模块可以正常导入")
        else:
            print("  [WARNING] utils 模块导入可能有问题")
        
        # 重启服务
        print("\n" + "=" * 70)
        print("重启后端服务")
        print("=" * 70)
        
        execute_command(ssh, "sudo systemctl restart admin-backend", "重启服务")
        time.sleep(5)
        
        success, output, _ = execute_command(ssh, "systemctl is-active admin-backend", "检查服务状态", show_output=False)
        if 'active' in output:
            print("  [OK] 后端服务已启动")
        else:
            print("  [WARNING] 后端服务可能未启动")
            execute_command(ssh, "sudo journalctl -u admin-backend -n 30 --no-pager", "查看服务日志")
        
        # 验证
        success, output, _ = execute_command(ssh, "curl -s http://localhost:8000/health", "后端健康检查", show_output=False)
        if 'ok' in output.lower():
            print("  [OK] 后端健康检查通过")
        else:
            print(f"  [WARNING] 后端健康检查: {output}")
        
        print("\n" + "=" * 70)
        print("完成！")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[ERROR] 上传过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sftp.close()
        ssh.close()

if __name__ == "__main__":
    main()


