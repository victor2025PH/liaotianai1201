# 建群聊天功能测试脚本
# 测试账号自动建群和按剧本聊天功能

$baseUrl = "http://localhost:8000"
$apiBase = "$baseUrl/api/v1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "建群聊天功能测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查后端服务状态
Write-Host "[1/6] 检查后端服务状态..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get -ErrorAction Stop
    Write-Host "✅ 后端服务运行正常" -ForegroundColor Green
    Write-Host "   状态: $($healthResponse.status)" -ForegroundColor Gray
} catch {
    Write-Host "❌ 后端服务未运行或无法访问" -ForegroundColor Red
    Write-Host "   错误: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. 获取可用账号列表
Write-Host "[2/6] 获取可用账号列表..." -ForegroundColor Yellow
try {
    $accountsResponse = Invoke-RestMethod -Uri "$apiBase/group-ai/accounts" -Method Get -ErrorAction Stop
    $accounts = $accountsResponse.items
    
    if ($accounts.Count -eq 0) {
        Write-Host "❌ 没有可用的账号" -ForegroundColor Red
        exit 1
    }
    
    # 查找在线账号
    $onlineAccounts = $accounts | Where-Object { $_.status -eq "ONLINE" }
    
    if ($onlineAccounts.Count -eq 0) {
        Write-Host "⚠️  没有在线账号，尝试使用第一个账号..." -ForegroundColor Yellow
        $testAccount = $accounts[0]
    } else {
        $testAccount = $onlineAccounts[0]
    }
    
    Write-Host "✅ 找到测试账号:" -ForegroundColor Green
    Write-Host "   账号ID: $($testAccount.account_id)" -ForegroundColor Gray
    Write-Host "   状态: $($testAccount.status)" -ForegroundColor Gray
    Write-Host "   剧本ID: $($testAccount.script_id)" -ForegroundColor Gray
    
    $accountId = $testAccount.account_id
} catch {
    Write-Host "❌ 获取账号列表失败" -ForegroundColor Red
    Write-Host "   错误: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 3. 确保账号在线
Write-Host "[3/6] 确保账号在线..." -ForegroundColor Yellow
if ($testAccount.status -ne "ONLINE") {
    try {
        Write-Host "   尝试启动账号 $accountId..." -ForegroundColor Gray
        $startResponse = Invoke-RestMethod -Uri "$apiBase/group-ai/accounts/$accountId/start" -Method Post -ErrorAction Stop
        Write-Host "✅ 账号启动请求已发送" -ForegroundColor Green
        Write-Host "   等待账号启动..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
        
        # 检查账号状态
        $accountCheck = Invoke-RestMethod -Uri "$apiBase/group-ai/accounts/$accountId" -Method Get -ErrorAction Stop
        if ($accountCheck.status -eq "ONLINE") {
            Write-Host "✅ 账号已在线" -ForegroundColor Green
        } else {
            Write-Host "⚠️  账号状态: $($accountCheck.status)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  启动账号失败，继续测试..." -ForegroundColor Yellow
        Write-Host "   错误: $($_.Exception.Message)" -ForegroundColor Gray
    }
} else {
    Write-Host "✅ 账号已在线" -ForegroundColor Green
}
Write-Host ""

# 4. 创建测试群组
Write-Host "[4/6] 创建测试群组..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$groupTitle = "测试群组-$timestamp"
$groupId = $null

$createGroupData = @{
    account_id = $accountId
    title = $groupTitle
    description = "自动化测试创建的群组"
    auto_reply = $true
} | ConvertTo-Json

try {
    $createResponse = Invoke-RestMethod -Uri "$apiBase/group-ai/groups/create" -Method Post -Body $createGroupData -ContentType "application/json" -ErrorAction Stop
    
    if ($createResponse.success) {
        $groupId = $createResponse.group_id
        Write-Host "✅ 群组创建成功!" -ForegroundColor Green
        Write-Host "   群组ID: $groupId" -ForegroundColor Gray
        Write-Host "   群组标题: $($createResponse.group_title)" -ForegroundColor Gray
        Write-Host "   消息: $($createResponse.message)" -ForegroundColor Gray
    } else {
        Write-Host "❌ 群组创建失败" -ForegroundColor Red
        Write-Host "   消息: $($createResponse.message)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ 创建群组失败" -ForegroundColor Red
    Write-Host "   错误: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "   响应: $responseBody" -ForegroundColor Red
        } catch {
            # 忽略读取响应流的错误
        }
    }
    exit 1
}
Write-Host ""

# 5. 发送测试消息（如果群组创建成功）
if ($groupId) {
    Write-Host "[5/6] 发送测试消息..." -ForegroundColor Yellow
    $testMessages = @("你好", "新人", "欢迎")
    
    foreach ($testMessage in $testMessages) {
        Write-Host "   发送消息: '$testMessage'..." -ForegroundColor Gray
        
        $sendMessageData = @{
            account_id = $accountId
            group_id = $groupId
            message = $testMessage
            wait_for_reply = $true
            wait_timeout = 15
        } | ConvertTo-Json
        
        try {
            $sendResponse = Invoke-RestMethod -Uri "$apiBase/group-ai/groups/send-test-message" -Method Post -Body $sendMessageData -ContentType "application/json" -ErrorAction Stop
            
            if ($sendResponse.success) {
                Write-Host "   ✅ 消息发送成功" -ForegroundColor Green
                if ($sendResponse.reply_received) {
                    Write-Host "   ✅ 收到自动回复" -ForegroundColor Green
                    Write-Host "      回复前消息数: $($sendResponse.reply_count_before)" -ForegroundColor Gray
                    Write-Host "      回复后消息数: $($sendResponse.reply_count_after)" -ForegroundColor Gray
                } else {
                    Write-Host "   ⚠️  未收到自动回复（可能正常，取决于剧本配置）" -ForegroundColor Yellow
                }
            } else {
                Write-Host "   ⚠️  消息发送失败: $($sendResponse.message)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "   ⚠️  发送消息失败: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        
        # 等待一段时间再发送下一条消息
        Start-Sleep -Seconds 3
    }
    Write-Host ""
}

# 6. 检查账号状态更新
Write-Host "[6/6] 检查账号状态更新..." -ForegroundColor Yellow
try {
    $accountStatus = Invoke-RestMethod -Uri "$apiBase/group-ai/accounts/$accountId" -Method Get -ErrorAction Stop
    Write-Host "✅ 账号状态:" -ForegroundColor Green
    Write-Host "   群组数: $($accountStatus.group_count)" -ForegroundColor Gray
    Write-Host "   消息数: $($accountStatus.message_count)" -ForegroundColor Gray
    Write-Host "   回复数: $($accountStatus.reply_count)" -ForegroundColor Gray
} catch {
    Write-Host "⚠️  获取账号状态失败" -ForegroundColor Yellow
    Write-Host "   错误: $($_.Exception.Message)" -ForegroundColor Gray
}
Write-Host ""

# 测试总结
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试总结" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
if ($groupId) {
    Write-Host "✅ 群组创建: 成功" -ForegroundColor Green
    Write-Host "   群组ID: $groupId" -ForegroundColor Gray
    Write-Host "   群组标题: $groupTitle" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📝 下一步操作:" -ForegroundColor Yellow
    Write-Host "   1. 在Telegram客户端中打开群组: $groupTitle" -ForegroundColor Gray
    Write-Host "   2. 发送测试消息验证自动回复功能" -ForegroundColor Gray
    Write-Host "   3. 观察账号是否按照剧本自动回复" -ForegroundColor Gray
} else {
    Write-Host "❌ 群组创建失败" -ForegroundColor Red
}
Write-Host ""
Write-Host "测试完成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
