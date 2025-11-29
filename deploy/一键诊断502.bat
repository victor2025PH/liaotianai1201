@echo off
chcp 65001 >nul
echo ========================================
echo 诊断502错误 - 收集服务器信息
echo ========================================
echo.

echo [1] 检查服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-frontend --no-pager | head -20" > deploy/诊断结果-服务状态.txt 2>&1
type deploy/诊断结果-服务状态.txt

echo.
echo [2] 查看服务日志...
ssh ubuntu@165.154.233.55 "sudo journalctl -u liaotian-frontend -n 50 --no-pager" > deploy/诊断结果-服务日志.txt 2>&1
type deploy/诊断结果-服务日志.txt

echo.
echo [3] 检查端口监听...
ssh ubuntu@165.154.233.55 "ss -tlnp | grep ':3000'" > deploy/诊断结果-端口监听.txt 2>&1
type deploy/诊断结果-端口监听.txt

echo.
echo [4] 检查standalone目录...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && STANDALONE_DIR=\$(find .next/standalone -name 'server.js' -type f 2>/dev/null | head -1 | xargs dirname) && echo \"Standalone目录: \$STANDALONE_DIR\" && ls -la \"\$STANDALONE_DIR/server.js\" 2>&1" > deploy/诊断结果-standalone目录.txt 2>&1
type deploy/诊断结果-standalone目录.txt

echo.
echo [5] 检查systemd服务配置...
ssh ubuntu@165.154.233.55 "cat /etc/systemd/system/liaotian-frontend.service" > deploy/诊断结果-服务配置.txt 2>&1
type deploy/诊断结果-服务配置.txt

echo.
echo ========================================
echo 诊断完成！结果已保存到 deploy/ 目录
echo ========================================
pause

