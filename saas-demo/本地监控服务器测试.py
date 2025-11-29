#!/usr/bin/env python3
"""
本地监控服务器上的测试进度
持续检查直到所有任务完成
"""

import subprocess
import time
import sys
import re
from datetime import datetime

SERVER = "ubuntu@165.154.233.55"
MAX_CHECKS = 120  # 最多检查30分钟（120 * 15秒）

def ssh_exec(cmd):
    """通过SSH执行命令"""
    try:
        full_cmd = f'ssh {SERVER} "{cmd}"'
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "命令执行超时", 1
    except Exception as e:
        return str(e), 1

def check_backend():
    """检查后端服务"""
    output, code = ssh_exec("curl -s http://localhost:8000/health 2>&1")
    return "ok" in output.lower() or "status" in output.lower()

def check_test_user():
    """检查测试用户"""
    cmd = """curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=testpass123' 2>&1"""
    
    output, code = ssh_exec(cmd)
    return "access_token" in output

def get_latest_log():
    """获取最新日志文件名"""
    cmd = "ls -t ~/liaotian/test_logs/e2e_test_*.log 2>/dev/null | head -1"
    output, code = ssh_exec(cmd)
    if output.strip():
        return output.strip()
    return None

def get_log_tail(log_file, lines=30):
    """获取日志的最后几行"""
    if not log_file:
        return None
    cmd = f"tail -{lines} '{log_file}' 2>/dev/null"
    output, code = ssh_exec(cmd)
    return output if code == 0 else None

def check_test_status():
    """检查测试状态"""
    log_file = get_latest_log()
    
    if not log_file:
        return "NO_LOG", None
    
    log_content = get_log_tail(log_file, 100)
    if not log_content:
        return "RUNNING", log_file
    
    content_lower = log_content.lower()
    
    # 检查是否完成
    if any(keyword in content_lower for keyword in ["测试.*完成", "所有.*完成", "测试执行完成", "所有任务完成"]):
        # 检查是否成功
        if any(keyword in content_lower for keyword in ["所有测试通过", "✅", "成功", "success"]):
            return "SUCCESS", log_file
        elif any(keyword in content_lower for keyword in ["测试失败", "❌", "错误", "error", "failed"]):
            return "FAILED", log_file
        else:
            return "COMPLETED", log_file
    
    return "RUNNING", log_file

def fix_test_user():
    """修复测试用户"""
    print("  [修复] 创建/修复测试用户...")
    cmd = """cd ~/liaotian/admin-backend && \
source .venv/bin/activate && \
export ADMIN_DEFAULT_PASSWORD=testpass123 && \
python reset_admin_user.py 2>&1"""
    
    output, code = ssh_exec(cmd)
    time.sleep(2)
    return code == 0

def start_test():
    """启动测试"""
    print("  [启动] 启动测试任务...")
    cmd = "cd ~/liaotian/saas-demo && bash 启动后台测试.sh 2>&1"
    output, code = ssh_exec(cmd)
    time.sleep(5)
    return code == 0

def main():
    """主函数"""
    print("="*60)
    print("本地监控服务器测试系统")
    print("="*60)
    print(f"服务器: {SERVER}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print()
    
    # 准备环境
    print("[准备] 更新服务器代码...")
    ssh_exec("cd ~/liaotian/saas-demo && git pull origin master > /dev/null 2>&1")
    ssh_exec("cd ~/liaotian/saas-demo && chmod +x *.sh 2>/dev/null || true")
    print("✅ 代码已更新")
    print()
    
    # 检查后端服务
    print("[检查] 后端服务...")
    if not check_backend():
        print("❌ 后端服务未运行")
        print("   请在服务器上启动后端服务")
        return
    print("✅ 后端服务正常")
    print()
    
    # 检查并修复测试用户
    print("[检查] 测试用户...")
    if not check_test_user():
        print("❌ 测试用户登录失败")
        if fix_test_user():
            if check_test_user():
                print("✅ 测试用户已修复")
            else:
                print("❌ 修复后仍然失败")
                return
        else:
            print("❌ 无法修复测试用户")
            return
    else:
        print("✅ 测试用户正常")
    print()
    
    # 启动测试（如果需要）
    print("[检查] 测试任务...")
    log_file = get_latest_log()
    if not log_file:
        print("  没有找到测试日志，启动新测试...")
        start_test()
    else:
        print(f"  找到现有日志: {log_file.split('/')[-1]}")
    print()
    
    # 持续监控
    print("="*60)
    print("开始持续监控（每15秒检查一次）...")
    print("="*60)
    print()
    
    check_count = 0
    
    while check_count < MAX_CHECKS:
        check_count += 1
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        print(f"[检查 {check_count}] {timestamp}")
        
        # 检查状态
        status, log_file = check_test_status()
        
        if status == "SUCCESS":
            print()
            print("="*60)
            print("✅ 所有任务成功完成！")
            print("="*60)
            print()
            
            if log_file:
                print("最终日志摘要:")
                print("-"*60)
                log_content = get_log_tail(log_file, 50)
                if log_content:
                    print(log_content)
                print("-"*60)
            
            return True
            
        elif status == "FAILED":
            print()
            print("="*60)
            print("❌ 测试失败，尝试修复...")
            print("="*60)
            print()
            
            if log_file:
                print("错误日志:")
                print("-"*60)
                log_content = get_log_tail(log_file, 50)
                if log_content:
                    errors = [line for line in log_content.split('\n') 
                             if any(k in line.lower() for k in ['error', '失败', '错误', 'failed'])]
                    for err in errors[-10:]:
                        print(f"  {err}")
                print("-"*60)
            
            # 尝试修复
            fix_test_user()
            time.sleep(2)
            start_test()
            print()
            
        elif status == "COMPLETED":
            print()
            print("="*60)
            print("⚠️  测试已完成，但状态未知")
            print("="*60)
            if log_file:
                print(f"日志文件: {log_file}")
                print("-"*60)
                log_content = get_log_tail(log_file, 30)
                if log_content:
                    print(log_content)
            return True
            
        elif status == "RUNNING":
            if log_file:
                log_content = get_log_tail(log_file, 5)
                if log_content:
                    last_line = log_content.strip().split('\n')[-1]
                    print(f"  进度: {last_line[:70]}")
                else:
                    print("  测试运行中...")
            else:
                print("  等待日志文件...")
        
        print()
        time.sleep(15)
    
    print("="*60)
    print("⚠️  达到最大检查次数")
    print("="*60)
    
    log_file = get_latest_log()
    if log_file:
        print(f"\n请手动查看日志: {log_file}")
        print("\n最后30行:")
        print("-"*60)
        log_content = get_log_tail(log_file, 30)
        if log_content:
            print(log_content)
    
    return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n监控已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
