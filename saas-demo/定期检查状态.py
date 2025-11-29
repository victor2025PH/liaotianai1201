#!/usr/bin/env python3
"""
定期检查测试状态并反馈
持续监控直到所有任务完成
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def run_cmd(cmd):
    """执行命令并返回输出"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=10
        )
        return result.stdout + result.stderr, result.returncode
    except Exception as e:
        return str(e), 1

def check_status():
    """检查测试状态"""
    print(f"\n[{time.strftime('%H:%M:%S')}] 检查状态...")
    
    # 1. 检查后端服务
    output, code = run_cmd("curl -s http://localhost:8000/health 2>&1")
    if code == 0 and "ok" in output.lower():
        print("✅ 后端服务正常")
    else:
        print(f"❌ 后端服务异常: {output[:100]}")
        return False
    
    # 2. 检查测试用户
    login_cmd = """curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=testpass123" 2>&1"""
    
    output, code = run_cmd(login_cmd)
    if "access_token" in output:
        print("✅ 测试用户登录正常")
    else:
        print(f"❌ 登录失败，尝试修复...")
        # 修复用户
        run_cmd("cd ~/liaotian/admin-backend && source .venv/bin/activate && export ADMIN_DEFAULT_PASSWORD=testpass123 && python reset_admin_user.py 2>&1")
        time.sleep(2)
        return False
    
    # 3. 检查日志文件
    log_dir = Path.home() / "liaotian" / "test_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_files = sorted(log_dir.glob("e2e_test_*.log"), key=os.path.getmtime, reverse=True)
    
    if log_files:
        latest_log = log_files[0]
        print(f"📄 最新日志: {latest_log.name}")
        
        # 读取最后50行
        try:
            with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                last_lines = lines[-50:] if len(lines) > 50 else lines
                
            # 检查是否完成
            content = ''.join(last_lines).lower()
            if any(keyword in content for keyword in ["测试.*完成", "所有.*完成", "测试执行完成"]):
                print("\n" + "="*50)
                print("测试已完成！")
                print("="*50)
                print("\n最后30行日志:")
                print("-"*50)
                for line in lines[-30:]:
                    print(line.rstrip())
                print("-"*50)
                
                if any(keyword in content for keyword in ["所有测试通过", "✅", "成功"]):
                    print("\n✅ 所有任务成功完成！")
                    return "SUCCESS"
                elif any(keyword in content for keyword in ["测试失败", "❌", "错误", "error"]):
                    print("\n❌ 测试失败")
                    errors = [line for line in last_lines if any(k in line.lower() for k in ["error", "失败", "错误"])]
                    if errors:
                        print("\n错误信息:")
                        for err in errors[-10:]:
                            print(f"  {err.rstrip()}")
                    return "FAILED"
                else:
                    return "UNKNOWN"
            else:
                # 显示进度
                last_line = lines[-1].strip() if lines else ""
                print(f"   进度: {last_line[:80]}")
        except Exception as e:
            print(f"读取日志失败: {e}")
    else:
        print("⚠️  日志文件不存在")
    
    # 4. 检查进程
    pid_file = log_dir / "e2e_test.pid"
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            output, code = run_cmd(f"ps -p {pid} > /dev/null 2>&1")
            if code == 0:
                print(f"🔄 测试进程运行中 (PID: {pid})")
            else:
                print("⚠️  测试进程已结束")
        except:
            pass
    
    return "RUNNING"

def main():
    """主函数"""
    print("="*50)
    print("自动监控系统启动")
    print("="*50)
    
    # 确保环境准备
    print("\n[准备] 更新代码...")
    run_cmd("cd ~/liaotian/saas-demo && git pull origin master > /dev/null 2>&1")
    run_cmd("cd ~/liaotian/saas-demo && chmod +x *.sh 2>/dev/null || true")
    
    # 启动测试（如果未运行）
    log_dir = Path.home() / "liaotian" / "test_logs"
    pid_file = log_dir / "e2e_test.pid"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    should_start = True
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            output, code = run_cmd(f"ps -p {pid} > /dev/null 2>&1")
            if code == 0:
                print(f"✅ 测试已在运行 (PID: {pid})")
                should_start = False
        except:
            pass
    
    if should_start:
        print("[启动] 启动测试任务...")
        run_cmd("cd ~/liaotian/saas-demo && bash 启动后台测试.sh > /dev/null 2>&1 &")
        time.sleep(5)
    
    # 持续监控
    print("\n[监控] 开始持续监控（每15秒检查一次）...")
    print("="*50)
    
    max_checks = 120  # 30分钟
    check_count = 0
    
    while check_count < max_checks:
        status = check_status()
        
        if status == "SUCCESS":
            sys.exit(0)
        elif status == "FAILED":
            # 尝试修复并重启
            print("\n[修复] 尝试修复问题...")
            run_cmd("cd ~/liaotian/admin-backend && source .venv/bin/activate && export ADMIN_DEFAULT_PASSWORD=testpass123 && python reset_admin_user.py 2>&1")
            time.sleep(2)
            print("[重启] 重新启动测试...")
            if pid_file.exists():
                try:
                    pid = int(pid_file.read_text().strip())
                    run_cmd(f"kill {pid} 2>/dev/null || true")
                except:
                    pass
                pid_file.unlink()
            run_cmd("cd ~/liaotian/saas-demo && bash 启动后台测试.sh > /dev/null 2>&1 &")
            time.sleep(5)
        
        check_count += 1
        time.sleep(15)
    
    print("\n⚠️  达到最大检查次数")
    sys.exit(1)

if __name__ == "__main__":
    main()
