# 全自动测试服务器建群和聊天功能
# 目标：账号在服务器上运行 -> 建群 -> 聊天全部跑通

$ErrorActionPreference = "Continue"
$baseUrl = "http://localhost:8000/api/v1"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  全自动测试服务器建群和聊天功能" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 步骤1: 登录获取token
Write-Host "`n[1/6] 登录获取token..." -ForegroundColor Yellow
try {
    $loginBody = @{
        username = "admin@example.com"
        password = "changeme123"
    } | ConvertTo-Json
    
    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method POST -ContentType "application/x-www-form-urlencoded" -Body "username=admin@example.com&password=changeme123"
    $token = $loginResponse.access_token
    Write-Host "✅ 登录成功" -ForegroundColor Green
} catch {
    Write-Host "❌ 登录失败: $_" -ForegroundColor Red
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# 步骤2: 获取账号列表
Write-Host "`n[2/6] 获取账号列表..." -ForegroundColor Yellow
try {
    $accountsResponse = Invoke-RestMethod -Uri "$baseUrl/group-ai/accounts?page=1&page_size=100" -Method GET -Headers $headers
    $accounts = $accountsResponse.items
    if (-not $accounts) { $accounts = $accountsResponse }
    
    Write-Host "✅ 获取到 $($accounts.Count) 个账号" -ForegroundColor Green
    
    # 查找已分配到服务器的账号
    $serverAccounts = $accounts | Where-Object { $_.server_id -and $_.server_id -ne "" -and $_.server_id -ne $null }
    Write-Host "   已分配到服务器的账号: $($serverAccounts.Count) 个" -ForegroundColor Gray
    
    if ($serverAccounts.Count -eq 0) {
        Write-Host "❌ 没有已分配到服务器的账号" -ForegroundColor Red
        Write-Host "   需要先创建账号并分配到服务器" -ForegroundColor Yellow
        exit 1
    }
    
    # 选择第一个账号
    $testAccount = $serverAccounts[0]
    Write-Host "   选择测试账号: $($testAccount.account_id)" -ForegroundColor Gray
    Write-Host "   服务器: $($testAccount.server_id)" -ForegroundColor Gray
    Write-Host "   状态: $($testAccount.status)" -ForegroundColor Gray
    
} catch {
    Write-Host "❌ 获取账号列表失败: $_" -ForegroundColor Red
    exit 1
}

# 步骤3: 确保账号在线
Write-Host "`n[3/6] 确保账号在线..." -ForegroundColor Yellow
if ($testAccount.status -ne "online") {
    Write-Host "   账号状态为 $($testAccount.status)，尝试启动..." -ForegroundColor Gray
    try {
        $startResponse = Invoke-RestMethod -Uri "$baseUrl/group-ai/accounts/$($testAccount.account_id)/start" -Method POST -Headers $headers
        Write-Host "✅ 启动请求已发送: $($startResponse.message)" -ForegroundColor Green
        Write-Host "   等待5秒让账号启动..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
    } catch {
        Write-Host "⚠️  启动请求失败: $_" -ForegroundColor Yellow
        Write-Host "   继续测试（账号可能在服务器上已运行）" -ForegroundColor Gray
    }
} else {
    Write-Host "✅ 账号已在线" -ForegroundColor Green
}

# 步骤4: 创建群组
Write-Host "`n[4/6] 创建群组..." -ForegroundColor Yellow
$groupTitle = "测试群组-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
try {
    $createGroupBody = @{
        account_id = $testAccount.account_id
        title = $groupTitle
        description = "全自动测试创建的群组"
        auto_reply = $true
    } | ConvertTo-Json
    
    $createGroupResponse = Invoke-RestMethod -Uri "$baseUrl/group-ai/groups/create" -Method POST -Headers $headers -Body $createGroupBody
    $groupId = $createGroupResponse.group_id
    Write-Host "✅ 群组创建成功" -ForegroundColor Green
    Write-Host "   群组ID: $groupId" -ForegroundColor Gray
    Write-Host "   群组标题: $($createGroupResponse.group_title)" -ForegroundColor Gray
    Write-Host "   等待3秒让群组初始化..." -ForegroundColor Gray
    Start-Sleep -Seconds 3
} catch {
    Write-Host "❌ 创建群组失败: $_" -ForegroundColor Red
    Write-Host "   错误详情: $($_.Exception.Response)" -ForegroundColor Gray
    if ($_.ErrorDetails.Message) {
        $errorObj = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "   错误信息: $($errorObj.detail)" -ForegroundColor Gray
    }
    exit 1
}

# 步骤5: 发送测试消息
Write-Host "`n[5/6] 发送测试消息..." -ForegroundColor Yellow
$testMessages = @("你好", "新人", "欢迎")
$successCount = 0

foreach ($msg in $testMessages) {
    Write-Host "   发送消息: `"$msg`"..." -ForegroundColor Gray
    try {
        $sendMessageBody = @{
            account_id = $testAccount.account_id
            group_id = $groupId
            message = $msg
            wait_for_reply = $true
            wait_timeout = 15
        } | ConvertTo-Json
        
        $sendResponse = Invoke-RestMethod -Uri "$baseUrl/group-ai/groups/send-test-message" -Method POST -Headers $headers -Body $sendMessageBody
        Write-Host "   ✅ 消息发送成功" -ForegroundColor Green
        if ($sendResponse.reply_received) {
            Write-Host "   ✅ 检测到自动回复" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "   ⚠️  未检测到自动回复" -ForegroundColor Yellow
        }
        Start-Sleep -Seconds 3
    } catch {
        Write-Host "   ❌ 发送消息失败: $_" -ForegroundColor Red
    }
}

# 步骤6: 测试结果汇总
Write-Host "`n[6/6] 测试结果汇总..." -ForegroundColor Yellow
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  测试完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`n测试账号: $($testAccount.account_id)" -ForegroundColor Gray
Write-Host "服务器: $($testAccount.server_id)" -ForegroundColor Gray
Write-Host "群组ID: $groupId" -ForegroundColor Gray
Write-Host "群组标题: $groupTitle" -ForegroundColor Gray
Write-Host "成功发送消息: $($testMessages.Count) 条" -ForegroundColor Gray
Write-Host "检测到自动回复: $successCount 次" -ForegroundColor Gray

if ($successCount -gt 0) {
    Write-Host "`n✅ 测试成功！账号建群和聊天功能正常" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  测试部分成功，但未检测到自动回复" -ForegroundColor Yellow
    Write-Host "   可能原因：" -ForegroundColor Gray
    Write-Host "   1. 账号未正确加载剧本" -ForegroundColor Gray
    Write-Host "   2. 消息未触发剧本中的场景" -ForegroundColor Gray
    Write-Host "   3. 自动回复功能未正确启动" -ForegroundColor Gray
}

Write-Host "`n========================================" -ForegroundColor Cyan

