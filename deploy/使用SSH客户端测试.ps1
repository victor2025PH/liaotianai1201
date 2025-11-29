# 使用 SSH 客户端工具进行测试
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "SSH 连接测试 - 使用 SSH 客户端" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 检查 SSH 客户端
Write-Host "[检查] SSH 客户端..." -ForegroundColor Yellow
$sshPath = (Get-Command ssh -ErrorAction SilentlyContinue).Source
if ($sshPath) {
    Write-Host "✓ 找到 SSH 客户端: $sshPath" -ForegroundColor Green
} else {
    Write-Host "✗ 未找到 SSH 客户端" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 测试 1: 基本连接
Write-Host "[测试 1] 基本连接测试..." -ForegroundColor Yellow
Write-Host "执行: ssh ubuntu@165.154.233.55 `"echo 'SSH 连接测试成功 - TEST123'`"" -ForegroundColor Gray
$output1 = & ssh ubuntu@165.154.233.55 "echo 'SSH 连接测试成功 - TEST123'" 2>&1
Write-Host "输出:" -ForegroundColor Green
Write-Host $output1
Write-Host ""

# 测试 2: 系统信息
Write-Host "[测试 2] 系统信息..." -ForegroundColor Yellow
Write-Host "执行: ssh ubuntu@165.154.233.55 `"whoami && hostname && pwd`"" -ForegroundColor Gray
$output2 = & ssh ubuntu@165.154.233.55 "whoami && hostname && pwd" 2>&1
Write-Host "输出:" -ForegroundColor Green
Write-Host $output2
Write-Host ""

# 测试 3: Nginx 配置
Write-Host "[测试 3] Nginx 配置语法检查..." -ForegroundColor Yellow
Write-Host "执行: ssh ubuntu@165.154.233.55 `"sudo nginx -t`"" -ForegroundColor Gray
$output3 = & ssh ubuntu@165.154.233.55 "sudo nginx -t" 2>&1
Write-Host "输出:" -ForegroundColor Green
Write-Host $output3
Write-Host ""

# 测试 4: WebSocket 配置
Write-Host "[测试 4] WebSocket 配置检查..." -ForegroundColor Yellow
Write-Host "执行: ssh ubuntu@165.154.233.55 `"sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc`"" -ForegroundColor Gray
$output4 = & ssh ubuntu@165.154.233.55 "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc" 2>&1
Write-Host "输出:" -ForegroundColor Green
if ($output4) {
    Write-Host $output4
} else {
    Write-Host "(未找到 WebSocket 配置)" -ForegroundColor Red
}
Write-Host ""

# 测试 5: 服务状态
Write-Host "[测试 5] 服务状态检查..." -ForegroundColor Yellow
Write-Host "执行: ssh ubuntu@165.154.233.55 `"sudo systemctl is-active nginx`"" -ForegroundColor Gray
$output5 = & ssh ubuntu@165.154.233.55 "sudo systemctl is-active nginx" 2>&1
Write-Host "Nginx 状态:" -ForegroundColor Green
Write-Host $output5
Write-Host ""

Write-Host "执行: ssh ubuntu@165.154.233.55 `"sudo systemctl is-active liaotian-backend`"" -ForegroundColor Gray
$output6 = & ssh ubuntu@165.154.233.55 "sudo systemctl is-active liaotian-backend" 2>&1
Write-Host "后端服务状态:" -ForegroundColor Green
Write-Host $output6
Write-Host ""

# 测试 6: 后端日志
Write-Host "[测试 6] 后端日志（最近5条）..." -ForegroundColor Yellow
Write-Host "执行: ssh ubuntu@165.154.233.55 `"sudo journalctl -u liaotian-backend -n 5 --no-pager`"" -ForegroundColor Gray
$output7 = & ssh ubuntu@165.154.233.55 "sudo journalctl -u liaotian-backend -n 5 --no-pager" 2>&1
Write-Host "输出:" -ForegroundColor Green
Write-Host $output7
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

