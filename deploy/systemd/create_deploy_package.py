#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建优化的部署包（排除不需要的文件）
"""

import os
import shutil
import tarfile
from pathlib import Path

def should_exclude(path, name):
    """判断文件/目录是否应该排除"""
    exclude_patterns = [
        # 虚拟环境
        '.venv', 'venv', 'env', 'ENV',
        # Python 缓存
        '__pycache__', '.pytest_cache', '*.pyc', '*.pyo', '*.py[co]',
        # Git
        '.git', '.gitignore',
        # 构建产物
        '.next', 'dist', 'build', '*.egg-info',
        # 日志
        '*.log', 'logs',
        # IDE
        '.idea', '.vscode', '.vs',
        # 系统文件
        '.DS_Store', 'Thumbs.db', 'desktop.ini',
        # 其他
        'node_modules', '.cache', '.tmp', 'temp', 'tmp'
    ]
    
    # 检查完整路径和名称
    path_str = str(path).lower()
    name_lower = name.lower()
    
    for pattern in exclude_patterns:
        if pattern.startswith('*'):
            if name_lower.endswith(pattern[1:]):
                return True
        elif name_lower == pattern or pattern in path_str:
            return True
    
    return False

def create_deploy_package(source_dir, output_file, exclude_func=None):
    """创建部署包"""
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"[ERROR] 源目录不存在: {source_dir}")
        return False
    
    print("=" * 70)
    print("创建优化的部署包")
    print("=" * 70)
    print(f"\n源目录: {source_dir}")
    print(f"输出文件: {output_file}")
    
    exclude_func = exclude_func or should_exclude
    
    # 统计信息
    total_files = 0
    excluded_files = 0
    total_size = 0
    excluded_size = 0
    
    print("\n扫描文件...")
    
    with tarfile.open(output_file, 'w:gz') as tar:
        for root, dirs, files in os.walk(source_path):
            # 过滤目录
            dirs[:] = [d for d in dirs if not exclude_func(Path(root) / d, d)]
            
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(source_path.parent)
                
                total_files += 1
                file_size = file_path.stat().st_size
                total_size += file_size
                
                if exclude_func(file_path, file):
                    excluded_files += 1
                    excluded_size += file_size
                    continue
                
                # 添加到压缩包
                try:
                    tar.add(file_path, arcname=rel_path)
                except Exception as e:
                    print(f"  [WARNING] 跳过文件 {rel_path}: {e}")
    
    output_size = Path(output_file).stat().st_size
    
    print("\n" + "=" * 70)
    print("打包完成")
    print("=" * 70)
    print(f"\n统计信息:")
    print(f"  总文件数: {total_files}")
    print(f"  排除文件数: {excluded_files}")
    print(f"  包含文件数: {total_files - excluded_files}")
    print(f"\n大小:")
    print(f"  原始大小: {total_size / 1024 / 1024:.2f} MB")
    print(f"  排除大小: {excluded_size / 1024 / 1024:.2f} MB")
    print(f"  压缩后大小: {output_size / 1024 / 1024:.2f} MB")
    print(f"  节省空间: {(excluded_size / 1024 / 1024):.2f} MB")
    print(f"\n输出文件: {output_file}")
    
    return True

if __name__ == "__main__":
    base_dir = Path(r"C:\Users\Administrator\Desktop\liaotian20251126")
    
    # 创建后端部署包
    backend_source = base_dir / "admin-backend-deploy"
    backend_output = base_dir / "admin-backend-deploy-clean.tar.gz"
    
    if backend_source.exists():
        print("\n创建后端部署包...")
        create_deploy_package(str(backend_source), str(backend_output))
    
    # 前端已经是压缩包，不需要处理
    print("\n前端已经是 frontend.zip，无需处理")

