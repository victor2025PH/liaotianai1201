# 测试创建群组脚本
# 使用可用账号测试创建群组功能

$baseUrl = "http://localhost:8000/api/v1"
$testAccountId = "639457597211"  # 使用第一个可用账号

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

# 测试创建群组
Write-Host "`n=== 测试创建群组 ===" -ForegroundColor Cyan
Write-Host "使用账号: $testAccountId" -ForegroundColor Yellow

$groupTitle = "测试群组-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$createGroupBody = @{
    account_id = $testAccountId
    title = $groupTitle
    description = "这是一个测试群组，用于测试自动建群和按剧本聊天功能"
    auto_reply = $true
} | ConvertTo-Json

try {
    Write-Host "正在创建群组: $groupTitle" -ForegroundColor Yellow
    
    $createResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/groups/create" `
        -Method POST `
        -ContentType "application/json" `
        -Headers @{ "Authorization" = "Bearer $token" } `
        -Body $createGroupBody `
        -UseBasicParsing
    
    $groupData = $createResponse.Content | ConvertFrom-Json
    
    Write-Host "`n✅ 群组创建成功！" -ForegroundColor Green
    Write-Host "  账号ID: $($groupData.account_id)" -ForegroundColor Gray
    Write-Host "  群组ID: $($groupData.group_id)" -ForegroundColor Gray
    Write-Host "  群组标题: $($groupData.group_title)" -ForegroundColor Gray
    Write-Host "  消息: $($groupData.message)" -ForegroundColor Gray
    
    # 保存群组信息
    $groupInfo = [PSCustomObject]@{
        AccountId = $groupData.account_id
        GroupId = $groupData.group_id
        GroupTitle = $groupData.group_title
        CreatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Status = "Success"
    }
    
    $groupInfo | Export-Csv -Path "群组创建测试结果.csv" -NoTypeInformation -Encoding UTF8
    Write-Host "`n群组信息已保存到: 群组创建测试结果.csv" -ForegroundColor Green
    
    # 等待几秒，然后检查账号状态
    Write-Host "`n等待5秒后检查账号状态..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    $accountResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts/$testAccountId" `
        -Method GET `
        -Headers @{ "Authorization" = "Bearer $token" } `
        -UseBasicParsing
    
    $accountData = $accountResponse.Content | ConvertFrom-Json
    Write-Host "`n账号状态更新:" -ForegroundColor Cyan
    Write-Host "  账号ID: $($accountData.account_id)" -ForegroundColor Gray
    Write-Host "  状态: $($accountData.status)" -ForegroundColor Gray
    Write-Host "  群组数: $($accountData.group_count)" -ForegroundColor Gray
    Write-Host "  消息数: $($accountData.message_count)" -ForegroundColor Gray
    Write-Host "  回复数: $($accountData.reply_count)" -ForegroundColor Gray
    
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
    
    Write-Host "`n❌ 创建群组失败: $errorMessage" -ForegroundColor Red
    
    $errorInfo = [PSCustomObject]@{
        AccountId = $testAccountId
        GroupTitle = $groupTitle
        CreatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Status = "Failed"
        Error = $errorMessage
    }
    
    $errorInfo | Export-Csv -Path "群组创建测试结果.csv" -NoTypeInformation -Encoding UTF8
}

Write-Host "`n=== 测试完成 ===" -ForegroundColor Cyan

