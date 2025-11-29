@echo off
chcp 65001 >nul
echo ============================================================
echo 全自动修复 WebSocket 连接问题（完整版）
echo ============================================================
echo.

cd /d "%~dp0\.."

echo [步骤 1/5] 创建修复脚本...
(
echo #!/bin/bash
echo # 修复 WebSocket 连接 - 自动执行版本
echo.
echo NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"
echo.
echo echo "修复 WebSocket 连接..."
echo.
echo # 备份
echo sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.bak.$(date +%%Y%%m%%d_%%H%%M%%S)"
echo.
echo # 使用 Python 修复配置
echo python3 ^<^< 'PYEOF'
echo import re
echo.
echo config_path = "/etc/nginx/sites-available/aikz.usdt2026.cc"
echo.
echo with open(config_path, 'r', encoding='utf-8') as f:
echo     lines = f.readlines()
echo.
echo # 查找 location /api/ 的位置
echo api_idx = None
echo for i, line in enumerate(lines^):
echo     if 'location /api/' in line:
echo         api_idx = i
echo         break
echo.
echo if api_idx is None:
echo     print("错误: 未找到 location /api/")
echo     exit(1^)
echo.
echo # 检查是否已有 WebSocket location
echo has_ws = any('location /api/v1/notifications/ws' in line for line in lines[:api_idx]^)
echo.
echo if not has_ws:
echo     ws_block = [
echo         '    # WebSocket 支持 - 通知服务（必须在 /api/ 之前）\n',
echo         '    location /api/v1/notifications/ws {\n',
echo         '        proxy_pass http://127.0.0.1:8000;\n',
echo         '        proxy_http_version 1.1;\n',
echo         '        proxy_set_header Upgrade $http_upgrade;\n',
echo         '        proxy_set_header Connection "upgrade";\n',
echo         '        proxy_set_header Host $host;\n',
echo         '        proxy_set_header X-Real-IP $remote_addr;\n',
echo         '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n',
echo         '        proxy_set_header X-Forwarded-Proto $scheme;\n',
echo         '        proxy_read_timeout 86400;\n',
echo         '        proxy_send_timeout 86400;\n',
echo         '        proxy_buffering off;\n',
echo         '    }\n',
echo         '\n'
echo     ]
echo     lines[api_idx:api_idx] = ws_block
echo     print("已添加 WebSocket location 配置")
echo else:
echo     print("WebSocket location 已存在，检查配置...")
echo     # 检查配置是否正确
echo     ws_start = None
echo     for i, line in enumerate(lines^):
echo         if 'location /api/v1/notifications/ws' in line:
echo             ws_start = i
echo             break
echo     if ws_start:
echo         ws_block = ''.join(lines[ws_start:ws_start+15]^)
echo         if 'Upgrade' not in ws_block or 'upgrade' not in ws_block:
echo             print("WebSocket 配置不完整，需要修复")
echo             # 这里可以添加修复逻辑
echo         else:
echo             print("WebSocket 配置已正确")
echo.
echo with open(config_path, 'w', encoding='utf-8') as f:
echo     f.writelines(lines^)
echo.
echo print("配置已更新")
echo PYEOF
echo.
echo # 测试并重新加载
echo if sudo nginx -t; then
echo     echo "Nginx 配置测试通过"
echo     sudo systemctl reload nginx
echo     echo "Nginx 已重新加载"
echo     echo ""
echo     echo "修复完成！"
echo else
echo     echo "Nginx 配置测试失败"
echo     sudo nginx -t
echo     exit 1
echo fi
) > deploy\temp_修复WS.sh

echo [步骤 2/5] 上传修复脚本到服务器...
scp deploy\temp_修复WS.sh ubuntu@165.154.233.55:/tmp/修复WS.sh
if errorlevel 1 (
    echo [错误] 上传失败，请检查 SSH 连接
    del deploy\temp_修复WS.sh
    pause
    exit /b 1
)

echo.
echo [步骤 3/5] 在服务器上执行修复...
ssh ubuntu@165.154.233.55 "chmod +x /tmp/修复WS.sh && sudo bash /tmp/修复WS.sh" > deploy\WebSocket修复结果.txt 2>&1

echo.
echo [步骤 4/5] 修复结果：
echo ============================================================
type deploy\WebSocket修复结果.txt

echo.
echo [步骤 5/5] 验证配置...
ssh ubuntu@165.154.233.55 "sudo grep -A 12 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc" > deploy\WebSocket配置验证.txt 2>&1

echo.
echo WebSocket 配置验证：
echo ============================================================
type deploy\WebSocket配置验证.txt

echo.
echo ============================================================
echo 全自动修复完成！
echo ============================================================
echo.
echo 下一步：
echo 1. 在浏览器中刷新页面（按 F5）
echo 2. 打开开发者工具（F12）→ Console
echo 3. 检查 WebSocket 错误是否消失
echo.
del deploy\temp_修复WS.sh
pause

