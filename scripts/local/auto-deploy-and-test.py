#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全自动部署、重启、监控和测试脚本
功能：自动连接到服务器，部署服务，重启，监控日志，打开浏览器测试
"""

import json
import paramiko
import sys
import time
import subprocess
import webbrowser
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
    
    # 使用马尼拉服务器
    manila_config = config.get('servers', {}).get('manila', {})
    
    return {
        'host': '165.154.233.55',
        'user': manila_config.get('user', 'ubuntu'),
        'password': manila_config.get('password', 'Along2025!!!'),
        'project_dir': '/home/ubuntu/telegram-ai-system',
    }

def connect_server(host, user, password, retries=3):
    """连接服务器，支持重试"""
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
        
        # 实时输出
        output_lines = []
        error_lines = []
        
        # 读取标准输出
        for line in iter(stdout.readline, ""):
            if line:
                line = line.rstrip()
                print(line)
                output_lines.append(line)
        
        # 读取错误输出
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
    print("🚀 全自动部署、重启、监控和测试")
    print("="*60)
    print()
    
    # 加载配置
    config = load_config()
    host = config['host']
    user = config['user']
    password = config['password']
    project_dir = config['project_dir']
    
    client = None
    try:
        # 步骤 1: 连接服务器
        client = connect_server(host, user, password)
        
        # 步骤 2: 拉取最新代码
        run_command(
            client,
            f"cd {project_dir} && git pull origin main",
            "拉取最新代码"
        )
        time.sleep(2)
        
        # 步骤 3: 检查并创建虚拟环境
        print(f"\n{'='*60}")
        print("📋 检查虚拟环境")
        print(f"{'='*60}")
        
        # 检查后端虚拟环境
        stdout, stderr, exit_code = run_command(
            client,
            f"test -d {project_dir}/admin-backend/venv && echo 'exists' || echo 'not found'",
            "",
            check_output=False
        )
        
        if 'not found' in stdout:
            print("⚠️  后端虚拟环境不存在，创建中...")
            run_command(
                client,
                f"cd {project_dir}/admin-backend && python3 -m venv venv",
                "创建后端虚拟环境"
            )
            # 安装依赖
            run_command(
                client,
                f"cd {project_dir}/admin-backend && source venv/bin/activate && pip install -r requirements.txt",
                "安装后端依赖"
            )
        else:
            print("✅ 后端虚拟环境存在")
        
        # 检查 Bot 虚拟环境（可选，如果不存在可以跳过 Bot 服务）
        stdout, stderr, exit_code = run_command(
            client,
            f"test -d {project_dir}/venv && echo 'exists' || echo 'not found'",
            "",
            check_output=False
        )
        
        if 'not found' in stdout:
            print("⚠️  Bot 虚拟环境不存在，创建中...")
            run_command(
                client,
                f"cd {project_dir} && python3 -m venv venv",
                "创建 Bot 虚拟环境"
            )
            # 安装依赖
            run_command(
                client,
                f"cd {project_dir} && source venv/bin/activate && pip install -r requirements.txt",
                "安装 Bot 依赖"
            )
        else:
            print("✅ Bot 虚拟环境存在")
        
        time.sleep(2)
        
        # 步骤 4: 部署 systemd 服务
        print(f"\n{'='*60}")
        print("📋 部署 systemd 服务")
        print(f"{'='*60}")
        
        # 检查服务文件是否存在
        stdout, stderr, exit_code = run_command(
            client,
            f"test -f {project_dir}/deploy/systemd/telegram-bot.service && echo 'exists' || echo 'not found'",
            "",
            check_output=False
        )
        
        if 'exists' in stdout:
            print("✅ 服务文件存在，开始部署...")
            # 使用更宽松的错误处理，因为 Bot 服务可能不需要
            stdout, stderr, exit_code = run_command(
                client,
                f"cd {project_dir} && sudo bash scripts/server/deploy-systemd.sh",
                "部署 systemd 服务",
                check_output=False
            )
            if exit_code != 0:
                print("⚠️  部署脚本有警告，继续...")
        else:
            print("⚠️  服务文件不存在，手动安装...")
            run_command(
                client,
                f"cd {project_dir} && sudo cp deploy/systemd/telegram-backend.service /etc/systemd/system/ && sudo systemctl daemon-reload",
                "手动安装后端服务"
            )
        
        time.sleep(2)
        
        # 步骤 5: 重启服务并测试
        print(f"\n{'='*60}")
        print("🔄 重启服务并执行测试")
        print(f"{'='*60}")
        
        # 先重新加载 systemd（确保服务文件更新）
        run_command(
            client,
            f"sudo systemctl daemon-reload",
            "重新加载 systemd"
        )
        
        # 重启服务（使用更宽松的错误处理）
        stdout, stderr, exit_code = run_command(
            client,
            f"cd {project_dir} && sudo bash scripts/server/restart-and-test.sh",
            "重启服务并测试",
            check_output=False  # 允许部分失败
        )
        
        if exit_code != 0:
            print("⚠️  重启脚本执行有警告，继续检查服务状态...")
        
        time.sleep(3)
        
        # 步骤 6: 检查服务状态
        print(f"\n{'='*60}")
        print("📊 检查服务状态")
        print(f"{'='*60}")
        
        run_command(
            client,
            f"systemctl is-active telegram-backend telegram-bot && echo '✅ 所有服务运行正常' || echo '⚠️  部分服务未运行'",
            "服务状态"
        )
        
        # 步骤 7: 测试 API（允许部分失败）
        print(f"\n{'='*60}")
        print("🧪 测试 API 端点")
        print(f"{'='*60}")
        
        stdout, stderr, exit_code = run_command(
            client,
            f"cd {project_dir} && bash scripts/server/test-all-endpoints.sh",
            "API 端点测试",
            check_output=False  # 允许部分失败
        )
        
        if exit_code != 0:
            print("⚠️  API 测试有警告，但继续...")
        
        # 步骤 8: 显示最近日志
        print(f"\n{'='*60}")
        print("📋 最近日志（最后 30 行）")
        print(f"{'='*60}")
        
        run_command(
            client,
            f"journalctl -u telegram-backend -n 30 --no-pager | tail -20",
            "后端日志"
        )
        
        print(f"\n{'='*60}")
        print("✅ 服务器端操作完成!")
        print(f"{'='*60}")
        print()
        print("📝 下一步:")
        print("   1. 实时监控日志（在服务器上执行）:")
        print(f"      bash {project_dir}/scripts/server/monitor-all-logs.sh")
        print("   2. 查看日志（在服务器上执行）:")
        print(f"      bash {project_dir}/scripts/server/view-logs.sh all -f")
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
    
    # 步骤 9: 在本地打开浏览器测试
    print(f"\n{'='*60}")
    print("🌐 打开浏览器测试")
    print(f"{'='*60}")
    
    test_urls = [
        f"http://{host}:8000/docs",      # Swagger UI
        f"http://{host}:8000/redoc",     # ReDoc
        f"http://{host}:8000/health",    # 健康检查
    ]
    
    print("\n正在打开测试页面...")
    for url in test_urls:
        try:
            print(f"  打开: {url}")
            webbrowser.open(url)
            time.sleep(1)
        except Exception as e:
            print(f"  ⚠️  无法打开 {url}: {e}")
    
    print("\n✅ 浏览器测试页面已打开!")
    print("\n📋 测试清单:")
    print("   1. 检查 Swagger UI 是否正常加载")
    print("   2. 检查 API 端点是否可访问")
    print("   3. 测试登录功能")
    print("   4. 测试各个功能模块")
    print()
    
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

