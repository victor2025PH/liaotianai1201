# 全面测试所有功能模块
# 包括登录、服务器管理、账号管理、剧本管理等

$ErrorActionPreference = "Continue"

$baseUrl = "http://localhost:8000"
$frontendUrl = "http://localhost:3000"

Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🧪 全面测试所有功能模块" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

$testResults = @()
$errors = @()

function Test-Step {
    param($stepName, $testScript)
    Write-Host "`n[$stepName] 测试中..." -ForegroundColor Yellow
    try {
        $result = & $testScript
        Write-Host "   ✅ 通过" -ForegroundColor Green
        $script:testResults += @{Step=$stepName; Status="PASS"; Result=$result}
        return $true
    } catch {
        Write-Host "   ❌ 失败: $($_.Exception.Message)" -ForegroundColor Red
        $script:testResults += @{Step=$stepName; Status="FAIL"; Error=$_.Exception.Message}
        $script:errors += "$stepName : $($_.Exception.Message)"
        return $false
    }
}

# 1. 登录
$loginSuccess = Test-Step "1. 登录" {
    $body = "username=admin@example.com&password=changeme123"
    $login = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method Post -Body $body -ContentType "application/x-www-form-urlencoded" -TimeoutSec 10
    $script:token = $login.access_token
    $script:headers = @{"Authorization" = "Bearer $script:token"}
    return "Token获取成功"
}

if (-not $loginSuccess) {
    Write-Host "`n❌ 登录失败，无法继续测试" -ForegroundColor Red
    exit 1
}

# 2. 测试获取当前用户
Test-Step "2. 获取当前用户" {
    $user = Invoke-RestMethod -Uri "$baseUrl/api/v1/users/me" -Headers $script:headers -TimeoutSec 10
    return "用户: $($user.email)"
}

# 3. 测试获取服务器列表
Test-Step "3. 获取服务器列表" {
    $servers = Invoke-RestMethod -Uri "$baseUrl/api/v1/group-ai/servers" -Headers $script:headers -TimeoutSec 10
    $script:servers = $servers
    return "找到 $($servers.Count) 个服务器"
}

# 4. 测试扫描服务器账号
if ($script:servers -and $script:servers.Count -gt 0) {
    $testServerId = $script:servers[0].node_id
    Test-Step "4. 扫描服务器账号 ($testServerId)" {
        $accounts = Invoke-RestMethod -Uri "$baseUrl/api/v1/group-ai/account-management/scan-server-accounts?server_id=$testServerId" -Headers $script:headers -TimeoutSec 20
        if ($accounts -and $accounts.Count -gt 0) {
            $serverData = $accounts[0]
            return "找到 $($serverData.total_count) 个账号"
        } else {
            return "返回数据为空"
        }
    }
} else {
    Write-Host "`n⚠️  没有服务器，跳过账号扫描测试" -ForegroundColor Yellow
}

# 5. 测试获取剧本列表
Test-Step "5. 获取剧本列表" {
    $scripts = Invoke-RestMethod -Uri "$baseUrl/api/v1/group-ai/scripts" -Headers $script:headers -TimeoutSec 10
    return "找到 $($scripts.items.Count) 个剧本"
}

# 6. 测试获取账号列表
Test-Step "6. 获取账号列表" {
    $accounts = Invoke-RestMethod -Uri "$baseUrl/api/v1/group-ai/accounts" -Headers $script:headers -TimeoutSec 10
    return "找到 $($accounts.total) 个账号"
}

# 7. 测试获取自动化任务列表
Test-Step "7. 获取自动化任务列表" {
    $tasks = Invoke-RestMethod -Uri "$baseUrl/api/v1/group-ai/automation-tasks" -Headers $script:headers -TimeoutSec 10
    return "找到 $($tasks.items.Count) 个任务"
}

# 8. 测试获取分配方案列表
Test-Step "8. 获取分配方案列表" {
    $schemes = Invoke-RestMethod -Uri "$baseUrl/api/v1/group-ai/allocation-schemes" -Headers $script:headers -TimeoutSec 10
    return "找到 $($schemes.items.Count) 个方案"
}

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
    Write-Host "   $status $($result.Step)" -ForegroundColor $color
    if ($result.Result) {
        Write-Host "      $($result.Result)" -ForegroundColor Gray
    }
    if ($result.Error) {
        Write-Host "      错误: $($result.Error)" -ForegroundColor Red
    }
}

Write-Host "`n总计: $passed 通过, $failed 失败" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Yellow" })

if ($errors.Count -gt 0) {
    Write-Host "`n❌ 发现 $($errors.Count) 个错误，需要修复:" -ForegroundColor Red
    $errors | ForEach-Object {
        Write-Host "   - $_" -ForegroundColor Gray
    }
}

Write-Host ""

