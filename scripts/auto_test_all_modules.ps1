# 全自动测试所有功能模块
# 包括登录、服务器管理、账号管理、剧本管理等

$ErrorActionPreference = "Continue"

$baseUrl = "http://localhost:8000"
$frontendUrl = "http://localhost:3000"

Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🤖 全自动测试所有功能模块" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

$testResults = @()
$errors = @()
$warnings = @()

function Test-API {
    param(
        [string]$Name,
        [string]$Method = "GET",
        [string]$Uri,
        [hashtable]$Headers = $null,
        [object]$Body = $null,
        [int]$Timeout = 10
    )
    
    Write-Host "`n[$Name] 测试中..." -ForegroundColor Yellow
    
    try {
        $params = @{
            Uri = $Uri
            Method = $Method
            TimeoutSec = $Timeout
            ErrorAction = "Stop"
        }
        
        if ($Headers) {
            $params.Headers = $Headers
        }
        
        if ($Body) {
            if ($Body -is [string]) {
                $params.Body = $Body
                $params.ContentType = "application/x-www-form-urlencoded"
            } else {
                $params.Body = ($Body | ConvertTo-Json -Depth 10)
                $params.ContentType = "application/json"
            }
        }
        
        $response = Invoke-RestMethod @params
        Write-Host "   ✅ 通过" -ForegroundColor Green
        
        $result = @{
            Name = $Name
            Status = "PASS"
            Response = $response
        }
        
        # 提取有用的信息
        if ($response -is [PSCustomObject] -or $response -is [System.Array]) {
            if ($response.Count) {
                $result.Info = "找到 $($response.Count) 项"
            } elseif ($response.items -and $response.items.Count) {
                $result.Info = "找到 $($response.items.Count) 项"
            } elseif ($response.total) {
                $result.Info = "总计 $($response.total) 项"
            }
        }
        
        $script:testResults += $result
        return $true
    } catch {
        $errorMsg = $_.Exception.Message
        Write-Host "   ❌ 失败: $errorMsg" -ForegroundColor Red
        
        # 尝试获取详细错误信息
        if ($_.Exception.Response) {
            try {
                $stream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($stream)
                $responseBody = $reader.ReadToEnd()
                if ($responseBody) {
                    Write-Host "   详情: $responseBody" -ForegroundColor Gray
                    $errorMsg += " - $responseBody"
                }
            } catch {
                # 忽略读取错误
            }
        }
        
        $script:testResults += @{
            Name = $Name
            Status = "FAIL"
            Error = $errorMsg
        }
        $script:errors += "$Name : $errorMsg"
        return $false
    }
}

# 1. 检查服务状态
Write-Host "`n[0/10] 检查服务状态..." -ForegroundColor Yellow
try {
    $backendHealth = Invoke-RestMethod -Uri "$baseUrl/health" -TimeoutSec 3
    Write-Host "   ✅ 后端服务正常: $($backendHealth.status)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 后端服务异常: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

try {
    $frontendCheck = Invoke-WebRequest -Uri $frontendUrl -TimeoutSec 3 -UseBasicParsing
    Write-Host "   ✅ 前端服务正常: HTTP $($frontendCheck.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  前端服务可能还在启动中" -ForegroundColor Yellow
    $script:warnings += "前端服务可能未完全启动"
}

# 2. 登录
$loginBody = "username=admin@example.com&password=changeme123"
$loginSuccess = Test-API -Name "1. 登录" -Method "POST" -Uri "$baseUrl/api/v1/auth/login" -Body $loginBody

if (-not $loginSuccess) {
    Write-Host "`n❌ 登录失败，无法继续测试" -ForegroundColor Red
    exit 1
}

$token = $testResults[-1].Response.access_token
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

Write-Host "   Token已获取: $($token.Substring(0, 30))..." -ForegroundColor Gray

# 3. 获取当前用户信息
Test-API -Name "2. 获取当前用户" -Uri "$baseUrl/api/v1/users/me" -Headers $headers

# 4. 获取服务器列表
$serversTest = Test-API -Name "3. 获取服务器列表" -Uri "$baseUrl/api/v1/group-ai/servers" -Headers $headers
$servers = $null
if ($serversTest) {
    $servers = $testResults[-1].Response
}

# 5. 测试扫描服务器账号
if ($servers -and $servers.Count -gt 0) {
    $testServerId = $servers[0].node_id
    Write-Host "`n   使用服务器 $testServerId 进行测试" -ForegroundColor Gray
    Test-API -Name "4. 扫描服务器账号 ($testServerId)" -Uri "$baseUrl/api/v1/group-ai/account-management/scan-server-accounts?server_id=$testServerId" -Headers $headers -Timeout 20
    
    # 检查扫描结果
    if ($testResults[-1].Status -eq "PASS") {
        $scanResult = $testResults[-1].Response
        if ($scanResult -and $scanResult.Count -gt 0) {
            $serverData = $scanResult[0]
            Write-Host "      服务器: $($serverData.server_id)" -ForegroundColor Gray
            Write-Host "      账号数: $($serverData.total_count)" -ForegroundColor Gray
            if ($serverData.accounts -and $serverData.accounts.Count -gt 0) {
                Write-Host "      账号列表:" -ForegroundColor Gray
                foreach ($acc in $serverData.accounts) {
                    Write-Host "         - $($acc.account_id): $($acc.session_file)" -ForegroundColor Gray
                }
            } else {
                Write-Host "      ⚠️  账号列表为空" -ForegroundColor Yellow
                $script:warnings += "服务器 $testServerId 账号列表为空"
            }
        }
    }
} else {
    Write-Host "`n⚠️  没有服务器，跳过账号扫描测试" -ForegroundColor Yellow
    $script:warnings += "没有可用的服务器进行账号扫描测试"
}

# 6. 获取剧本列表
Test-API -Name "5. 获取剧本列表" -Uri "$baseUrl/api/v1/group-ai/scripts" -Headers $headers

# 7. 获取账号列表
Test-API -Name "6. 获取账号列表" -Uri "$baseUrl/api/v1/group-ai/accounts" -Headers $headers

# 8. 获取自动化任务列表
Test-API -Name "7. 获取自动化任务列表" -Uri "$baseUrl/api/v1/group-ai/automation-tasks" -Headers $headers

# 9. 获取分配方案列表（如果存在）
Test-API -Name "8. 获取分配方案列表" -Uri "$baseUrl/api/v1/group-ai/account-allocation/schemes" -Headers $headers

# 10. 获取角色列表
Test-API -Name "9. 获取角色列表" -Uri "$baseUrl/api/v1/user-roles" -Headers $headers

# 11. 获取权限列表
Test-API -Name "10. 获取权限列表" -Uri "$baseUrl/api/v1/permissions" -Headers $headers

# 总结
Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "📊 测试结果总结" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

$passed = ($testResults | Where-Object {$_.Status -eq "PASS"}).Count
$failed = ($testResults | Where-Object {$_.Status -eq "FAIL"}).Count

foreach ($result in $testResults) {
    $status = if ($result.Status -eq "PASS") { "✅" } else { "❌" }
    $color = if ($result.Status -eq "PASS") { "Green" } else { "Red" }
    Write-Host "   $status $($result.Name)" -ForegroundColor $color
    if ($result.Info) {
        Write-Host "      $($result.Info)" -ForegroundColor Gray
    }
    if ($result.Error) {
        Write-Host "      错误: $($result.Error)" -ForegroundColor Red
    }
}

Write-Host "`n总计: $passed 通过, $failed 失败" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Yellow" })

if ($warnings.Count -gt 0) {
    Write-Host "`n⚠️  警告 ($($warnings.Count) 个):" -ForegroundColor Yellow
    $warnings | ForEach-Object {
        Write-Host "   - $_" -ForegroundColor Gray
    }
}

if ($errors.Count -gt 0) {
    Write-Host "`n❌ 错误 ($($errors.Count) 个):" -ForegroundColor Red
    $errors | ForEach-Object {
        Write-Host "   - $_" -ForegroundColor Gray
    }
    Write-Host "`n💡 需要修复的问题已记录" -ForegroundColor Yellow
} else {
    Write-Host "`n✅ 所有测试通过！" -ForegroundColor Green
}

Write-Host ""

