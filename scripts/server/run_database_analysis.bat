@echo off
chcp 65001 > nul
echo ============================================
echo 数据库慢查询分析（本地执行）
echo ============================================
echo.
echo 注意：此脚本需要在服务器上执行
echo 请使用 SSH 连接到服务器后运行 run_database_analysis.sh
echo.
echo 或者手动执行以下命令：
echo cd admin-backend
echo python scripts/analyze_slow_queries.py
echo python scripts/optimize_database_queries.py
echo.
pause

