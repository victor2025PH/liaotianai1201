#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查前端服务状态和静态资源
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
    print("🔍 检查前端服务状态和静态资源")
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
        
        # 1. 检查前端服务状态
        run_command(
            client,
            f"systemctl list-units --type=service | grep -E 'frontend|next' || echo '未找到前端服务'",
            "检查前端服务"
        )
        
        # 2. 检查端口监听
        run_command(
            client,
            f"ss -tlnp | grep :3000 || echo '端口 3000 未监听'",
            "检查端口 3000"
        )
        
        # 3. 检查进程
        run_command(
            client,
            f"ps aux | grep -E 'next|node.*3000' | grep -v grep || echo '未找到前端进程'",
            "检查前端进程"
        )
        
        # 4. 检查 .next 目录
        run_command(
            client,
            f"ls -la {project_dir}/saas-demo/.next/static 2>/dev/null | head -20 || echo '.next/static 目录不存在或无法访问'",
            "检查静态文件目录"
        )
        
        # 5. 检查 Nginx 配置
        run_command(
            client,
            f"sudo nginx -t 2>&1 || echo 'Nginx 未安装或配置错误'",
            "检查 Nginx 配置"
        )
        
        # 6. 检查 Nginx 是否运行
        run_command(
            client,
            f"sudo systemctl status nginx --no-pager -l | head -15 || echo 'Nginx 未运行'",
            "检查 Nginx 状态"
        )
        
        # 7. 检查 Nginx 配置中的静态文件路径
        run_command(
            client,
            f"sudo grep -r 'next/static' /etc/nginx/ 2>/dev/null | head -10 || echo '未找到 next/static 配置'",
            "检查 Nginx 静态文件配置"
        )
        
        # 8. 测试本地访问
        run_command(
            client,
            f"curl -s -o /dev/null -w 'HTTP %{{http_code}}' http://localhost:3000 2>/dev/null || echo '无法访问本地 3000 端口'",
            "测试本地前端访问"
        )
        
        # 9. 检查前端日志
        run_command(
            client,
            f"sudo journalctl -u liaotian-frontend -n 30 --no-pager 2>/dev/null || tail -30 /tmp/frontend.log 2>/dev/null || echo '无日志'",
            "查看前端日志"
        )
        
        print(f"\n{'='*60}")
        print("✅ 检查完成")
        print(f"{'='*60}")
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

