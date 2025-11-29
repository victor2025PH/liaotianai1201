# 诊断输出问题
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "SSH 连接测试 - PowerShell 版本" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 测试 1
Write-Host "[测试 1] 基本连接..." -ForegroundColor Yellow
$result1 = ssh ubuntu@165.154.233.55 "echo 'SSH 连接测试成功 - TEST123'" 2>&1
Write-Host "结果:" -ForegroundColor Green
Write-Host $result1
Write-Host ""

# 测试 2
Write-Host "[测试 2] 系统信息..." -ForegroundColor Yellow
$result2 = ssh ubuntu@165.154.233.55 "whoami" 2>&1
Write-Host "用户:" -ForegroundColor Green
Write-Host $result2
$result3 = ssh ubuntu@165.154.233.55 "hostname" 2>&1
Write-Host "主机名:" -ForegroundColor Green
Write-Host $result3
Write-Host ""

# 测试 3
Write-Host "[测试 3] Nginx 配置..." -ForegroundColor Yellow
$result4 = ssh ubuntu@165.154.233.55 "sudo nginx -t" 2>&1
Write-Host "结果:" -ForegroundColor Green
Write-Host $result4
Write-Host ""

# 测试 4
Write-Host "[测试 4] WebSocket 配置..." -ForegroundColor Yellow
$result5 = ssh ubuntu@165.154.233.55 "sudo grep -A 10 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc" 2>&1
Write-Host "结果:" -ForegroundColor Green
if ($result5) {
    Write-Host $result5
} else {
    Write-Host "(未找到配置)" -ForegroundColor Red
}
Write-Host ""

# 测试 5
Write-Host "[测试 5] 服务状态..." -ForegroundColor Yellow
$result6 = ssh ubuntu@165.154.233.55 "sudo systemctl is-active nginx" 2>&1
Write-Host "Nginx:" -ForegroundColor Green
Write-Host $result6
$result7 = ssh ubuntu@165.154.233.55 "sudo systemctl is-active liaotian-backend" 2>&1
Write-Host "后端:" -ForegroundColor Green
Write-Host $result7
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

