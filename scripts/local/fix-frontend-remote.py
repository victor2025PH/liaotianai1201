#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
远程修复前端 404 错误
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
        'host': '165.154.233.55',
        'user': manila_config.get('user', 'ubuntu'),
        'password': manila_config.get('password', 'Along2025!!!'),
        'project_dir': '/home/ubuntu/telegram-ai-system',
    }

def connect_server(host, user, password, retries=3):
    """连接服务器"""
    for i in range(retries):
        try:
            print(f"正在连接服务器 {host}... (尝试 {i+1}/{retries})")
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, username=user, password=password, timeout=30)
            print("✅ SSH 连接成功!")
            return client
        except Exception as e:
            if i < retries - 1:
                print(f"⚠️  连接失败: {e}, 3秒后重试...")
                time.sleep(3)
            else:
                print(f"❌ 连接失败: {e}")
                raise
    return None

def run_command(client, command, description="", check_output=True):
    """执行远程命令"""
    if description:
        print(f"\n{'='*60}")
        print(f"📋 {description}")
        print(f"{'='*60}")
    
    try:
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        
        output_lines = []
        error_lines = []
        
        for line in iter(stdout.readline, ""):
            if line:
                line = line.rstrip()
                print(line)
                output_lines.append(line)
        
        for line in iter(stderr.readline, ""):
            if line:
                line = line.rstrip()
                if line and not line.startswith('Warning:'):
                    print(f"⚠️  {line}", file=sys.stderr)
                error_lines.append(line)
        
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0 and check_output:
            error_msg = '\n'.join(error_lines) if error_lines else "命令执行失败"
            raise Exception(f"命令执行失败 (退出码: {exit_status}): {error_msg}")
        
        return '\n'.join(output_lines), '\n'.join(error_lines), exit_status
    
    except Exception as e:
        print(f"❌ 执行命令失败: {e}")
        raise

def main():
    """主函数"""
    print("="*60)
    print("🔧 远程修复前端 404 错误")
    print("="*60)
    print()
    
    config = load_config()
    host = config['host']
    user = config['user']
    password = config['password']
    project_dir = config['project_dir']
    
    client = None
    try:
        client = connect_server(host, user, password)
        
        # 上传修复脚本
        print(f"\n{'='*60}")
        print("📤 上传修复脚本")
        print(f"{'='*60}")
        
        # 读取本地脚本
        script_path = Path(__file__).parent.parent / "server" / "fix-frontend-404.sh"
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # 写入远程文件
        sftp = client.open_sftp()
        remote_script = f"{project_dir}/scripts/server/fix-frontend-404.sh"
        with sftp.file(remote_script, 'w') as f:
            f.write(script_content)
        sftp.chmod(remote_script, 0o755)
        sftp.close()
        
        print("✅ 脚本已上传")
        
        # 执行修复脚本
        run_command(
            client,
            f"cd {project_dir} && sudo bash scripts/server/fix-frontend-404.sh",
            "执行前端修复"
        )
        
        # 检查服务状态
        print(f"\n{'='*60}")
        print("📊 检查服务状态")
        print(f"{'='*60}")
        
        run_command(
            client,
            f"ss -tlnp | grep :3000 || echo '端口 3000 未监听'",
            "检查端口"
        )
        
        run_command(
            client,
            f"ps aux | grep -E 'next.*start|node.*3000' | grep -v grep || echo '未找到前端进程'",
            "检查进程"
        )
        
        print(f"\n{'='*60}")
        print("✅ 修复完成！")
        print(f"{'='*60}")
        print()
        print("📝 下一步:")
        print("   1. 等待 1-2 分钟让前端完全启动")
        print("   2. 刷新浏览器页面: https://aikz.usdt2026.cc")
        print("   3. 如果还有问题，检查日志:")
        print(f"      tail -50 /tmp/frontend.log")
        print()
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        if client:
            client.close()
            print("🔌 SSH 连接已关闭")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

