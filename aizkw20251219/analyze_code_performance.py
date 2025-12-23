#!/usr/bin/env python3
"""
admin-backend 代码性能分析脚本
检查常见的性能问题：
1. 同步阻塞操作
2. 未使用异步队列的重计算任务
3. 数据库连接池配置问题
"""

import os
import re
import sys
from pathlib import Path

ADMIN_BACKEND_DIR = "/home/ubuntu/telegram-ai-system/admin-backend"

def find_files(directory, pattern):
    """查找匹配模式的文件"""
    files = []
    for root, dirs, filenames in os.walk(directory):
        # 跳过虚拟环境和缓存目录
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
        for filename in filenames:
            if re.search(pattern, filename):
                files.append(os.path.join(root, filename))
    return files

def analyze_main_py(main_file):
    """分析 main.py 文件"""
    issues = []
    if not os.path.exists(main_file):
        return ["❌ main.py 不存在"]
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # 检查同步路由
    sync_routes = []
    for i, line in enumerate(lines, 1):
        if re.search(r'@app\.(get|post|put|delete|patch)\s*\(', line, re.IGNORECASE):
            # 检查下一个函数定义是否是同步的
            for j in range(i, min(i+10, len(lines))):
                if re.search(r'^\s*def\s+\w+', lines[j]) and 'async' not in lines[j]:
                    sync_routes.append((i, line.strip(), lines[j].strip()))
                    break
                elif re.search(r'^\s*async\s+def\s+\w+', lines[j]):
                    break
    
    if sync_routes:
        issues.append("⚠️  发现同步路由（可能阻塞主线程）:")
        for line_num, route, func in sync_routes[:5]:
            issues.append(f"  行 {line_num}: {route} -> {func}")
    
    # 检查重计算操作
    heavy_ops = []
    patterns = [
        (r'for\s+\w+\s+in\s+range\s*\([^)]+\)', 'for 循环'),
        (r'while\s+True', '无限循环'),
        (r'\.map\s*\(', 'map 操作'),
        (r'\.filter\s*\(', 'filter 操作'),
        (r'sorted\s*\(', '排序操作'),
        (r'\.sort\s*\(', '排序操作'),
    ]
    
    for i, line in enumerate(lines, 1):
        for pattern, desc in patterns:
            if re.search(pattern, line):
                heavy_ops.append((i, desc, line.strip()[:80]))
    
    if heavy_ops:
        issues.append("⚠️  发现可能的重计算操作:")
        for line_num, desc, code in heavy_ops[:10]:
            issues.append(f"  行 {line_num} ({desc}): {code}")
    
    return issues

def analyze_database_config(db_files):
    """分析数据库配置"""
    issues = []
    
    for db_file in db_files:
        with open(db_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查连接池配置
        if 'create_engine' in content:
            if 'pool_size' not in content and 'poolclass' not in content:
                issues.append(f"⚠️  {db_file}: 未配置连接池大小 (pool_size)")
            if 'max_overflow' not in content:
                issues.append(f"⚠️  {db_file}: 未配置最大溢出连接数 (max_overflow)")
            if 'pool_pre_ping' not in content:
                issues.append(f"⚠️  {db_file}: 建议启用 pool_pre_ping 以检测断开的连接")
            if 'pool_recycle' not in content:
                issues.append(f"⚠️  {db_file}: 建议设置 pool_recycle 以回收旧连接")
        
        # 检查 Session 管理
        if 'SessionLocal' in content or 'sessionmaker' in content:
            # 检查是否有正确的上下文管理器或依赖注入
            if 'Depends' not in content and 'with' not in content:
                issues.append(f"⚠️  {db_file}: Session 可能未正确关闭")
    
    return issues

def analyze_routes(route_files):
    """分析路由文件"""
    issues = []
    
    for route_file in route_files:
        with open(route_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # 检查同步数据库操作
        for i, line in enumerate(lines, 1):
            # 检查同步查询（没有 await）
            if re.search(r'\.(query|get|all|first|filter|filter_by)\s*\(', line):
                # 检查前后是否有 await
                context = '\n'.join(lines[max(0, i-3):min(len(lines), i+3)])
                if 'await' not in context and 'async def' in '\n'.join(lines[:i]):
                    issues.append(f"⚠️  {route_file}:行 {i}: 可能的同步数据库操作: {line.strip()[:60]}")
        
        # 检查是否有重计算任务未放入队列
        for i, line in enumerate(lines, 1):
            if re.search(r'(for|while|map|filter|sorted)', line):
                # 检查是否在异步任务中
                func_start = max(0, i-20)
                func_context = '\n'.join(lines[func_start:i])
                if '@app.' in func_context and 'celery' not in func_context.lower() and 'task' not in func_context.lower():
                    issues.append(f"⚠️  {route_file}:行 {i}: 重计算任务可能应放入异步队列: {line.strip()[:60]}")
    
    return issues

def check_celery_config(directory):
    """检查 Celery 配置"""
    issues = []
    
    celery_files = find_files(directory, r'celery|tasks\.py')
    if not celery_files:
        issues.append("⚠️  未找到 Celery 配置文件，所有任务可能都在主线程执行")
    else:
        issues.append(f"✓ 找到 Celery 配置: {', '.join(celery_files)}")
    
    return issues

def main():
    print("===== admin-backend 代码性能分析 =====\n")
    
    if not os.path.exists(ADMIN_BACKEND_DIR):
        print(f"❌ 目录不存在: {ADMIN_BACKEND_DIR}")
        print("请确认 admin-backend 的路径")
        return
    
    os.chdir(ADMIN_BACKEND_DIR)
    print(f"分析目录: {os.getcwd()}\n")
    
    # 1. 分析 main.py
    print("=== 1. 分析 main.py ===")
    main_file = os.path.join(ADMIN_BACKEND_DIR, "app", "main.py")
    if os.path.exists(main_file):
        issues = analyze_main_py(main_file)
        for issue in issues:
            print(issue)
    else:
        print("❌ app/main.py 不存在")
    print()
    
    # 2. 分析数据库配置
    print("=== 2. 分析数据库配置 ===")
    db_files = find_files(ADMIN_BACKEND_DIR, r'(database|db|config|models)\.py')
    if db_files:
        issues = analyze_database_config(db_files[:5])
        for issue in issues:
            print(issue)
    else:
        print("⚠️  未找到数据库配置文件")
    print()
    
    # 3. 分析路由文件
    print("=== 3. 分析路由文件 ===")
    route_files = find_files(ADMIN_BACKEND_DIR, r'(routes|routers|api|views)\.py')
    if route_files:
        issues = analyze_routes(route_files[:10])
        for issue in issues[:20]:  # 限制输出
            print(issue)
        if len(issues) > 20:
            print(f"... 还有 {len(issues) - 20} 个问题")
    else:
        print("⚠️  未找到路由文件")
    print()
    
    # 4. 检查 Celery 配置
    print("=== 4. 检查异步任务队列 ===")
    issues = check_celery_config(ADMIN_BACKEND_DIR)
    for issue in issues:
        print(issue)
    print()
    
    print("===== 分析完成 =====")

if __name__ == "__main__":
    main()


