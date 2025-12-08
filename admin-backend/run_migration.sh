#!/bin/bash
# 运行数据库迁移脚本

cd "$(dirname "$0")"
python -m alembic upgrade head

