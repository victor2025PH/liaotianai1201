# 测试账号启动脚本
# 测试8个账号的启动功能

$baseUrl = "http://localhost:8000/api/v1"
$accounts = @(
    "639277333688",
    "639277356155",
    "639277356598",
    "639457597211",
    "639641837416",
    "639641842001",
    "639652840998",
    "639679410504"
)

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

# 测试每个账号的启动
Write-Host "`n=== 开始测试账号启动 ===" -ForegroundColor Cyan
$results = @()

foreach ($accountId in $accounts) {
    Write-Host "`n测试账号: $accountId" -ForegroundColor Yellow
    
    try {
        # 先获取账号状态
        $getAccountResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts/$accountId" `
            -Method GET `
            -Headers @{ "Authorization" = "Bearer $token" } `
            -UseBasicParsing
        
        $accountData = $getAccountResponse.Content | ConvertFrom-Json
        $initialStatus = $accountData.status
        Write-Host "  初始状态: $initialStatus" -ForegroundColor Gray
        
        # 如果账号是offline状态，尝试启动
        if ($initialStatus -eq "offline") {
            Write-Host "  尝试启动账号..." -ForegroundColor Yellow
            
            $startResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts/$accountId/start" `
                -Method POST `
                -Headers @{ "Authorization" = "Bearer $token" } `
                -UseBasicParsing
            
            Write-Host "  启动请求已发送，等待3秒..." -ForegroundColor Yellow
            Start-Sleep -Seconds 3
            
            # 再次获取账号状态
            $getAccountResponse2 = Invoke-WebRequest -Uri "$baseUrl/group-ai/accounts/$accountId" `
                -Method GET `
                -Headers @{ "Authorization" = "Bearer $token" } `
                -UseBasicParsing
            
            $accountData2 = $getAccountResponse2.Content | ConvertFrom-Json
            $finalStatus = $accountData2.status
            
            $result = [PSCustomObject]@{
                AccountId = $accountId
                InitialStatus = $initialStatus
                FinalStatus = $finalStatus
                Success = ($finalStatus -eq "online")
                Error = $null
            }
            
            if ($finalStatus -eq "online") {
                Write-Host "  ✅ 账号启动成功 (状态: $finalStatus)" -ForegroundColor Green
            } elseif ($finalStatus -eq "error") {
                Write-Host "  ❌ 账号启动失败 (状态: $finalStatus)" -ForegroundColor Red
            } else {
                Write-Host "  ⏸️  账号状态: $finalStatus" -ForegroundColor Yellow
            }
        } else {
            $result = [PSCustomObject]@{
                AccountId = $accountId
                InitialStatus = $initialStatus
                FinalStatus = $initialStatus
                Success = ($initialStatus -eq "online")
                Error = "账号已经是 $initialStatus 状态"
            }
            
            if ($initialStatus -eq "online") {
                Write-Host "  ✅ 账号已经在线" -ForegroundColor Green
            } else {
                Write-Host "  ⏸️  账号状态: $initialStatus" -ForegroundColor Yellow
            }
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
        
        $result = [PSCustomObject]@{
            AccountId = $accountId
            InitialStatus = "unknown"
            FinalStatus = "error"
            Success = $false
            Error = $errorMessage
        }
        
        Write-Host "  ❌ 测试失败: $errorMessage" -ForegroundColor Red
    }
    
    $results += $result
}

# 输出汇总结果
Write-Host "`n=== 测试结果汇总 ===" -ForegroundColor Cyan
$successCount = ($results | Where-Object { $_.Success }).Count
$failCount = ($results | Where-Object { -not $_.Success }).Count
Write-Host "总账号数: $($accounts.Count)"
Write-Host "成功启动: $successCount"
Write-Host "启动失败: $failCount"

Write-Host "`n=== 详细结果 ===" -ForegroundColor Cyan
$results | Format-Table -AutoSize

# 保存结果到文件
if ($results.Count -gt 0) {
    $results | Export-Csv -Path "账号启动测试结果.csv" -NoTypeInformation -Encoding UTF8
    Write-Host "`n结果已保存到: 账号启动测试结果.csv" -ForegroundColor Green
} else {
    Write-Host "`n警告: 没有结果可保存" -ForegroundColor Yellow
}

