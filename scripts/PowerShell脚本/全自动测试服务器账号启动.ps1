# 全自动测试服务器账号启动功能
# 修复了API认证问题

$ErrorActionPreference = "Continue"
$baseUrl = "http://localhost:8000/api/v1"

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  全自动测试服务器账号启动功能" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. 登录获取Token
Write-Host "1. 登录获取Token..." -ForegroundColor Yellow
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
    Write-Host "   ✅ 登录成功" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 登录失败: $_" -ForegroundColor Red
    exit 1
}

# 创建headers（确保格式正确）
$headers = @{}
$headers.Add("Authorization", "Bearer $token")
$headers.Add("Content-Type", "application/json")

# 2. 获取账号列表
Write-Host "`n2. 获取账号列表..." -ForegroundColor Yellow
try {
    $accountsResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts?page=1&page_size=100" `
        -Method GET `
        -Headers $headers `
        -UseBasicParsing `
        -ErrorAction Stop
    
    $accountsData = $accountsResponse.Content | ConvertFrom-Json
    $accounts = $accountsData.items
    
    if (-not $accounts) {
        Write-Host "   ⚠️  未获取到账号数据，尝试直接使用accountsData" -ForegroundColor Yellow
        $accounts = $accountsData
    }
    
    Write-Host "   ✅ 获取到 $($accounts.Count) 个账号" -ForegroundColor Green
    
    # 查找已分配到服务器的账号
    $serverAccounts = $accounts | Where-Object { 
        $_.server_id -and $_.server_id -ne "" -and $_.server_id -ne $null 
    }
    
    Write-Host "`n   已分配到服务器的账号: $($serverAccounts.Count) 个" -ForegroundColor Cyan
    
    if ($serverAccounts.Count -eq 0) {
        Write-Host "   ⚠️  没有已分配到服务器的账号" -ForegroundColor Yellow
        Write-Host "`n   显示所有账号信息：" -ForegroundColor Yellow
        foreach ($acc in $accounts | Select-Object -First 5) {
            $serverInfo = if ($acc.server_id) { $acc.server_id } else { "未分配" }
            Write-Host "     - $($acc.account_id): 状态=$($acc.status), 服务器=$serverInfo" -ForegroundColor Gray
        }
        Write-Host "`n   建议：使用前端界面批量创建账号，系统会自动分配服务器" -ForegroundColor Yellow
        exit 0
    }
    
    # 显示已分配的账号
    Write-Host "`n   已分配的账号列表：" -ForegroundColor Gray
    foreach ($acc in $serverAccounts) {
        Write-Host "     - $($acc.account_id): 服务器=$($acc.server_id), 状态=$($acc.status)" -ForegroundColor Gray
    }
    
    # 选择第一个账号进行测试
    $testAccount = $serverAccounts[0]
    Write-Host "`n   选择测试账号: $($testAccount.account_id)" -ForegroundColor Cyan
    Write-Host "   服务器ID: $($testAccount.server_id)" -ForegroundColor Cyan
    Write-Host "   当前状态: $($testAccount.status)" -ForegroundColor Cyan
    
} catch {
    Write-Host "   ❌ 获取账号列表失败: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "   状态码: $statusCode" -ForegroundColor Gray
        try {
            $errorContent = $_.Exception.Response.Content | ConvertFrom-Json
            Write-Host "   错误详情: $($errorContent.detail)" -ForegroundColor Gray
        } catch {
            Write-Host "   错误内容: $($_.Exception.Response.Content)" -ForegroundColor Gray
        }
    }
    exit 1
}

# 3. 测试启动账号（应该在服务器上启动）
Write-Host "`n3. 测试启动账号（应该在服务器上启动）..." -ForegroundColor Yellow
Write-Host "   账号ID: $($testAccount.account_id)" -ForegroundColor Gray
Write-Host "   服务器ID: $($testAccount.server_id)" -ForegroundColor Gray
Write-Host "   当前状态: $($testAccount.status)" -ForegroundColor Gray

try {
    Write-Host "`n   发送启动请求..." -ForegroundColor Gray
    $startResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts/$($testAccount.account_id)/start" `
        -Method POST `
        -Headers $headers `
        -UseBasicParsing `
        -ErrorAction Stop
    
    $startResult = $startResponse.Content | ConvertFrom-Json
    Write-Host "   ✅ 启动请求成功" -ForegroundColor Green
    Write-Host "     消息: $($startResult.message)" -ForegroundColor Gray
    
    if ($startResult.server_id) {
        Write-Host "   ✅ 账号在服务器 $($startResult.server_id) 上启动" -ForegroundColor Green
    } elseif ($startResult.PSObject.Properties.Name -contains "server_id") {
        Write-Host "   ⚠️  账号在本地启动（未指定服务器）" -ForegroundColor Yellow
    } else {
        Write-Host "   ℹ️  启动结果: $($startResult | ConvertTo-Json -Depth 2)" -ForegroundColor Gray
    }
    
    # 等待几秒让账号启动
    Write-Host "`n   等待5秒让账号启动..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
    
    # 检查账号状态
    Write-Host "`n   检查账号状态..." -ForegroundColor Gray
    $accountResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts/$($testAccount.account_id)" `
        -Method GET `
        -Headers $headers `
        -UseBasicParsing `
        -ErrorAction Stop
    
    $account = $accountResponse.Content | ConvertFrom-Json
    Write-Host "   账号状态: $($account.status)" -ForegroundColor Gray
    Write-Host "   服务器ID: $($account.server_id)" -ForegroundColor Gray
    
    if ($account.status -eq "online") {
        Write-Host "   ✅ 账号启动成功并在线" -ForegroundColor Green
    } elseif ($account.status -eq "error") {
        Write-Host "   ❌ 账号启动失败（状态: error）" -ForegroundColor Red
        Write-Host "   可能原因：" -ForegroundColor Yellow
        Write-Host "     - Telegram连接失败" -ForegroundColor Gray
        Write-Host "     - Session文件无效或已过期" -ForegroundColor Gray
        Write-Host "     - 服务器上的启动命令执行失败" -ForegroundColor Gray
    } else {
        Write-Host "   ⚠️  账号状态: $($account.status)" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "   ❌ 启动账号失败: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        try {
            $errorContent = $_.Exception.Response.Content | ConvertFrom-Json
            Write-Host "     错误详情: $($errorContent.detail)" -ForegroundColor Red
        } catch {
            $errorText = $_.Exception.Response.Content
            Write-Host "     错误内容: $errorText" -ForegroundColor Red
        }
    }
}

# 4. 测试结果汇总
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  测试结果汇总" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "测试账号: $($testAccount.account_id)" -ForegroundColor Yellow
Write-Host "服务器分配: $($account.server_id)" -ForegroundColor Yellow
Write-Host "账号状态: $($account.status)" -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ 测试完成" -ForegroundColor Green

