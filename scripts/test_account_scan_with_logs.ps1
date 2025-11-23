# 测试账号扫描功能并监控日志

$ErrorActionPreference = "Continue"

$baseUrl = "http://localhost:8000"

Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🧪 测试账号扫描功能（带日志监控）" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# 1. 登录
Write-Host "`n[1/3] 登录..." -ForegroundColor Yellow
$body = "username=admin@example.com&password=changeme123"
try {
    $login = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
    $token = $login.access_token
    Write-Host "   ✅ 登录成功" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 登录失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$headers = @{"Authorization" = "Bearer $token"}

# 2. 获取服务器列表
Write-Host "`n[2/3] 获取服务器列表..." -ForegroundColor Yellow
try {
    $servers = Invoke-RestMethod -Uri "$baseUrl/api/v1/group-ai/servers" -Headers $headers
    Write-Host "   ✅ 获取到 $($servers.Count) 个服务器" -ForegroundColor Green
    foreach ($server in $servers) {
        Write-Host "      - $($server.node_id): $($server.accounts_count)/$($server.max_accounts) 账号" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ 获取服务器列表失败: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "   错误详情: $($_.ErrorDetails.Message)" -ForegroundColor Gray
    }
    exit 1
}

# 3. 测试扫描服务器账号
Write-Host "`n[3/3] 测试扫描服务器账号..." -ForegroundColor Yellow
if ($servers -and $servers.Count -gt 0) {
    $testServerId = $servers[0].node_id
    Write-Host "   测试服务器: $testServerId" -ForegroundColor Gray
    Write-Host "   发送请求到: $baseUrl/api/v1/group-ai/account-management/scan-server-accounts?server_id=$testServerId" -ForegroundColor Gray
    
    try {
        $accounts = Invoke-RestMethod -Uri "$baseUrl/api/v1/group-ai/account-management/scan-server-accounts?server_id=$testServerId" -Headers $headers -TimeoutSec 20
        Write-Host "   ✅ 扫描成功" -ForegroundColor Green
        
        if ($accounts -and $accounts.Count -gt 0) {
            $serverData = $accounts[0]
            Write-Host "      服务器: $($serverData.server_id)" -ForegroundColor Gray
            Write-Host "      账号数: $($serverData.total_count)" -ForegroundColor Gray
            
            if ($serverData.accounts -and $serverData.accounts.Count -gt 0) {
                Write-Host "      账号列表:" -ForegroundColor Gray
                foreach ($acc in $serverData.accounts) {
                    Write-Host "         - $($acc.account_id): $($acc.session_file)" -ForegroundColor Gray
                }
            } else {
                Write-Host "      ⚠️  账号列表为空" -ForegroundColor Yellow
                Write-Host "      这可能是因为:" -ForegroundColor Yellow
                Write-Host "        1. 服务器上确实没有账号文件" -ForegroundColor Gray
                Write-Host "        2. 扫描函数无法找到文件" -ForegroundColor Gray
                Write-Host "        3. 无法从文件名提取账号ID" -ForegroundColor Gray
            }
        } else {
            Write-Host "   ⚠️  返回数据为空" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ❌ 扫描失败: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host "   错误详情: $($_.ErrorDetails.Message)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "   ⚠️  没有可用的服务器进行测试" -ForegroundColor Yellow
}

Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "✅ 测试完成" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 提示: 请查看后端日志中的扫描相关信息" -ForegroundColor Yellow
Write-Host "   查找包含 '扫描服务器'、'找到.*账号'、'账号ID' 的日志" -ForegroundColor Gray

