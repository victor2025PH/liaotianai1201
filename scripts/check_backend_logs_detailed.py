#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细检查后端日志
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import re

def check_backend_logs():
    """检查后端日志"""
    print("=" * 80)
    print("Backend Log Analysis")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    log_files = [
        Path("admin-backend/backend.log"),
        Path("admin-backend/backend_stdout.log"),
        Path("admin-backend/backend_stderr.log"),
    ]
    
    for log_file in log_files:
        if not log_file.exists():
            continue
        
        print(f"Log File: {log_file}")
        print("-" * 80)
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            print(f"Total lines: {len(lines)}")
            print()
            
            # Find recent verification code related logs
            verification_keywords = [
                '远程发送验证码',
                '验证码发送成功',
                'CODE_SENT',
                'send_code',
                '验证码验证',
                '远程验证',
                'PhoneCodeExpired',
                'PhoneCodeInvalid',
                'ERROR:PHONE_BANNED',
                'ERROR:FLOOD_WAIT',
            ]
            
            print("Recent verification code related logs:")
            print("-" * 80)
            
            found_logs = []
            for i, line in enumerate(lines[-500:], start=max(0, len(lines)-500)):
                for keyword in verification_keywords:
                    if keyword.lower() in line.lower():
                        found_logs.append((i+1, line.strip()))
                        break
            
            if found_logs:
                for line_num, line in found_logs[-30:]:  # Show last 30
                    # Truncate long lines
                    if len(line) > 200:
                        line = line[:200] + "..."
                    print(f"Line {line_num}: {line}")
            else:
                print("No verification code related logs found")
            
            print()
            
            # Find errors
            print("Recent errors:")
            print("-" * 80)
            
            error_logs = []
            for i, line in enumerate(lines[-500:], start=max(0, len(lines)-500)):
                if any(keyword in line for keyword in ['ERROR', 'Exception', 'Traceback', '失败', '错误']):
                    error_logs.append((i+1, line.strip()))
            
            if error_logs:
                for line_num, line in error_logs[-20:]:  # Show last 20
                    if len(line) > 200:
                        line = line[:200] + "..."
                    print(f"Line {line_num}: {line}")
            else:
                print("No errors found")
            
            print()
            
        except Exception as e:
            print(f"ERROR reading log file: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("=" * 80)
    print("Analysis Complete")
    print("=" * 80)

if __name__ == "__main__":
    check_backend_logs()

