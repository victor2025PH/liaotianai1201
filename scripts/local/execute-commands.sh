#!/bin/bash
# 在服务器上执行的命令脚本

set -e

echo '=== service status ==='
sudo systemctl status liaotian-frontend.service --no-pager

echo ''
echo '=== service file ==='
sudo systemctl cat liaotian-frontend.service

