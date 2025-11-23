# 验证新的API端点是否已加载
$baseUrl = "http://localhost:8000/api/v1"

Write-Host "=== 验证新的API端点 ===" -ForegroundColor Cyan

# 1. 登录
Write-Host "`n1. 登录获取Token..." -ForegroundColor Yellow
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
    Write-Host "   请确保后端服务正在运行" -ForegroundColor Yellow
    exit 1
}

# 2. 测试新API端点
Write-Host "`n2. 测试新的API端点..." -ForegroundColor Yellow
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$testBody = @{
    account_id = "test"
    group_id = -1
    message = "test"
} | ConvertTo-Json

try {
    $testResponse = Invoke-WebRequest -Uri "$baseUrl/group-ai/groups/send-test-message" `
        -Method POST `
        -Headers $headers `
        -Body $testBody `
        -UseBasicParsing `
        -ErrorAction Stop
    
    Write-Host "   ⚠️  API端点返回了响应（不应该成功，因为参数无效）" -ForegroundColor Yellow
    Write-Host "   状态码: $($testResponse.StatusCode)" -ForegroundColor Gray
    
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    
    if ($statusCode -eq 404) {
        Write-Host "   ❌ API端点不存在（404）" -ForegroundColor Red
        Write-Host "   后端服务可能未重启，或者新API端点未加载" -ForegroundColor Yellow
        Write-Host "`n   请检查：" -ForegroundColor Yellow
        Write-Host "   1. 后端服务是否已重启" -ForegroundColor Gray
        Write-Host "   2. admin-backend/app/api/group_ai/groups.py 文件是否包含 send-test-message 端点" -ForegroundColor Gray
        Write-Host "   3. 后端日志中是否有错误信息" -ForegroundColor Gray
        exit 1
    } elseif ($statusCode -eq 422 -or $statusCode -eq 400) {
        Write-Host "   ✅ API端点已加载！" -ForegroundColor Green
        Write-Host "   状态码: $statusCode (验证错误是正常的，因为测试参数无效)" -ForegroundColor Gray
        Write-Host "`n   ✅ 新的API端点已成功加载，可以开始测试！" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  意外的状态码: $statusCode" -ForegroundColor Yellow
        Write-Host "   响应内容: $($_.Exception.Response)" -ForegroundColor Gray
    }
}

Write-Host "`n=== 验证完成 ===" -ForegroundColor Cyan

