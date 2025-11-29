#!/usr/bin/env python3
"""
本地实时监控服务器测试执行
持续读取服务器日志并显示实时信息
自动检测问题并修复
"""

import subprocess
import time
import sys
import os
from datetime import datetime
from pathlib import Path

SERVER = "ubuntu@165.154.233.55"
MAX_ITERATIONS = 300  # 最多监控1.25小时
CHECK_INTERVAL = 10  # 每10秒检查一次

def ssh_exec(cmd, timeout=30):
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
    icons = {"SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠️", "INFO": "ℹ️"}
    colors = {
        "SUCCESS": "\033[32m",
        "ERROR": "\033[31m",
        "WARN": "\033[33m",
        "INFO": "\033[36m"
    }
    icon = icons.get(status, "")
    color = colors.get(status, "")
    reset = "\033[0m"
    print(f"{color}[{timestamp}]{reset} {icon} {msg}")

def get_status_file():
    """获取状态文件内容"""
    cmd = "cat ~/liaotian/test_logs/current_status.txt 2>/dev/null || echo ''"
    output, _ = ssh_exec(cmd, timeout=10)
    return output.strip()

def get_latest_log():
    """获取最新监控日志"""
    cmd = "ls -t ~/liaotian/test_logs/realtime_monitor_*.log 2>/dev/null | head -1"
    output, _ = ssh_exec(cmd, timeout=10)
    log_file = output.strip()
    return log_file if log_file else None

def get_log_tail(log_file, lines=50, offset=0):
    """获取日志的最后几行（支持偏移）"""
    if not log_file:
        return None, 0
    
    cmd = f"tail -{lines + offset} '{log_file}' 2>/dev/null"
    output, code = ssh_exec(cmd, timeout=10)
    
    if code != 0 or not output:
        return None, 0
    
    lines_list = output.strip().split('\n')
    return '\n'.join(lines_list), len(lines_list)

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

def start_test():
    """启动测试"""
    print_status("启动实时监控执行...", "INFO")
    
    cmd = "cd ~/liaotian/saas-demo && nohup bash 服务器端实时监控执行.sh > /dev/null 2>&1 & echo \$!"
    output, code = ssh_exec(cmd, timeout=30)
    
    if code == 0 and output.strip():
        print_status(f"监控脚本已启动 (PID: {output.strip()})", "SUCCESS")
        time.sleep(5)
        return True
    return False

def main():
    """主函数"""
    print("="*70)
    print("本地实时监控系统")
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
    
    print_status("环境准备完成", "SUCCESS")
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
    print_status("启动实时监控执行系统...", "INFO")
    if not start_test():
        print_status("无法启动监控脚本", "ERROR")
        return False
    
    print()
    print("="*70)
    print("开始实时监控（每10秒检查一次）...")
    print("="*70)
    print()
    
    # 持续监控
    iteration = 0
    last_log_size = 0
    last_log_file = None
    consecutive_errors = 0
    max_consecutive_errors = 3
    
    while iteration < MAX_ITERATIONS:
        iteration += 1
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 获取状态文件
        status = get_status_file()
        if status:
            status_parts = status.split('|')
            if len(status_parts) >= 2:
                status_msg = status_parts[-1]
                print(f"[{timestamp}] {status_msg}")
        
        # 获取最新日志文件
        log_file = get_latest_log()
        
        if log_file and log_file != last_log_file:
            print_status(f"找到日志文件: {os.path.basename(log_file)}", "INFO")
            last_log_file = log_file
            last_log_size = 0
        
        if log_file:
            # 获取新的日志内容
            log_content, new_size = get_log_tail(log_file, lines=100, offset=last_log_size)
            
            if log_content and new_size > last_log_size:
                # 显示新内容
                lines_list = log_content.split('\n')
                new_lines = lines_list[last_log_size:] if last_log_size < len(lines_list) else []
                
                for line in new_lines:
                    if line.strip():
                        # 根据内容类型显示不同颜色
                        if any(kw in line.lower() for kw in ['✅', '成功', '通过', 'success']):
                            print(f"  \033[32m{line}\033[0m")
                        elif any(kw in line.lower() for kw in ['❌', '失败', '错误', 'error', 'failed']):
                            print(f"  \033[31m{line}\033[0m")
                        elif any(kw in line.lower() for kw in ['⚠️', '警告', 'warning']):
                            print(f"  \033[33m{line}\033[0m")
                        else:
                            print(f"  {line}")
                
                last_log_size = new_size
                
                # 检查是否完成
                if any(kw in log_content.lower() for kw in ["所有任务成功完成", "所有测试通过", "✅.*成功", "测试.*成功"]):
                    print()
                    print("="*70)
                    print_status("所有任务成功完成！", "SUCCESS")
                    print("="*70)
                    print()
                    
                    # 获取最终日志
                    final_log, _ = get_log_tail(log_file, lines=50)
                    if final_log:
                        print("最终日志摘要:")
                        print("-"*70)
                        print(final_log)
                        print("-"*70)
                    
                    return True
                    
                elif any(kw in log_content.lower() for kw in ["测试失败", "❌.*失败", "错误", "error", "failed"]):
                    consecutive_errors += 1
                    
                    if consecutive_errors >= max_consecutive_errors:
                        print()
                        print("="*70)
                        print_status("检测到错误，尝试修复...", "WARN")
                        print("="*70)
                        
                        # 分析错误并修复
                        if "auth" in log_content.lower() or "login" in log_content.lower():
                            print_status("检测到认证错误，修复用户...", "INFO")
                            fix_and_verify_user()
                        
                        # 重新启动
                        print_status("重新启动测试...", "INFO")
                        ssh_exec("pkill -f '服务器端实时监控执行.sh' 2>/dev/null || true", timeout=10)
                        time.sleep(2)
                        start_test()
                        
                        consecutive_errors = 0
                        last_log_size = 0
                        last_log_file = None
                        print()
                else:
                    consecutive_errors = 0
            else:
                # 显示最后一行作为进度
                if log_content:
                    last_line = log_content.strip().split('\n')[-1]
                    if last_line and len(last_line) > 0:
                        print(f"  进度: {last_line[:70]}")
        else:
            print(f"  等待日志文件...")
        
        print()
        time.sleep(CHECK_INTERVAL)
    
    print()
    print("="*70)
    print_status("达到最大检查次数", "WARN")
    print("="*70)
    
    # 显示最终状态
    log_file = get_latest_log()
    if log_file:
        final_log, _ = get_log_tail(log_file, lines=50)
        if final_log:
            print("\n最终日志:")
            print("-"*70)
            print(final_log)
    
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
