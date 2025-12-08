@echo off
REM 运行数据库迁移脚本

cd /d %~dp0
python -m alembic upgrade head

