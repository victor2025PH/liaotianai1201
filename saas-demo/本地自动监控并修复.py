#!/usr/bin/env python3
"""
本地自动监控服务器测试并自动修复问题
持续运行直到所有任务完成
"""

import subprocess
import time
import sys
import os
from datetime import datetime

SERVER = "ubuntu@165.154.233.55"
MAX_ITERATIONS = 200  # 最多检查200次（约50分钟）

def ssh_exec(cmd, timeout=60):
    """通过SSH执行命令"""
    try:
        full_cmd = f'ssh {SERVER} "{cmd}"'
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "命令执行超时", 1
    except Exception as e:
        return str(e), 1

def print_status(msg, status="INFO"):
    """打印状态"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    icons = {
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARN": "⚠️",
        "INFO": "ℹ️"
    }
    print(f"[{timestamp}] {icons.get(status, '')} {msg}")

def check_backend():
    """检查后端服务"""
    output, code = ssh_exec("curl -s --max-time 5 http://localhost:8000/health 2>&1", timeout=10)
    return code == 0 and ("ok" in output.lower() or "status" in output.lower())

def fix_and_verify_user():
    """修复并验证测试用户"""
    print_status("修复测试用户...", "INFO")
    
    cmd = """cd ~/liaotian/admin-backend && \
source .venv/bin/activate && \
export ADMIN_DEFAULT_PASSWORD=testpass123 && \
python reset_admin_user.py 2>&1"""
    
    output, code = ssh_exec(cmd, timeout=30)
    time.sleep(2)
    
    # 验证登录
    login_cmd = """curl -s --max-time 5 -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=testpass123' 2>&1"""
    
    login_output, login_code = ssh_exec(login_cmd, timeout=10)
    return "access_token" in login_output

def get_latest_log():
    """获取最新系统日志"""
    cmd = "ls -t ~/liaotian/test_logs/system_*.log 2>/dev/null | head -1"
    output, _ = ssh_exec(cmd, timeout=10)
    log_file = output.strip()
    return log_file if log_file and os.path.basename(log_file).startswith("system_") else None

def get_test_log():
    """获取最新测试日志"""
    cmd = "ls -t ~/liaotian/test_logs/test_run_*.log 2>/dev/null | head -1"
    output, _ = ssh_exec(cmd, timeout=10)
    log_file = output.strip()
    return log_file if log_file and os.path.basename(log_file).startswith("test_run_") else None

def check_log_completion(log_file):
    """检查日志是否显示完成"""
    if not log_file:
        return None
    
    cmd = f"tail -100 '{log_file}' 2>/dev/null"
    output, code = ssh_exec(cmd, timeout=10)
    
    if code != 0 or not output:
        return None
    
    content_lower = output.lower()
    
    # 检查是否成功完成
    if any(kw in content_lower for kw in ["所有任务成功完成", "所有测试通过", "✅.*成功", "success"]):
        return "SUCCESS"
    
    # 检查是否失败
    if any(kw in content_lower for kw in ["测试失败", "❌", "错误", "error", "failed"]):
        return "FAILED"
    
    # 检查是否完成但状态未知
    if any(kw in content_lower for kw in ["测试执行完成", "完成", "completed"]):
        return "COMPLETED"
    
    return "RUNNING"

def main():
    """主函数"""
    print("="*70)
    print("全自动监控和修复系统")
    print("="*70)
    print(f"服务器: {SERVER}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print()
    
    # 准备阶段
    print_status("准备环境...", "INFO")
    
    # 更新代码
    print_status("更新服务器代码...", "INFO")
    ssh_exec("cd ~/liaotian/saas-demo && git pull origin master > /dev/null 2>&1", timeout=30)
    
    # 给脚本添加执行权限
    ssh_exec("cd ~/liaotian/saas-demo && chmod +x *.sh 2>/dev/null || true", timeout=10)
    
    print_status("准备完成", "SUCCESS")
    print()
    
    # 检查后端服务
    print_status("检查后端服务...", "INFO")
    if not check_backend():
        print_status("后端服务未运行", "ERROR")
        print_status("请先启动后端服务", "WARN")
        return False
    print_status("后端服务正常", "SUCCESS")
    print()
    
    # 修复测试用户
    print_status("准备测试用户...", "INFO")
    if not fix_and_verify_user():
        print_status("测试用户准备失败，重试...", "WARN")
        time.sleep(3)
        if not fix_and_verify_user():
            print_status("测试用户准备失败", "ERROR")
            return False
    print_status("测试用户准备完成", "SUCCESS")
    print()
    
    # 启动测试
    print_status("启动测试任务...", "INFO")
    
    # 检查是否已有测试在运行
    cmd = "if [ -f ~/liaotian/test_logs/e2e_test.pid ]; then PID=\$(cat ~/liaotian/test_logs/e2e_test.pid); ps -p \$PID > /dev/null 2>&1 && echo 'RUNNING' || echo 'STOPPED'; else echo 'NOT_RUNNING'; fi"
    status_output, _ = ssh_exec(cmd, timeout=10)
    
    if "RUNNING" not in status_output:
        # 启动测试
        cmd = "cd ~/liaotian/saas-demo && nohup bash 全自动执行和监控系统.sh > ~/liaotian/test_logs/system_exec.log 2>&1 & echo \$!"
        output, code = ssh_exec(cmd, timeout=30)
        time.sleep(5)
        print_status(f"测试已启动", "SUCCESS")
    else:
        print_status("测试已在运行", "INFO")
    
    print()
    print("="*70)
    print("开始持续监控（每15秒检查一次）...")
    print("="*70)
    print()
    
    # 持续监控
    iteration = 0
    last_status = None
    
    while iteration < MAX_ITERATIONS:
        iteration += 1
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        print(f"[{timestamp}] 检查 {iteration}/{MAX_ITERATIONS}")
        
        # 检查系统日志
        system_log = get_latest_log()
        if system_log:
            status = check_log_completion(system_log)
            
            if status == "SUCCESS":
                print()
                print("="*70)
                print_status("所有任务成功完成！", "SUCCESS")
                print("="*70)
                print()
                
                # 获取最终日志
                log_content, _ = ssh_exec(f"tail -50 '{system_log}'", timeout=10)
                if log_content:
                    print("最终日志摘要:")
                    print("-"*70)
                    print(log_content)
                    print("-"*70)
                
                return True
                
            elif status == "FAILED":
                print()
                print("="*70)
                print_status("测试失败，尝试修复...", "ERROR")
                print("="*70)
                
                # 获取错误信息
                log_content, _ = ssh_exec(f"tail -100 '{system_log}'", timeout=10)
                if log_content:
                    errors = [line for line in log_content.split('\n') 
                             if any(k in line.lower() for k in ['error', '失败', '错误', 'failed'])]
                    if errors:
                        print("错误信息:")
                        for err in errors[-10:]:
                            print(f"  {err}")
                
                # 尝试修复
                print()
                print_status("尝试修复问题...", "INFO")
                
                # 修复用户
                fix_and_verify_user()
                time.sleep(2)
                
                # 重新启动
                print_status("重新启动测试...", "INFO")
                ssh_exec("pkill -f '全自动执行和监控系统.sh' 2>/dev/null || true", timeout=10)
                time.sleep(2)
                cmd = "cd ~/liaotian/saas-demo && nohup bash 全自动执行和监控系统.sh > ~/liaotian/test_logs/system_exec.log 2>&1 &"
                ssh_exec(cmd, timeout=30)
                time.sleep(5)
                print()
                
            elif status == "COMPLETED":
                print()
                print("="*70)
                print_status("测试已完成", "SUCCESS")
                print("="*70)
                return True
                
            elif status == "RUNNING":
                # 显示进度
                log_content, _ = ssh_exec(f"tail -5 '{system_log}' 2>/dev/null", timeout=10)
                if log_content:
                    last_line = log_content.strip().split('\n')[-1]
                    if last_line:
                        print(f"  进度: {last_line[:60]}")
        else:
            print("  等待日志文件...")
        
        # 检查测试日志
        test_log = get_test_log()
        if test_log:
            print(f"  测试日志: {os.path.basename(test_log)}")
        
        print()
        time.sleep(15)
    
    print()
    print("="*70)
    print_status("达到最大检查次数", "WARN")
    print("="*70)
    
    # 显示最终状态
    system_log = get_latest_log()
    if system_log:
        log_content, _ = ssh_exec(f"tail -50 '{system_log}'", timeout=10)
        if log_content:
            print("\n最终日志:")
            print("-"*70)
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
