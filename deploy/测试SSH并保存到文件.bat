@echo off
chcp 65001 >nul
title SSH 测试 - 保存到文件
echo.
echo ============================================================
echo            SSH 连接测试 - 保存结果到文件
echo ============================================================
echo.

set OUTPUT_FILE=SSH测试结果_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
set OUTPUT_FILE=%OUTPUT_FILE: =0%

echo 测试结果将保存到: %OUTPUT_FILE%
echo.

(
    echo ============================================================
    echo SSH 连接测试结果
    echo ============================================================
    echo 测试时间: %date% %time%
    echo.
    
    echo [测试 1] 基本连接测试...
    echo ----------------------------------------
    ssh ubuntu@165.154.233.55 "echo 'SSH 连接测试成功 - TEST123'"
    echo.
    
    echo [测试 2] 系统信息...
    echo ----------------------------------------
    ssh ubuntu@165.154.233.55 "whoami"
    ssh ubuntu@165.154.233.55 "hostname"
    ssh ubuntu@165.154.233.55 "pwd"
    echo.
    
    echo [测试 3] Nginx 配置语法检查...
    echo ----------------------------------------
    ssh ubuntu@165.154.233.55 "sudo nginx -t"
    echo.
    
    echo [测试 4] WebSocket 配置检查...
    echo ----------------------------------------
    ssh ubuntu@165.154.233.55 "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
    echo.
    
    echo [测试 5] 服务状态...
    echo ----------------------------------------
    ssh ubuntu@165.154.233.55 "sudo systemctl is-active nginx"
    ssh ubuntu@165.154.233.55 "sudo systemctl is-active liaotian-backend"
    echo.
    
    echo [测试 6] 后端日志（最近5条）...
    echo ----------------------------------------
    ssh ubuntu@165.154.233.55 "sudo journalctl -u liaotian-backend -n 5 --no-pager"
    echo.
    
    echo ============================================================
    echo 测试完成
    echo ============================================================
) > "%OUTPUT_FILE%" 2>&1

echo.
echo 测试完成！结果已保存到: %OUTPUT_FILE%
echo.
type "%OUTPUT_FILE%"
echo.
pause

