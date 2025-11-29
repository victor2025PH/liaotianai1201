#!/usr/bin/env python3
"""
完整部署 UPSERT 功能修改：
1. 上传修改后的文件到服务器
2. 重启后端服务
3. 在浏览器中测试
"""
import subprocess
import sys
import os
from pathlib import Path

# 配置
SERVER = "ubuntu@165.154.233.55"
LOCAL_FILE = "admin-backend/app/api/group_ai/accounts.py"
REMOTE_FILE = "~/liaotian/admin-backend/app/api/group_ai/accounts.py"
PROJECT_ROOT = Path(__file__).parent.parent

def run_ssh_command(cmd):
    """执行 SSH 命令"""
    full_cmd = f'ssh {SERVER} "{cmd}"'
    print(f"执行: {full_cmd}")
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def upload_file():
    """上传文件到服务器"""
    print("=" * 60)
    print("步骤 1: 上传文件到服务器")
    print("=" * 60)
    
    local_path = PROJECT_ROOT / LOCAL_FILE
    if not local_path.exists():
        print(f"✗ 错误: 本地文件不存在: {local_path}")
        return False
    
    # 备份远程文件
    print("  备份远程文件...")
    success, stdout, stderr = run_ssh_command(
        f"cd ~/liaotian/admin-backend/app/api/group_ai && "
        f"cp accounts.py accounts.py.bak.$(date +%Y%m%d_%H%M%S) && "
        f"echo 'Backup created'"
    )
    if success:
        print("  ✓ 备份完成")
    else:
        print(f"  ⚠ 备份警告: {stderr}")
    
    # 使用 scp 上传文件
    print("  上传文件...")
    scp_cmd = f'scp "{local_path}" {SERVER}:{REMOTE_FILE}'
    result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("  ✓ 文件上传成功")
        return True
    else:
        print(f"  ✗ SCP 上传失败: {result.stderr}")
        print("  尝试使用 SSH 管道上传...")
        
        # 使用 SSH 管道上传
        with open(local_path, 'rb') as f:
            content = f.read()
        
        # 使用 base64 编码传输（避免特殊字符问题）
        import base64
        encoded = base64.b64encode(content).decode('ascii')
        
        cmd = f'echo "{encoded}" | base64 -d > {REMOTE_FILE}'
        success, stdout, stderr = run_ssh_command(cmd)
        
        if success:
            print("  ✓ 文件上传成功（base64）")
            return True
        else:
            print(f"  ✗ 上传失败: {stderr}")
            return False

def verify_file():
    """验证文件是否包含 UPSERT 代码"""
    print("\n" + "=" * 60)
    print("步骤 2: 验证文件内容")
    print("=" * 60)
    
    success, stdout, stderr = run_ssh_command(
        f"grep -c 'UPSERT 模式' {REMOTE_FILE}"
    )
    
    if success and stdout.strip().isdigit() and int(stdout.strip()) > 0:
        print(f"  ✓ 文件包含 UPSERT 代码（找到 {stdout.strip()} 处）")
        return True
    else:
        print("  ✗ 文件不包含 UPSERT 代码")
        return False

def restart_backend():
    """重启后端服务"""
    print("\n" + "=" * 60)
    print("步骤 3: 重启后端服务")
    print("=" * 60)
    
    # 停止旧进程
    print("  停止旧进程...")
    run_ssh_command("pkill -f 'uvicorn.*app.main:app' || true")
    print("  ✓ 旧进程已停止")
    
    # 等待进程完全停止
    import time
    time.sleep(2)
    
    # 启动新进程
    print("  启动后端服务...")
    success, stdout, stderr = run_ssh_command(
        "cd ~/liaotian/admin-backend && "
        "source .venv/bin/activate 2>/dev/null || true && "
        "nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 & "
        "sleep 5 && "
        "echo 'Backend started'"
    )
    
    if success:
        print("  ✓ 后端服务已启动")
        
        # 验证服务是否正常运行
        print("  验证服务状态...")
        time.sleep(3)
        success, stdout, stderr = run_ssh_command(
            "curl -s http://localhost:8000/health | head -1"
        )
        
        if success:
            print(f"  ✓ 后端服务健康检查: {stdout.strip()}")
            return True
        else:
            print(f"  ⚠ 健康检查失败，查看日志:")
            run_ssh_command("tail -20 /tmp/backend.log")
            return False
    else:
        print(f"  ✗ 后端服务启动失败: {stderr}")
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("UPSERT 功能部署脚本")
    print("=" * 60)
    print()
    
    # 1. 上传文件
    if not upload_file():
        print("\n✗ 部署失败：文件上传失败")
        return 1
    
    # 2. 验证文件
    if not verify_file():
        print("\n✗ 部署失败：文件验证失败")
        return 1
    
    # 3. 重启后端
    if not restart_backend():
        print("\n✗ 部署失败：后端服务重启失败")
        return 1
    
    print("\n" + "=" * 60)
    print("✓ 部署完成！")
    print("=" * 60)
    print("\n下一步：请在浏览器中测试 UPSERT 功能")
    print("测试 URL: http://aikz.usdt2026.cc/group-ai/accounts")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
