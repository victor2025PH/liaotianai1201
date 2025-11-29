@echo off
chcp 65001 >nul
echo ============================================================
echo 全自动修复 WebSocket 连接问题
echo ============================================================
echo.
echo 正在执行修复，请稍候...
echo.

cd /d "%~dp0\.."

REM 创建临时修复脚本
echo 创建修复脚本...
(
echo #!/bin/bash
echo NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"
echo echo "修复 WebSocket 连接..."
echo sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.bak.$(date +%%Y%%m%%d_%%H%%M%%S)"
echo.
echo python3 ^<^< 'PYEOF'
echo import re
echo config_path = "/etc/nginx/sites-available/aikz.usdt2026.cc"
echo with open(config_path, 'r', encoding='utf-8') as f:
echo     lines = f.readlines()
echo api_idx = None
echo for i, line in enumerate(lines^):
echo     if 'location /api/' in line:
echo         api_idx = i
echo         break
echo if api_idx is None:
echo     print("错误: 未找到 location /api/")
echo     exit(1^)
echo has_ws = any('location /api/v1/notifications/ws' in line for line in lines[:api_idx]^)
echo if not has_ws:
echo     ws_block = ['    # WebSocket 支持\n', '    location /api/v1/notifications/ws {\n', '        proxy_pass http://127.0.0.1:8000;\n', '        proxy_http_version 1.1;\n', '        proxy_set_header Upgrade $http_upgrade;\n', '        proxy_set_header Connection "upgrade";\n', '        proxy_set_header Host $host;\n', '        proxy_set_header X-Real-IP $remote_addr;\n', '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n', '        proxy_set_header X-Forwarded-Proto $scheme;\n', '        proxy_read_timeout 86400;\n', '        proxy_send_timeout 86400;\n', '        proxy_buffering off;\n', '    }\n', '\n']
echo     lines[api_idx:api_idx] = ws_block
echo     print("已添加 WebSocket location")
echo else:
echo     print("WebSocket location 已存在")
echo with open(config_path, 'w', encoding='utf-8') as f:
echo     f.writelines(lines^)
echo print("配置已更新")
echo PYEOF
echo.
echo if sudo nginx -t; then
echo     sudo systemctl reload nginx
echo     echo "修复完成！"
echo else
echo     echo "配置测试失败"
echo     sudo nginx -t
echo     exit 1
echo fi
) > deploy\temp_ws_fix.sh

echo 上传并执行修复脚本...
scp deploy\temp_ws_fix.sh ubuntu@165.154.233.55:/tmp/修复WS.sh
if errorlevel 1 (
    echo.
    echo [错误] SSH 连接失败
    echo 请检查网络连接和 SSH 配置
    del deploy\temp_ws_fix.sh
    pause
    exit /b 1
)

echo.
echo 在服务器上执行修复...
ssh ubuntu@165.154.233.55 "chmod +x /tmp/修复WS.sh && sudo bash /tmp/修复WS.sh"

echo.
echo ============================================================
echo 修复完成！
echo ============================================================
echo.
echo 下一步：
echo 1. 在浏览器中刷新页面（按 F5）
echo 2. 打开开发者工具（F12）→ Console
echo 3. 检查 WebSocket 错误是否消失
echo.

del deploy\temp_ws_fix.sh
pause

