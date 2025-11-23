# 测试按剧本聊天功能（完整版）
# 使用新的API端点发送测试消息并观察自动回复

$baseUrl = "http://localhost:8000/api/v1"
# 先获取可用账号和群组
$testAccountId = $null
$groupId = $null

# 先登录获取token
Write-Host "=== 登录获取Token ===" -ForegroundColor Cyan
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

Write-Host "`n=== 获取可用账号和群组 ===" -ForegroundColor Cyan

# 获取账号列表
try {
    $accountsResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts?page=1&page_size=100" `
        -Method GET `
        -Headers @{ "Authorization" = "Bearer $token" } `
        -UseBasicParsing
    
    $accounts = $accountsResponse.Content | ConvertFrom-Json
    
    # 查找在线且有群组的账号
    $onlineAccounts = $accounts | Where-Object { $_.status -eq "online" }
    $accountsWithGroups = $onlineAccounts | Where-Object { $_.group_count -gt 0 }
    
    if ($accountsWithGroups.Count -gt 0) {
        $testAccountId = $accountsWithGroups[0].account_id
        Write-Host "✅ 找到可用账号: $testAccountId (群组数: $($accountsWithGroups[0].group_count))" -ForegroundColor Green
        
        # 获取账号详情以获取群组ID
        $accountDetailResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts/$testAccountId" `
            -Method GET `
            -Headers @{ "Authorization" = "Bearer $token" } `
            -UseBasicParsing
        
        $accountDetail = $accountDetailResponse.Content | ConvertFrom-Json
        # 从账号配置中获取群组ID（需要从AccountManager获取）
        # 暂时使用第一个群组，或者需要创建新群组
        Write-Host "⚠️  需要获取群组ID，将尝试创建新群组..." -ForegroundColor Yellow
    } elseif ($onlineAccounts.Count -gt 0) {
        $testAccountId = $onlineAccounts[0].account_id
        Write-Host "✅ 找到在线账号: $testAccountId (但没有群组，将创建新群组)" -ForegroundColor Green
    } else {
        Write-Host "❌ 没有在线账号，无法进行测试" -ForegroundColor Red
        Write-Host "请先启动账号后再测试" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "获取账号列表失败: $_" -ForegroundColor Red
    exit 1
}

# 如果没有群组，创建一个
if (-not $groupId) {
    Write-Host "`n=== 创建测试群组 ===" -ForegroundColor Cyan
    $groupTitle = "测试群组-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    $createGroupBody = @{
        account_id = $testAccountId
        title = $groupTitle
        description = "用于测试按剧本聊天功能的测试群组"
        auto_reply = $true
    } | ConvertTo-Json
    
    try {
        $createResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/groups/create" `
            -Method POST `
            -ContentType "application/json" `
            -Headers @{ "Authorization" = "Bearer $token" } `
            -Body $createGroupBody `
            -UseBasicParsing
        
        $groupData = $createResponse.Content | ConvertFrom-Json
        $groupId = $groupData.group_id
        Write-Host "✅ 群组创建成功: $($groupData.group_title) (ID: $groupId)" -ForegroundColor Green
        Start-Sleep -Seconds 2  # 等待群组创建完成
    } catch {
        Write-Host "❌ 创建群组失败: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n=== 测试按剧本聊天功能 ===" -ForegroundColor Cyan
Write-Host "账号ID: $testAccountId" -ForegroundColor Yellow
Write-Host "群组ID: $groupId" -ForegroundColor Yellow

# 检查账号状态
Write-Host "`n检查账号状态..." -ForegroundColor Yellow
try {
    $accountResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts/$testAccountId" `
        -Method GET `
        -Headers @{ "Authorization" = "Bearer $token" } `
        -UseBasicParsing
    
    $accountData = $accountResponse.Content | ConvertFrom-Json
    Write-Host "  账号状态: $($accountData.status)" -ForegroundColor Gray
    Write-Host "  群组数: $($accountData.group_count)" -ForegroundColor Gray
    Write-Host "  消息数: $($accountData.message_count)" -ForegroundColor Gray
    Write-Host "  回复数: $($accountData.reply_count)" -ForegroundColor Gray
    Write-Host "  剧本ID: $($accountData.script_id)" -ForegroundColor Gray
    
    if ($accountData.status -ne "online") {
        Write-Host "`n⚠️  警告: 账号状态不是online，可能无法正常回复消息" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "  获取账号状态失败: $_" -ForegroundColor Red
    exit 1
}

# 测试消息列表（根据000新人欢迎剧本）
$testMessages = @(
    "你好",
    "新人",
    "欢迎"
)

Write-Host "`n=== 发送测试消息并观察自动回复 ===" -ForegroundColor Cyan

foreach ($testMessage in $testMessages) {
    Write-Host "`n--- 测试消息: '$testMessage' ---" -ForegroundColor Yellow
    
    # 获取发送前的回复数
    $accountResponseBefore = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts/$testAccountId" `
        -Method GET `
        -Headers @{ "Authorization" = "Bearer $token" } `
        -UseBasicParsing
    $accountDataBefore = $accountResponseBefore.Content | ConvertFrom-Json
    $replyCountBefore = $accountDataBefore.reply_count
    
    Write-Host "  发送前回复数: $replyCountBefore" -ForegroundColor Gray
    
    # 发送测试消息
    $sendMessageBody = @{
        account_id = $testAccountId
        group_id = $groupId
        message = $testMessage
        wait_for_reply = $true
        wait_timeout = 10
    } | ConvertTo-Json
    
    try {
        Write-Host "  正在发送测试消息..." -ForegroundColor Yellow
        
        $sendResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/groups/send-test-message" `
            -Method POST `
            -ContentType "application/json" `
            -Headers @{ "Authorization" = "Bearer $token" } `
            -Body $sendMessageBody `
            -UseBasicParsing
        
        $sendData = $sendResponse.Content | ConvertFrom-Json
        
        Write-Host "  ✅ 测试消息已发送" -ForegroundColor Green
        Write-Host "    消息ID: $($sendData.message_id)" -ForegroundColor Gray
        Write-Host "    发送前回复数: $($sendData.reply_count_before)" -ForegroundColor Gray
        Write-Host "    发送后回复数: $($sendData.reply_count_after)" -ForegroundColor Gray
        
        if ($sendData.reply_received) {
            Write-Host "    ✅ 检测到自动回复！" -ForegroundColor Green
            Write-Host "    回复数增加了: $($sendData.reply_count_after - $sendData.reply_count_before)" -ForegroundColor Gray
        } else {
            Write-Host "    ⏸️  未检测到自动回复" -ForegroundColor Yellow
            Write-Host "    可能原因:" -ForegroundColor Yellow
            Write-Host "      - 剧本触发条件未匹配" -ForegroundColor Gray
            Write-Host "      - 回复率设置导致跳过回复" -ForegroundColor Gray
            Write-Host "      - 回复间隔限制" -ForegroundColor Gray
        }
        
        # 等待一段时间，然后再次检查
        Write-Host "  等待5秒后再次检查..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        $accountResponseAfter = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts/$testAccountId" `
            -Method GET `
            -Headers @{ "Authorization" = "Bearer $token" } `
            -UseBasicParsing
        $accountDataAfter = $accountResponseAfter.Content | ConvertFrom-Json
        
        Write-Host "  最终回复数: $($accountDataAfter.reply_count)" -ForegroundColor Gray
        if ($accountDataAfter.reply_count -gt $replyCountBefore) {
            Write-Host "  ✅ 确认：回复数已增加！" -ForegroundColor Green
        }
        
    } catch {
        $errorMessage = $_.Exception.Message
        if ($_.Exception.Response) {
            try {
                $responseBody = $_.Exception.Response.Content.ReadAsStringAsync().Result
                try {
                    $errorData = $responseBody | ConvertFrom-Json
                    $errorMessage = $errorData.detail
                } catch {
                    $errorMessage = $responseBody
                }
            } catch {
                $errorMessage = $_.Exception.Message
            }
        }
        
        Write-Host "  ❌ 发送测试消息失败: $errorMessage" -ForegroundColor Red
    }
    
    # 等待一段时间再发送下一条消息
    if ($testMessage -ne $testMessages[-1]) {
        Write-Host "  等待3秒后发送下一条消息..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}

Write-Host "`n=== 测试完成 ===" -ForegroundColor Cyan
Write-Host "`n测试说明：" -ForegroundColor Yellow
Write-Host "1. 如果检测到自动回复，说明按剧本聊天功能正常工作" -ForegroundColor Gray
Write-Host "2. 如果未检测到回复，可能原因：" -ForegroundColor Gray
Write-Host "   - 剧本触发条件未匹配（检查剧本配置）" -ForegroundColor Gray
Write-Host "   - 回复率设置导致跳过回复（检查账号配置）" -ForegroundColor Gray
Write-Host "   - 回复间隔限制（检查账号配置）" -ForegroundColor Gray
Write-Host "3. 可以在Telegram客户端中查看群组，确认回复内容是否符合剧本设定" -ForegroundColor Gray

