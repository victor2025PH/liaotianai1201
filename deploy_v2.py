#!/usr/bin/env python3
"""
Git Deployment Script v2 - Writes output to file
"""
import subprocess
import os
import sys
from datetime import datetime

# Output file
LOG_FILE = r"e:\deployment_output.log"
PROJECT_DIR = r"e:\002-工作文件\重要程序\聊天AI群聊程序"

def log(msg):
    """Write to log file"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{msg}\n")
    print(msg)

# Clear log file
with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write(f"=== Deployment Started: {datetime.now()} ===\n")

os.chdir(PROJECT_DIR)
log(f"Working Directory: {os.getcwd()}")

def run_cmd(cmd, desc):
    log(f"\n--- {desc} ---")
    log(f"Command: {cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=120
        )
        log(f"Exit: {result.returncode}")
        if result.stdout:
            log(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            log(f"STDERR:\n{result.stderr}")
        return result.returncode
    except Exception as e:
        log(f"ERROR: {e}")
        return -1

# Run deployment steps
run_cmd("git --version", "Git Version")
run_cmd("git status", "Git Status")
run_cmd("git add -A", "Git Add All")
run_cmd("git status", "Git Status After Add")
run_cmd('git commit -m "feat: Add advanced chat features - TTS, AI image, cross-group, alerts, templates, user lists, multi-lang, webhooks, private funnel"', "Git Commit")
run_cmd("git push loaotian1127 master", "Git Push to loaotian1127")
run_cmd("git push origin master", "Git Push to origin")

log(f"\n=== Deployment Completed: {datetime.now()} ===")
print(f"Log written to: {LOG_FILE}")
