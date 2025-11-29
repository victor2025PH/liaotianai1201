#!/bin/bash
# 查看分配剧本功能的实时日志

echo "========================================="
echo "查看分配剧本功能的实时日志"
echo "========================================="
echo ""
echo "按 Ctrl+C 退出监控"
echo ""
echo "等待日志输出..."
echo ""

# 检查日志文件是否存在
if [ ! -f "/tmp/backend_final.log" ]; then
    echo "⚠ 日志文件不存在: /tmp/backend_final.log"
    echo ""
    echo "请先启动后端服务:"
    echo "  bash ~/liaotian/deploy/强制启动并诊断服务.sh"
    exit 1
fi

# 实时监控日志
tail -f /tmp/backend_final.log | grep --line-buffered -E "MIDDLEWARE|UPDATE_ACCOUNT|server_id|账号ID匹配|639277358115|computer_001|扫描服务器|账号.*不存在|账号.*存在"
