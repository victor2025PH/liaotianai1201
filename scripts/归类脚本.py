#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文件归类脚本 - 自动整理根目录的MD文档和脚本文件"""
import os
import shutil
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

# 文件归类映射
FILE_MAPPING = {
    # 项目文档 -> docs/项目文档/
    "项目文档": {
        "files": [
            "CURRENT_STATUS_AND_NEXT_STEPS.md",
            "FINAL_SUMMARY.md",
            "FUNCTIONAL_TEST_GUIDE.md",
            "PROJECT_COMPLETE_FINAL.md",
            "PROJECT_COMPLETE.md",
            "README_TELEGRAM_REGISTRATION.md",
            "START_TESTING.md",
            "TESTING_NEXT_STEPS.md",
            "GitHub仓库准备问题清单.md",
            "GITHUB_PROJECT_AUDIT.md",
            "GAME_SYSTEM_INTEGRATION_GUIDE.md",
            "GAME_SYSTEM_INTEGRATION_SUMMARY.md",
            "REDPACKET_GAME_INTEGRATION_REQUIREMENTS.md",
            "FUNCTION_ANALYSIS_AND_OPTIMIZATION_REPORT.md",
            "Telegram消息发送问题分析和解决方案.md",
            "start_account API修改说明.md",
        ],
        "target": "docs/项目文档"
    },
    
    # 测试文档 -> docs/测试报告/根目录测试文档/
    "测试文档": {
        "files": [
            "下一步测试指南.md",
            "全自动测试最终总结.md",
            "全自动测试完成总结.md",
            "全自动测试总结.md",
            "全自动测试执行报告.md",
            "剧本加载问题修复报告.md",
            "功能测试总结报告.md",
            "完整功能测试报告.md",
            "建群和聊天功能测试最终报告.md",
            "建群和聊天功能测试结果.md",
            "建群和聊天功能测试计划.md",
            "批量创建提示修改说明.md",
            "批量创建测试最终报告.md",
            "批量创建测试完成报告.md",
            "批量创建测试流程.md",
            "批量创建测试结果.md",
            "批量创建测试进度.md",
            "批量创建测试进行中.md",
            "批量创建确认对话框修改说明.md",
            "服务启动和测试报告.md",
            "服务器分配和建群聊天测试报告.md",
            "服务器建群和聊天测试修复报告.md",
            "服务器建群和聊天测试结果.md",
            "服务器建群和聊天测试计划.md",
            "服务器账号启动测试总结.md",
            "服务器部署和测试方案.md",
            "服务器部署测试完成总结.md",
            "服务器部署测试总结.md",
            "服务器部署测试方案（正确流程）.md",
            "服务器部署测试正确流程.md",
            "测试开始指南.md",
            "测试成功报告.md",
            "测试执行报告.md",
            "测试执行计划.md",
            "测试服务器分配和建群聊天.md",
            "测试说明.md",
            "登录问题修复总结.md",
            "登录问题分析和修复.md",
            "端到端业务流程测试报告.md",
            "端到端测试最终报告.md",
            "端口3000服务功能测试报告.md",
            "简化测试方案.md",
            "账号启动测试最终报告.md",
            "账号启动测试结果.md",
            "账号启动测试计划.md",
            "账号测试和验证总结.md",
            "账号测试和验证方案.md",
            "账号测试执行计划.md",
            "账号测试结果.md",
            "重启后端服务说明.md",
            "重新测试说明.md",
            "问题分析和解决方案总结.md",
        ],
        "target": "docs/测试报告/根目录测试文档"
    },
    
    # 测试脚本 -> scripts/测试脚本/
    "测试脚本": {
        "files": [
            "analyze_auth_key_duplicated.py",
            "analyze_single_server_success.py",
            "analyze_three_servers_errors.py",
            "check_account_in_group.py",
            "check_account_manager_status.py",
            "check_accounts.py",
            "check_all_processes.py",
            "check_all_servers_status.py",
            "check_all_sessions_status.py",
            "check_and_fix_accounts.py",
            "check_local_test_results.py",
            "check_new_sessions_logs.py",
            "check_script_details.py",
            "check_server_logs.py",
            "check_server_main_py.py",
            "check_services_status.py",
            "check_session_file_usage.py",
            "check_session_locks.py",
            "check_startup_errors.py",
            "cleanup_all_accounts.py",
            "cleanup_and_restart_server_accounts.py",
            "cleanup_and_retry.py",
            "cleanup_servers_and_restart.py",
            "cleanup_session_journals.py",
            "create_accounts_from_servers.py",
            "create_default_script.py",
            "delete_all_sessions.py",
            "distribute_and_test_sessions.py",
            "final_test_status_report.py",
            "force_cleanup_and_restart.py",
            "force_start_accounts.py",
            "monitor_all_servers_logs.py",
            "monitor_three_servers_realtime.py",
            "release_all_connections.py",
            "restart_backend_and_test.py",
            "restart_server_accounts.py",
            "retest_failed_sessions.py",
            "run_main_single_session.py",
            "save_script_to_filesystem.py",
            "send_test_message_and_verify.py",
            "show_server_terminal.py",
            "start_account_with_script_yaml.py",
            "start_and_monitor_two_servers.py",
            "start_backend_with_monitor.py",
            "start_frontend_with_monitor.py",
            "start_main.py",
            "stop_all_and_test_one.py",
            "stop_all_servers_and_run_local.py",
            "stop_all_servers.py",
            "stop_backend_and_test.py",
            "stop_local_accounts.py",
            "stop_servers_and_test_local.py",
            "sync_server_account_status.py",
            "test_alternative_sessions.py",
            "test_group_chat_after_distribution.py",
            "test_group_chat_browser.py",
            "test_group_chat_complete.py",
            "test_group_chat_with_account.py",
            "test_group_chat.py",
            "test_group_creation_direct.py",
            "test_main_py_direct_output.py",
            "test_main_py_directly.py",
            "test_main_with_ai.py",
            "test_main_with_session.py",
            "test_main.py",
            "test_server_group_chat.py",
            "test_session_after_cleanup.py",
            "test_session_local.py",
            "test_single_new_session_local.py",
            "test_single_server_account.py",
            "test_two_sessions_local.py",
            "test_two_sessions_quick.py",
            "test_with_detailed_logging.py",
            "test_with_wait.py",
            "upload_and_test_three_servers.py",
            "upload_and_test_with_new_sessions.py",
            "verify_server_accounts_in_group.py",
            "verify_session.py",
            "wait_30_minutes.py",
            "wait_and_retry.py",
        ],
        "target": "scripts/测试脚本"
    },
    
    # PowerShell脚本 -> scripts/PowerShell脚本/
    "PowerShell脚本": {
        "files": [
            "check_python_processes.ps1",
            "monitor_services.ps1",
            "全自动测试服务器建群聊天.ps1",
            "全自动测试服务器账号启动.ps1",
            "检查可用账号.ps1",
            "测试创建群组.ps1",
            "测试建群聊天功能.ps1",
            "测试按剧本聊天.ps1",
            "测试按剧本聊天功能（完整版）.ps1",
            "测试按剧本聊天功能（替代方案）.ps1",
            "测试服务器分配和建群聊天.ps1",
            "测试服务器账号启动.ps1",
            "测试服务器部署和启动.ps1",
            "测试账号启动.ps1",
            "账号测试和验证脚本.ps1",
            "验证新API端点.ps1",
        ],
        "target": "scripts/PowerShell脚本"
    },
    
    # JavaScript脚本 -> scripts/JavaScript脚本/
    "JavaScript脚本": {
        "files": [
            "浏览器测试服务器账号启动.js",
            "浏览器测试脚本.js",
            "浏览器自动化测试脚本.js",
        ],
        "target": "scripts/JavaScript脚本"
    },
    
    # HTML文件 -> docs/测试页面/
    "HTML文件": {
        "files": [
            "服务器建群和聊天测试页面.html",
            "自动测试页面.html",
        ],
        "target": "docs/测试页面"
    },
    
    # 其他文档 -> docs/其他文档/
    "其他文档": {
        "files": [
            "修改文件.txt",
            "不可用账号通知_20251121_212120.txt",
            "不可用账号通知_20251121_212224.txt",
            "群组创建测试结果.csv",
            "账号启动测试结果.csv",
            "账号测试结果_20251121_212120.json",
            "账号测试结果_20251121_212224.json",
        ],
        "target": "docs/其他文档"
    },
}

def create_directories():
    """创建目标文件夹"""
    for category, info in FILE_MAPPING.items():
        target_dir = ROOT_DIR / info["target"]
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"[OK] 创建文件夹: {target_dir}")

def move_files(dry_run=False):
    """移动文件"""
    moved = 0
    skipped = 0
    errors = []
    
    for category, info in FILE_MAPPING.items():
        target_dir = ROOT_DIR / info["target"]
        print(f"\n处理类别: {category}")
        print(f"目标目录: {target_dir}")
        
        for filename in info["files"]:
            source_file = ROOT_DIR / filename
            target_file = target_dir / filename
            
            if not source_file.exists():
                print(f"  [跳过] {filename} - 文件不存在")
                skipped += 1
                continue
            
            if target_file.exists():
                print(f"  [跳过] {filename} - 目标文件已存在")
                skipped += 1
                continue
            
            try:
                if not dry_run:
                    shutil.move(str(source_file), str(target_file))
                print(f"  [移动] {filename} -> {target_dir}")
                moved += 1
            except Exception as e:
                error_msg = f"{filename}: {str(e)}"
                errors.append(error_msg)
                print(f"  [错误] {error_msg}")
    
    return moved, skipped, errors

def main(auto_confirm=False):
    """主函数"""
    print("=" * 60)
    print("文件归类脚本")
    print("=" * 60)
    print(f"项目根目录: {ROOT_DIR}\n")
    
    # 创建文件夹
    print("创建目标文件夹...")
    create_directories()
    
    # 先进行dry run
    print("\n" + "=" * 60)
    print("预览模式（不实际移动文件）")
    print("=" * 60)
    moved, skipped, errors = move_files(dry_run=True)
    
    print(f"\n预览结果:")
    print(f"  将移动: {moved} 个文件")
    print(f"  将跳过: {skipped} 个文件")
    if errors:
        print(f"  错误: {len(errors)} 个")
    
    # 询问是否继续（如果非自动模式）
    if not auto_confirm:
        print("\n" + "=" * 60)
        try:
            response = input("是否继续执行文件移动？(y/N): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n检测到非交互式环境，自动执行...")
            response = 'y'
    else:
        response = 'y'
    
    if response == 'y':
        print("\n开始移动文件...")
        moved, skipped, errors = move_files(dry_run=False)
        
        print("\n" + "=" * 60)
        print("文件移动完成")
        print("=" * 60)
        print(f"已移动: {moved} 个文件")
        print(f"已跳过: {skipped} 个文件")
        if errors:
            print(f"错误: {len(errors)} 个")
            for error in errors:
                print(f"  - {error}")
    else:
        print("已取消")

if __name__ == "__main__":
    import sys
    try:
        # 如果提供了 --auto 参数，自动执行
        auto_confirm = '--auto' in sys.argv or '-y' in sys.argv
        main(auto_confirm=auto_confirm)
    except KeyboardInterrupt:
        print("\n\n操作已中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

