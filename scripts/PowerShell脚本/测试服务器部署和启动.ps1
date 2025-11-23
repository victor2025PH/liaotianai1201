# 测试服务器部署和启动功能
# 测试账号创建、服务器分配、服务器启动的完整流程

$ErrorActionPreference = "Continue"
$baseUrl = "http://localhost:8000/api/v1"

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  测试服务器部署和启动功能" -ForegroundColor Cyan
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

# 创建headers字典（确保正确格式）
$headers = @{}
$headers["Authorization"] = "Bearer $token"
$headers["Content-Type"] = "application/json"

# 2. 检查服务器列表（可选，如果API不可用则跳过）
Write-Host "`n2. 检查服务器列表（可选）..." -ForegroundColor Yellow
$serversAvailable = $false
try {
    $serversUrl = "$baseUrl/group-ai/servers"
    $serversResponse = Invoke-WebRequest -Uri $serversUrl `
        -Method GET `
        -Headers $headers `
        -UseBasicParsing `
        -ErrorAction Stop
    
    $servers = $serversResponse.Content | ConvertFrom-Json
    Write-Host "   ✅ 获取到 $($servers.Count) 个服务器" -ForegroundColor Green
    
    foreach ($server in $servers) {
        Write-Host "   - $($server.node_id): $($server.status) ($($server.accounts_count)/$($server.max_accounts))" -ForegroundColor Gray
    }
    
    $serversAvailable = $true
} catch {
    Write-Host "   ⚠️  获取服务器列表失败（可能API不可用或需要重启后端服务），继续测试..." -ForegroundColor Yellow
    Write-Host "   错误: $_" -ForegroundColor Gray
}

# 3. 扫描本地session文件
Write-Host "`n3. 扫描本地session文件..." -ForegroundColor Yellow
$sessionsPath = "sessions"
if (-not (Test-Path $sessionsPath)) {
    Write-Host "   ❌ sessions目录不存在: $sessionsPath" -ForegroundColor Red
    exit 1
}

$sessionFiles = Get-ChildItem -Path $sessionsPath -Filter "*.session" -File | Where-Object { 
    $_.Name -notmatch "-journal$" -and $_.Length -gt 1000 
} | Sort-Object LastWriteTime -Descending

if ($sessionFiles.Count -eq 0) {
    Write-Host "   ❌ 未找到有效的session文件" -ForegroundColor Red
    exit 1
}

Write-Host "   ✅ 找到 $($sessionFiles.Count) 个有效的session文件" -ForegroundColor Green

# 4. 获取剧本列表
Write-Host "`n4. 获取剧本列表..." -ForegroundColor Yellow
try {
    $scriptsResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/scripts" `
        -Method GET `
        -Headers $headers `
        -UseBasicParsing
    
    $scripts = $scriptsResponse.Content | ConvertFrom-Json
    $scriptId = $null
    
    if ($scripts.Count -gt 0) {
        $scriptId = $scripts[0].script_id
        Write-Host "   ✅ 获取到 $($scripts.Count) 个剧本，使用: $scriptId" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  没有可用的剧本，将使用默认剧本" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  获取剧本列表失败，将使用默认剧本" -ForegroundColor Yellow
}

# 5. 创建测试账号（自动分配到服务器）
Write-Host "`n5. 创建测试账号（自动分配到服务器）..." -ForegroundColor Yellow
$testAccountId = $null
$testSessionFile = $sessionFiles[0]

try {
    # 提取账号ID
    $testAccountId = $testSessionFile.BaseName
    
    # 检查账号是否已存在
    try {
        $existingAccountResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts/$testAccountId" `
            -Method GET `
            -Headers $headers `
            -UseBasicParsing
        
        Write-Host "   ⚠️  账号 $testAccountId 已存在，跳过创建" -ForegroundColor Yellow
        $existingAccount = $existingAccountResponse.Content | ConvertFrom-Json
        $testAccountId = $existingAccount.account_id
    } catch {
        # 账号不存在，创建新账号
        Write-Host "   创建账号: $testAccountId" -ForegroundColor Gray
        
        $createAccountBody = @{
            account_id = $testAccountId
            session_file = $testSessionFile.FullName
            script_id = $scriptId
        } | ConvertTo-Json
        
        $createResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts" `
            -Method POST `
            -Headers $headers `
            -Body $createAccountBody `
            -UseBasicParsing
        
        $createdAccount = $createResponse.Content | ConvertFrom-Json
        Write-Host "   ✅ 账号创建成功" -ForegroundColor Green
        Write-Host "     账号ID: $($createdAccount.account_id)" -ForegroundColor Gray
        Write-Host "     服务器ID: $($createdAccount.server_id)" -ForegroundColor Gray
        Write-Host "     状态: $($createdAccount.status)" -ForegroundColor Gray
        
        if ($createdAccount.server_id) {
            Write-Host "   ✅ 账号已自动分配到服务器: $($createdAccount.server_id)" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  账号未分配到服务器（将在本地运行）" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "   ❌ 创建账号失败: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $errorContent = $_.Exception.Response.Content | ConvertFrom-Json
        Write-Host "     错误详情: $($errorContent.detail)" -ForegroundColor Red
    }
    exit 1
}

# 6. 启动账号（应该在服务器上启动）
Write-Host "`n6. 启动账号（应该在服务器上启动）..." -ForegroundColor Yellow
try {
    Write-Host "   发送启动请求..." -ForegroundColor Gray
    $startResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts/$testAccountId/start" `
        -Method POST `
        -Headers $headers `
        -UseBasicParsing
    
    $startResult = $startResponse.Content | ConvertFrom-Json
    Write-Host "   ✅ 启动请求成功" -ForegroundColor Green
    Write-Host "     消息: $($startResult.message)" -ForegroundColor Gray
    
    if ($startResult.server_id) {
        Write-Host "   ✅ 账号在服务器 $($startResult.server_id) 上启动" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  账号在本地启动" -ForegroundColor Yellow
    }
    
    # 等待几秒让账号启动
    Write-Host "   等待5秒让账号启动..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
    
    # 检查账号状态
    $accountResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts/$testAccountId" `
        -Method GET `
        -Headers $headers `
        -UseBasicParsing
    
    $account = $accountResponse.Content | ConvertFrom-Json
    Write-Host "   账号状态: $($account.status)" -ForegroundColor Gray
    
    if ($account.status -eq "online") {
        Write-Host "   ✅ 账号启动成功并在线" -ForegroundColor Green
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
            Write-Host "     错误详情: $($_.Exception.Response.Content)" -ForegroundColor Red
        }
    }
}

# 7. 测试结果汇总
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  测试结果汇总" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "测试账号: $testAccountId" -ForegroundColor Yellow
Write-Host "服务器分配: $(if ($account.server_id) { $account.server_id } else { '未分配' })" -ForegroundColor Yellow
Write-Host "账号状态: $($account.status)" -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ 测试完成" -ForegroundColor Green

