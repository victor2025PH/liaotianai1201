# 测试按剧本聊天功能
# 在已创建的群组中测试账号是否按照剧本进行回复

$baseUrl = "http://localhost:8000/api/v1"
$testAccountId = "639457597211"
$groupId = -5044873791  # 从群组创建测试结果中获取

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
    }
} catch {
    Write-Host "  获取账号状态失败: $_" -ForegroundColor Red
}

# 测试消息（根据000新人欢迎剧本，应该触发欢迎消息）
Write-Host "`n=== 测试剧本触发 ===" -ForegroundColor Cyan
Write-Host "根据'000新人欢迎剧本'，当有新成员加入或发送特定消息时，应该触发欢迎回复" -ForegroundColor Yellow
Write-Host "`n注意：由于无法直接通过API发送Telegram消息，需要："
Write-Host "1. 在Telegram客户端中手动发送消息到群组"
Write-Host "2. 或者使用另一个账号发送消息"
Write-Host "3. 然后观察账号是否按照剧本自动回复"
Write-Host "`n建议测试消息："
Write-Host "  - '你好'"
Write-Host "  - '新人'"
Write-Host "  - '欢迎'"
Write-Host "  - 或者直接加入新成员（如果剧本支持新成员触发）"

# 等待一段时间，然后检查消息和回复数
Write-Host "`n等待10秒后检查消息和回复数..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

try {
    $accountResponse2 = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts/$testAccountId" `
        -Method GET `
        -Headers @{ "Authorization" = "Bearer $token" } `
        -UseBasicParsing
    
    $accountData2 = $accountResponse2.Content | ConvertFrom-Json
    Write-Host "`n账号状态更新:" -ForegroundColor Cyan
    Write-Host "  消息数: $($accountData2.message_count) (之前: $($accountData.message_count))" -ForegroundColor Gray
    Write-Host "  回复数: $($accountData2.reply_count) (之前: $($accountData.reply_count))" -ForegroundColor Gray
    
    if ($accountData2.reply_count -gt $accountData.reply_count) {
        Write-Host "`n✅ 检测到账号已自动回复消息！" -ForegroundColor Green
        Write-Host "  回复数增加了 $($accountData2.reply_count - $accountData.reply_count) 条" -ForegroundColor Gray
    } else {
        Write-Host "`n⏸️  暂未检测到自动回复（可能需要手动发送消息到群组）" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  检查失败: $_" -ForegroundColor Red
}

Write-Host "`n=== 测试说明 ===" -ForegroundColor Cyan
Write-Host "由于Telegram API的限制，无法直接通过API发送消息到群组。"
Write-Host "要完整测试按剧本聊天功能，需要："
Write-Host "1. 在Telegram客户端中打开群组: $groupId"
Write-Host "2. 发送测试消息（如：'你好'、'新人'等）"
Write-Host "3. 观察账号是否按照剧本自动回复"
Write-Host "4. 检查回复内容是否符合剧本设定"

Write-Host "`n=== 测试完成 ===" -ForegroundColor Cyan

