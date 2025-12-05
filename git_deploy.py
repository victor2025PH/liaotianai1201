#!/usr/bin/env python3
"""
Git Deployment Script - Automatically commits and pushes changes
"""
import subprocess
import os
import sys
from datetime import datetime

# Change to project directory
PROJECT_DIR = r"e:\002-工作文件\重要程序\聊天AI群聊程序"
os.chdir(PROJECT_DIR)

print(f"=" * 60)
print(f"Git Deployment Script")
print(f"Working Directory: {os.getcwd()}")
print(f"Time: {datetime.now()}")
print(f"=" * 60)

def run_command(cmd, description):
    """Run a shell command and return output"""
    print(f"\n[{description}]")
    print(f"Command: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        output = result.stdout + result.stderr
        print(f"Exit code: {result.returncode}")
        print(f"Output:\n{output}")
        return result.returncode, output
    except Exception as e:
        print(f"Error: {e}")
        return -1, str(e)

# Step 1: Check git status
run_command("git status", "Checking git status")

# Step 2: Add all changes
run_command("git add -A", "Adding all changes")

# Step 3: Check status again
run_command("git status", "Checking status after add")

# Step 4: Create commit
commit_message = """feat: Add advanced chat features

New Features:
- TTS voice messaging system
- AI image generation  
- Cross-group synchronization
- Alert system
- Message templates
- Blacklist/whitelist management
- Multi-language support
- Webhook integration
- Private chat funnel for user conversion
- Frontend control pages for all new features
"""
run_command(f'git commit -m "{commit_message}"', "Creating commit")

# Step 5: Push to remote
run_command("git push loaotian1127 master", "Pushing to GitHub (loaotian1127)")

# Alternative push if the above fails
run_command("git push origin master", "Pushing to GitHub (origin)")

print(f"\n{'=' * 60}")
print("Deployment script completed!")
print(f"{'=' * 60}")
