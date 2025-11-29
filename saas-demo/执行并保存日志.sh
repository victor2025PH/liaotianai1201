#!/bin/bash
# 执行测试并保存日志到文件

LOG_FILE="~/liaotian/test_execution_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================"
echo "开始执行时间: $(date)"
echo "日志文件: $LOG_FILE"
echo "========================================"
echo ""

cd ~/liaotian/saas-demo
bash 一键执行所有测试.sh

echo ""
echo "========================================"
echo "执行完成时间: $(date)"
echo "========================================"
