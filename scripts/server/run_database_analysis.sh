#!/bin/bash
# 在服务器上运行数据库慢查询分析脚本

set -e

echo "============================================"
echo "数据库慢查询分析"
echo "============================================"

# 进入项目目录
cd /home/ubuntu/telegram-ai-system/admin-backend

# 激活虚拟环境
source venv/bin/activate

# 运行分析脚本
echo "正在运行慢查询分析..."
python scripts/analyze_slow_queries.py

# 运行优化脚本
echo ""
echo "正在运行数据库优化..."
python scripts/optimize_database_queries.py

echo ""
echo "============================================"
echo "分析完成"
echo "============================================"
echo "详细报告已保存到: admin-backend/database_analysis_report.json"

