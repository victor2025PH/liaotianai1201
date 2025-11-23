# 全面测试所有功能并监控日志
# 包括登录、服务器管理、账号管理等

$ErrorActionPreference = "Continue"

$projectRoot = "E:\002-工作文件\重要程序\聊天AI群聊程序"
$baseUrl = "http://localhost:8000"
$frontendUrl = "http://localhost:3000"

Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🧪 全面测试所有功能" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# 1. 测试后端健康检查
Write-Host "`n[1/8] 测试后端健康检查..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health" -TimeoutSec 5
    Write-Host "   ✅ 后端健康: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 后端健康检查失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. 测试登录
Write-Host "`n[2/8] 测试登录..." -ForegroundColor Yellow
# OAuth2PasswordRequestForm 需要 application/x-www-form-urlencoded 格式
$loginBody = "username=admin@example.com&password=changeme123"

try {
    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method Post -Body $loginBody -ContentType "application/x-www-form-urlencoded" -TimeoutSec 10
    $token = $loginResponse.access_token
    Write-Host "   ✅ 登录成功" -ForegroundColor Green
    Write-Host "   Token: $($token.Substring(0, 30))..." -ForegroundColor Gray
} catch {
    Write-Host "   ❌ 登录失败: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   尝试重置管理员密码..." -ForegroundColor Yellow
    # 尝试运行重置密码脚本
    try {
        Push-Location "$projectRoot\admin-backend"
        python reset_admin_user.py
        Pop-Location
        Start-Sleep -Seconds 2
        # 重试登录
        $loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method Post -Body $loginBody -ContentType "application/x-www-form-urlencoded" -TimeoutSec 10
        $token = $loginResponse.access_token
        Write-Host "   ✅ 登录成功（重置密码后）" -ForegroundColor Green
        Write-Host "   Token: $($token.Substring(0, 30))..." -ForegroundColor Gray
    } catch {
        Write-Host "   ❌ 登录失败: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# 确保token存在
if (-not $token) {
    Write-Host "   ❌ Token为空，无法继续测试" -ForegroundColor Red
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

Write-Host "   Token已设置到headers" -ForegroundColor Gray

# 3. 测试获取服务器列表
Write-Host "`n[3/8] 测试获取服务器列表..." -ForegroundColor Yellow
try {
    $servers = Invoke-RestMethod -Uri "$baseUrl/api/v1/group-ai/servers" -Headers $headers -TimeoutSec 10
    Write-Host "   ✅ 获取到 $($servers.Count) 个服务器" -ForegroundColor Green
    foreach ($server in $servers) {
        Write-Host "      - $($server.node_id): $($server.accounts_count)/$($server.max_accounts) 账号" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ 获取服务器列表失败: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. 测试扫描服务器账号
Write-Host "`n[4/8] 测试扫描服务器账号..." -ForegroundColor Yellow
if ($servers -and $servers.Count -gt 0) {
    $testServerId = $servers[0].node_id
    Write-Host "   测试服务器: $testServerId" -ForegroundColor Gray
    try {
        $accounts = Invoke-RestMethod -Uri "$baseUrl/api/v1/group-ai/account-management/scan-server-accounts?server_id=$testServerId" -Headers $headers -TimeoutSec 15
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
            }
        } else {
            Write-Host "   ⚠️  返回数据为空" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ❌ 扫描服务器账号失败: $($_.Exception.Message)" -ForegroundColor Red
        $errorResponse = $_.ErrorDetails.Message
        if ($errorResponse) {
            Write-Host "   错误详情: $errorResponse" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "   ⚠️  没有可用的服务器进行测试" -ForegroundColor Yellow
}

# 5. 测试获取剧本列表
Write-Host "`n[5/8] 测试获取剧本列表..." -ForegroundColor Yellow
try {
    $scripts = Invoke-RestMethod -Uri "$baseUrl/api/v1/group-ai/scripts" -Headers $headers -TimeoutSec 10
    Write-Host "   ✅ 获取到 $($scripts.items.Count) 个剧本" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 获取剧本列表失败: $($_.Exception.Message)" -ForegroundColor Red
}

# 6. 测试获取账号列表
Write-Host "`n[6/8] 测试获取账号列表..." -ForegroundColor Yellow
try {
    $accounts = Invoke-RestMethod -Uri "$baseUrl/api/v1/group-ai/accounts" -Headers $headers -TimeoutSec 10
    Write-Host "   ✅ 获取到 $($accounts.total) 个账号" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 获取账号列表失败: $($_.Exception.Message)" -ForegroundColor Red
}

# 7. 测试获取当前用户信息
Write-Host "`n[7/8] 测试获取当前用户信息..." -ForegroundColor Yellow
try {
    $user = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/me" -Headers $headers -TimeoutSec 10
    Write-Host "   ✅ 用户: $($user.email)" -ForegroundColor Green
    Write-Host "      角色: $($user.roles -join ', ')" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ 获取用户信息失败: $($_.Exception.Message)" -ForegroundColor Red
}

# 8. 检查后端日志中的扫描信息
Write-Host "`n[8/8] 检查后端日志..." -ForegroundColor Yellow
$backendJob = Get-Job | Where-Object {$_.Name -eq "BackendService" -and $_.State -eq "Running"} | Select-Object -First 1
if ($backendJob) {
    Write-Host "   正在获取后端日志..." -ForegroundColor Gray
    $logs = Receive-Job -Id $backendJob.Id -Keep
    $scanLogs = $logs | Where-Object {$_ -match "扫描服务器|scan.*account|找到.*账号|账号ID"}
    if ($scanLogs) {
        Write-Host "   ✅ 找到扫描相关日志:" -ForegroundColor Green
        $scanLogs | Select-Object -Last 10 | ForEach-Object {
            Write-Host "      $_" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ⚠️  未找到扫描相关日志" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️  未找到运行中的后端服务Job" -ForegroundColor Yellow
}

Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "✅ 测试完成" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

