#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查文件夹大小，找出占用空间大的文件和目录
"""

import os
from pathlib import Path
from collections import defaultdict

def get_size(path):
    """获取文件或目录大小"""
    if os.path.isfile(path):
        return os.path.getsize(path)
    elif os.path.isdir(path):
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += get_size(entry.path)
        except PermissionError:
            pass
        return total
    return 0

def format_size(size):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def analyze_directory(directory):
    """分析目录，找出大文件和目录"""
    path = Path(directory)
    if not path.exists():
        print(f"[ERROR] 目录不存在: {directory}")
        return
    
    print("=" * 70)
    print(f"分析目录: {directory}")
    print("=" * 70)
    
    # 总大小
    total_size = get_size(directory)
    print(f"\n总大小: {format_size(total_size)}")
    
    # 分析子目录和文件
    print("\n" + "=" * 70)
    print("占用空间最大的目录/文件（前20）:")
    print("=" * 70)
    
    sizes = []
    
    # 检查根目录下的文件和目录
    try:
        for item in path.iterdir():
            item_size = get_size(item)
            sizes.append((item.name, item_size, item.is_dir()))
    except PermissionError as e:
        print(f"[ERROR] 权限错误: {e}")
        return
    
    # 按大小排序
    sizes.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n{'类型':<8} {'大小':<15} {'名称'}")
    print("-" * 70)
    
    for name, size, is_dir in sizes[:20]:
        item_type = "目录" if is_dir else "文件"
        print(f"{item_type:<8} {format_size(size):<15} {name}")
    
    # 检查常见的不需要上传的目录
    print("\n" + "=" * 70)
    print("检查常见的不需要上传的目录:")
    print("=" * 70)
    
    exclude_patterns = [
        '.venv', 'venv', 'env', '__pycache__', '.pytest_cache',
        '.git', 'node_modules', '.next', 'dist', 'build',
        '*.pyc', '*.pyo', '*.log', '.DS_Store', 'Thumbs.db',
        '.idea', '.vscode', '*.egg-info'
    ]
    
    exclude_sizes = {}
    total_exclude = 0
    
    for name, size, is_dir in sizes:
        should_exclude = False
        exclude_reason = ""
        
        if is_dir:
            if name in ['.venv', 'venv', 'env', '__pycache__', '.pytest_cache', '.git', 'node_modules', '.next', 'dist', 'build', '.idea', '.vscode']:
                should_exclude = True
                exclude_reason = "开发环境/缓存目录"
            elif name.endswith('.egg-info'):
                should_exclude = True
                exclude_reason = "Python 包信息"
        else:
            if name.endswith(('.pyc', '.pyo', '.log', '.DS_Store', 'Thumbs.db')):
                should_exclude = True
                exclude_reason = "缓存/日志文件"
        
        if should_exclude:
            exclude_sizes[name] = (size, exclude_reason)
            total_exclude += size
    
    if exclude_sizes:
        print(f"\n可以排除的文件/目录（可节省 {format_size(total_exclude)}）:")
        print(f"\n{'类型':<8} {'大小':<15} {'原因':<20} {'名称'}")
        print("-" * 70)
        for name, (size, reason) in sorted(exclude_sizes.items(), key=lambda x: x[1][0], reverse=True):
            item_type = "目录" if Path(path / name).is_dir() else "文件"
            print(f"{item_type:<8} {format_size(size):<15} {reason:<20} {name}")
    else:
        print("\n未发现明显可以排除的目录")
    
    # 建议
    print("\n" + "=" * 70)
    print("建议:")
    print("=" * 70)
    print("\n不需要上传的文件/目录:")
    print("  1. 虚拟环境: .venv, venv, env")
    print("  2. Python 缓存: __pycache__, *.pyc, *.pyo")
    print("  3. Git 目录: .git")
    print("  4. 构建产物: .next, dist, build")
    print("  5. 日志文件: *.log")
    print("  6. IDE 配置: .idea, .vscode")
    print("  7. 系统文件: .DS_Store, Thumbs.db")
    print("\n建议:")
    print("  1. 创建 .gitignore 或 .deployignore 文件")
    print("  2. 使用压缩包上传（自动排除不需要的文件）")
    print("  3. 在服务器上直接安装依赖，而不是上传虚拟环境")

if __name__ == "__main__":
    directory = r"C:\Users\Administrator\Desktop\liaotian20251126\admin-backend-deploy"
    analyze_directory(directory)

