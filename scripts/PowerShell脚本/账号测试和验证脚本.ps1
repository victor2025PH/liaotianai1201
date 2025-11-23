# 账号测试和验证脚本
# 功能：扫描session文件，创建账号，测试启动，记录可用/不可用账号

param(
    [string]$ScriptId = "000新人欢迎剧本"
)

Write-Host "=== 账号测试和验证脚本 ===" -ForegroundColor Cyan
Write-Host ""

# 1. 登录获取Token
Write-Host "1. 登录获取Token..." -ForegroundColor Yellow
try {
    $loginResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/x-www-form-urlencoded" -Body "username=admin@example.com&password=changeme123" -ErrorAction Stop
    $token = ($loginResponse.Content | ConvertFrom-Json).access_token
    $script:headers = @{ 
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    Write-Host "✅ Token获取成功" -ForegroundColor Green
    Write-Host "   Token前30字符: $($token.Substring(0, [Math]::Min(30, $token.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "❌ 登录失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. 扫描session文件（直接从文件系统）
Write-Host "`n2. 扫描session文件..." -ForegroundColor Yellow
$sessionsPath = "E:\002-工作文件\重要程序\聊天AI群聊程序\sessions"
if (-not (Test-Path $sessionsPath)) {
    Write-Host "❌ Session目录不存在: $sessionsPath" -ForegroundColor Red
    exit 1
}

$sessionFiles = Get-ChildItem -Path $sessionsPath -Filter "*.session" -ErrorAction SilentlyContinue | Where-Object { 
    -not $_.Name.EndsWith("-journal") -and 
    -not $_.Name.ToLower().StartsWith("test") -and
    $_.Length -gt 0
}

$sessions = @()
foreach ($file in $sessionFiles) {
    $sessions += @{
        filename = $file.Name
        path = $file.FullName
        size = $file.Length
        modified = $file.LastWriteTime
    }
}

Write-Host "✅ 找到 $($sessions.Count) 个session文件" -ForegroundColor Green

if ($sessions.Count -eq 0) {
    Write-Host "⚠️ 没有找到session文件" -ForegroundColor Yellow
    exit 0
}

# 3. 获取现有账号列表
Write-Host "`n3. 获取现有账号列表..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/group-ai/accounts" -Method GET -Headers $script:headers -ErrorAction Stop
    $accountsResult = $response.Content | ConvertFrom-Json
    $existingAccounts = $accountsResult.accounts
    $existingAccountIds = $existingAccounts | ForEach-Object { $_.account_id }
    Write-Host "✅ 现有账号数量: $($existingAccounts.Count)" -ForegroundColor Green
} catch {
    Write-Host "⚠️ 获取账号列表失败，继续..." -ForegroundColor Yellow
    $existingAccountIds = @()
}

# 4. 测试结果存储
$testResults = @()
$validAccounts = @()
$invalidAccounts = @()

# 5. 处理每个session文件
Write-Host "`n4. 开始测试账号..." -ForegroundColor Yellow
Write-Host ""

foreach ($session in $sessions) {
    $sessionFileName = $session.filename
    $accountId = $sessionFileName -replace '\.session$', ''
    
    Write-Host "处理账号: $accountId" -ForegroundColor Cyan
    Write-Host "  Session文件: $sessionFileName"
    
    $testResult = @{
        AccountId = $accountId
        SessionFile = $sessionFileName
        Status = "unknown"
        Message = ""
        ServerId = $null
        CanStart = $false
    }
    
    # 5.1 检查账号是否已存在
    if ($accountId -in $existingAccountIds) {
        Write-Host "  ⚠️ 账号已存在，跳过创建" -ForegroundColor Yellow
        $existingAccount = $existingAccounts | Where-Object { $_.account_id -eq $accountId } | Select-Object -First 1
        $testResult.ServerId = $existingAccount.server_id
        $testResult.Status = "exists"
    } else {
        # 5.2 创建账号
        Write-Host "  📝 创建账号..." -ForegroundColor Yellow
        try {
            $createBody = @{
                account_id = $accountId
                session_file = $sessionFileName
                script_id = $ScriptId
            } | ConvertTo-Json -Compress
            
            Write-Host "    请求体: $createBody" -ForegroundColor Gray
            $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/group-ai/accounts" -Method POST -Headers $script:headers -Body $createBody -ErrorAction Stop
            $createdAccount = $response.Content | ConvertFrom-Json
            $testResult.ServerId = $createdAccount.server_id
            Write-Host "  ✅ 账号创建成功，分配到服务器: $($createdAccount.server_id)" -ForegroundColor Green
            $testResult.Status = "created"
        } catch {
            $errorDetail = $_.Exception.Message
            try {
                $errorResponse = $_.Exception.Response
                if ($errorResponse) {
                    $reader = New-Object System.IO.StreamReader($errorResponse.GetResponseStream())
                    $errorBody = $reader.ReadToEnd()
                    $errorObj = $errorBody | ConvertFrom-Json
                    $errorDetail = $errorObj.detail
                }
            } catch {}
            Write-Host "  ❌ 创建失败: $errorDetail" -ForegroundColor Red
            $testResult.Status = "create_failed"
            $testResult.Message = $errorDetail
            $invalidAccounts += $testResult
            $testResults += $testResult
            continue
        }
    }
    
    # 5.3 测试启动账号
    Write-Host "  🚀 测试启动账号..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2  # 等待账号创建完成
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/group-ai/accounts/$accountId/start" -Method POST -Headers $script:headers -ErrorAction Stop
        $startResult = $response.Content | ConvertFrom-Json
        Write-Host "  ✅ 启动成功: $($startResult.message)" -ForegroundColor Green
        $testResult.Status = "valid"
        $testResult.Message = "账号启动成功"
        $testResult.CanStart = $true
        $validAccounts += $testResult
        } catch {
            $errorDetail = $_.Exception.Message
            try {
                $errorResponse = $_.Exception.Response
                if ($errorResponse) {
                    $stream = $errorResponse.GetResponseStream()
                    $reader = New-Object System.IO.StreamReader($stream)
                    $errorBody = $reader.ReadToEnd()
                    $reader.Close()
                    $stream.Close()
                    try {
                        $errorObj = $errorBody | ConvertFrom-Json
                        $errorDetail = $errorObj.detail
                    } catch {
                        $errorDetail = $errorBody
                    }
                }
            } catch {}
        Write-Host "  ❌ 启动失败: $errorDetail" -ForegroundColor Red
        $testResult.Status = "invalid"
        $testResult.Message = $errorDetail
        $testResult.CanStart = $false
        $invalidAccounts += $testResult
    }
    
    $testResults += $testResult
    Write-Host ""
}

# 6. 输出测试结果
Write-Host "`n=== 测试结果汇总 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "总测试账号数: $($testResults.Count)" -ForegroundColor White
Write-Host "可用账号数: $($validAccounts.Count)" -ForegroundColor Green
Write-Host "不可用账号数: $($invalidAccounts.Count)" -ForegroundColor Red
Write-Host ""

# 7. 输出可用账号
if ($validAccounts.Count -gt 0) {
    Write-Host "=== 可用账号列表 ===" -ForegroundColor Green
    $validAccounts | ForEach-Object {
        Write-Host "  ✅ $($_.AccountId) - 服务器: $($_.ServerId)" -ForegroundColor Green
    }
    Write-Host ""
}

# 8. 输出不可用账号及原因
if ($invalidAccounts.Count -gt 0) {
    Write-Host "=== 不可用账号列表 ===" -ForegroundColor Red
    $invalidAccounts | ForEach-Object {
        Write-Host "  ❌ $($_.AccountId)" -ForegroundColor Red
        Write-Host "     原因: $($_.Message)" -ForegroundColor Yellow
    }
    Write-Host ""
}

# 9. 保存结果到文件
$resultFile = "账号测试结果_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$testResults | ConvertTo-Json -Depth 10 | Out-File -FilePath $resultFile -Encoding UTF8
Write-Host "测试结果已保存到: $resultFile" -ForegroundColor Cyan

# 10. 生成通知（如果需要）
if ($invalidAccounts.Count -gt 0) {
    $notificationFile = "不可用账号通知_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
    $notification = @"
不可用账号通知
生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

以下账号无法正常启动，请检查：

"@
    $invalidAccounts | ForEach-Object {
        $notification += "账号ID: $($_.AccountId)`n"
        $notification += "Session文件: $($_.SessionFile)`n"
        $notification += "失败原因: $($_.Message)`n"
        $notification += "`n"
    }
    $notification | Out-File -FilePath $notificationFile -Encoding UTF8
    Write-Host "不可用账号通知已保存到: $notificationFile" -ForegroundColor Yellow
}

Write-Host "`n测试完成！" -ForegroundColor Cyan

