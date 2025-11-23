# 测试按剧本聊天功能（替代方案）
# 使用现有API和直接方法测试

$baseUrl = "http://localhost:8000/api/v1"

Write-Host "=== 测试按剧本聊天功能（替代方案） ===" -ForegroundColor Cyan

# 1. 登录
Write-Host "`n1. 登录获取Token..." -ForegroundColor Yellow
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

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# 2. 获取账号列表（使用不同的API路径）
Write-Host "`n2. 获取账号列表..." -ForegroundColor Yellow
try {
    # 尝试不同的API路径
    $accountsUrl = "$baseUrl/group-ai/accounts?page=1&page_size=100"
    $accountsResponse = Invoke-WebRequest -Uri $accountsUrl `
        -Method GET `
        -Headers $headers `
        -UseBasicParsing
    
    $accounts = $accountsResponse.Content | ConvertFrom-Json
    
    # 如果返回的是对象而不是数组，尝试获取items属性
    if ($accounts.PSObject.Properties.Name -contains "items") {
        $accounts = $accounts.items
    }
    
    Write-Host "   ✅ 获取到 $($accounts.Count) 个账号" -ForegroundColor Green
    
    # 查找在线账号
    $onlineAccounts = $accounts | Where-Object { $_.status -eq "online" }
    Write-Host "   在线账号数: $($onlineAccounts.Count)" -ForegroundColor Gray
    
    if ($onlineAccounts.Count -eq 0) {
        Write-Host "   ⚠️  没有在线账号，无法进行测试" -ForegroundColor Yellow
        Write-Host "   请先启动账号" -ForegroundColor Yellow
        exit 1
    }
    
    $testAccount = $onlineAccounts[0]
    $testAccountId = $testAccount.account_id
    Write-Host "   使用账号: $testAccountId" -ForegroundColor Cyan
    
} catch {
    Write-Host "   ❌ 获取账号列表失败: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "   状态码: $statusCode" -ForegroundColor Gray
    }
    exit 1
}

# 3. 检查或创建群组
Write-Host "`n3. 检查群组..." -ForegroundColor Yellow
$groupId = $null

if ($testAccount.group_count -gt 0) {
    Write-Host "   账号已有 $($testAccount.group_count) 个群组" -ForegroundColor Gray
    Write-Host "   ⚠️  需要群组ID才能发送消息" -ForegroundColor Yellow
    Write-Host "   建议：在浏览器中查看账号详情获取群组ID" -ForegroundColor Yellow
} else {
    Write-Host "   账号没有群组，尝试创建..." -ForegroundColor Yellow
    $groupTitle = "测试群组-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    $createGroupBody = @{
        account_id = $testAccountId
        title = $groupTitle
        description = "用于测试按剧本聊天功能"
        auto_reply = $true
    } | ConvertTo-Json
    
    try {
        $createResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/groups/create" `
            -Method POST `
            -Headers $headers `
            -Body $createGroupBody `
            -UseBasicParsing
        
        $groupData = $createResponse.Content | ConvertFrom-Json
        $groupId = $groupData.group_id
        Write-Host "   ✅ 群组创建成功: $($groupData.group_title) (ID: $groupId)" -ForegroundColor Green
        Start-Sleep -Seconds 2
    } catch {
        Write-Host "   ❌ 创建群组失败: $_" -ForegroundColor Red
        Write-Host "   状态码: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Gray
    }
}

# 4. 测试发送消息（如果新API端点可用）
if ($groupId) {
    Write-Host "`n4. 测试发送消息..." -ForegroundColor Yellow
    
    # 先尝试新的API端点
    $sendMessageBody = @{
        account_id = $testAccountId
        group_id = $groupId
        message = "你好"
        wait_for_reply = $true
        wait_timeout = 10
    } | ConvertTo-Json
    
    try {
        Write-Host "   尝试使用新的API端点发送消息..." -ForegroundColor Gray
        $sendResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/groups/send-test-message" `
            -Method POST `
            -Headers $headers `
            -Body $sendMessageBody `
            -UseBasicParsing `
            -ErrorAction Stop
        
        $sendData = $sendResponse.Content | ConvertFrom-Json
        Write-Host "   ✅ 消息发送成功！" -ForegroundColor Green
        Write-Host "   消息ID: $($sendData.message_id)" -ForegroundColor Gray
        
        if ($sendData.reply_received) {
            Write-Host "   ✅ 检测到自动回复！" -ForegroundColor Green
            Write-Host "   回复数: $($sendData.reply_count_before) → $($sendData.reply_count_after)" -ForegroundColor Gray
        } else {
            Write-Host "   ⏸️  未检测到自动回复" -ForegroundColor Yellow
            Write-Host "   可能原因：剧本触发条件未匹配、回复率设置等" -ForegroundColor Gray
        }
        
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq 404) {
            Write-Host "   ⚠️  新的API端点未加载（404）" -ForegroundColor Yellow
            Write-Host "   需要重启后端服务以加载新API端点" -ForegroundColor Yellow
            Write-Host "`n   替代方案：" -ForegroundColor Cyan
            Write-Host "   1. 在Telegram客户端中手动发送消息到群组" -ForegroundColor Gray
            Write-Host "   2. 观察账号是否按照剧本自动回复" -ForegroundColor Gray
            Write-Host "   3. 群组ID: $groupId" -ForegroundColor Gray
        } else {
            Write-Host "   ❌ 发送消息失败: $_" -ForegroundColor Red
            Write-Host "   状态码: $statusCode" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "`n⚠️  无法继续测试：没有群组ID" -ForegroundColor Yellow
    Write-Host "   建议：" -ForegroundColor Cyan
    Write-Host "   1. 在浏览器中创建群组" -ForegroundColor Gray
    Write-Host "   2. 获取群组ID" -ForegroundColor Gray
    Write-Host "   3. 手动在Telegram客户端中发送消息测试" -ForegroundColor Gray
}

Write-Host "`n=== 测试完成 ===" -ForegroundColor Cyan

