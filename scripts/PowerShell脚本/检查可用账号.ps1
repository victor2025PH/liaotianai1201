# 检查可用账号
$baseUrl = "http://localhost:8000/api/v1"

# 登录
$loginBody = @{
    username = "admin@example.com"
    password = "changeme123"
}

try {
    $loginResponse = Invoke-WebRequest -Uri "$baseUrl/auth/login" `
        -Method POST `
        -ContentType "application/x-www-form-urlencoded" `
        -Body $loginBody `
        -UseBasicParsing
    
    $loginData = $loginResponse.Content | ConvertFrom-Json
    $token = $loginData.access_token
    Write-Host "登录成功" -ForegroundColor Green
} catch {
    Write-Host "登录失败: $_" -ForegroundColor Red
    exit 1
}

# 获取账号列表
try {
    $accountsResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts" `
        -Method GET `
        -Headers @{ "Authorization" = "Bearer $token" } `
        -UseBasicParsing
    
    $accounts = $accountsResponse.Content | ConvertFrom-Json
    
    Write-Host "`n=== 可用账号列表 ===" -ForegroundColor Cyan
    Write-Host "总账号数: $($accounts.Count)" -ForegroundColor Yellow
    
    $onlineAccounts = $accounts | Where-Object { $_.status -eq "online" }
    Write-Host "`n在线账号 (可用于测试):" -ForegroundColor Green
    foreach ($account in $onlineAccounts) {
        Write-Host "  - $($account.account_id) (状态: $($account.status), 群组数: $($account.group_count))" -ForegroundColor Gray
    }
    
    if ($onlineAccounts.Count -eq 0) {
        Write-Host "`n⚠️  没有在线账号，需要先启动账号" -ForegroundColor Yellow
    } else {
        Write-Host "`n推荐使用账号: $($onlineAccounts[0].account_id)" -ForegroundColor Cyan
    }
    
    # 检查有群组的账号
    $accountsWithGroups = $accounts | Where-Object { $_.group_count -gt 0 }
    if ($accountsWithGroups.Count -gt 0) {
        Write-Host "`n有群组的账号:" -ForegroundColor Green
        foreach ($account in $accountsWithGroups) {
            Write-Host "  - $($account.account_id) (群组数: $($account.group_count))" -ForegroundColor Gray
        }
    }
    
} catch {
    Write-Host "获取账号列表失败: $_" -ForegroundColor Red
    try {
        $errorResponse = $_.Exception.Response
        if ($errorResponse) {
            $stream = $errorResponse.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $errorContent = $reader.ReadToEnd()
            Write-Host "错误详情: $errorContent" -ForegroundColor Red
        }
    } catch {
        Write-Host "无法读取错误详情" -ForegroundColor Yellow
    }
}

