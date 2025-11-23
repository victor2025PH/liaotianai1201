#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时监控后端日志（通过API）
"""
import requests
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin@example.com"
PASSWORD = "changeme123"

def login():
    """登录获取token"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": USERNAME, "password": PASSWORD},
            timeout=5
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Login failed: {e}")
        return None

def monitor_logs(token, keywords=None):
    """监控日志"""
    if keywords is None:
        keywords = [
            "远程发送验证码",
            "验证码发送成功",
            "CODE_SENT",
            "验证码验证",
            "远程验证",
            "ERROR",
        ]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("=" * 80)
    print("Real-time Backend Log Monitoring")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Monitoring keywords: {', '.join(keywords)}")
    print("=" * 80)
    print()
    print("Monitoring... (Press Ctrl+C to stop)")
    print()
    
    last_log_time = None
    
    try:
        while True:
            try:
                # Try to get logs via API
                response = requests.get(
                    f"{BASE_URL}/group-ai/logs",
                    headers=headers,
                    params={"page_size": 50, "q": "验证码"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    logs_data = response.json()
                    if logs_data.get('items'):
                        logs = logs_data['items']
                        for log in logs:
                            log_time = log.get('timestamp', '')
                            message = log.get('message', '')
                            level = log.get('level', '')
                            
                            # Check if this is a new log
                            if log_time != last_log_time:
                                # Check if it matches keywords
                                if any(keyword in message for keyword in keywords):
                                    color = "ERROR" if level == "error" else "INFO" if level == "info" else "WARNING"
                                    print(f"[{log_time}] [{level}] {message}")
                                    last_log_time = log_time
                
                time.sleep(2)
                
            except KeyboardInterrupt:
                print("\n\nMonitoring stopped")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)
    
    except Exception as e:
        print(f"Monitoring failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    token = login()
    if not token:
        print("ERROR: Failed to login")
        sys.exit(1)
    
    keywords = sys.argv[1:] if len(sys.argv) > 1 else None
    monitor_logs(token, keywords)

