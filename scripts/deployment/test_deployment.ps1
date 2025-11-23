# 部署后测试脚本 - PowerShell 版本
# 使用方法: .\test_deployment.ps1 -ServerIP <ip> [Username <user>]

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "165.154.255.48",
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "ubuntu"
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "部署后测试" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "服务器: $ServerIP`n" -ForegroundColor Cyan

# 测试计数器
$script:TotalTests = 0
$script:PassedTests = 0
$script:FailedTests = 0

function Test-Pass {
    param([string]$Name)
    $script:TotalTests++
    $script:PassedTests++
    Write-Host "✓ $Name" -ForegroundColor Green
}

function Test-Fail {
    param([string]$Name, [string]$Error = "")
    $script:TotalTests++
    $script:FailedTests++
    Write-Host "✗ $Name" -ForegroundColor Red
    if ($Error) {
        Write-Host "  错误: $Error" -ForegroundColor Red
    }
}

# 1. 测试服务可访问性
Write-Host "[1/6] 测试服务可访问性..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://${ServerIP}:8000/health" -Method Get -TimeoutSec 10 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Test-Pass "服务可访问"
    } else {
        Test-Fail "服务返回异常状态码: $($response.StatusCode)"
    }
} catch {
    Test-Fail "服务不可访问" $_.Exception.Message
    Write-Host "  提示: 检查防火墙和端口配置" -ForegroundColor Yellow
}

# 2. 测试健康检查端点
Write-Host "[2/6] 测试健康检查端点..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://${ServerIP}:8000/health" -Method Get -TimeoutSec 10
    $health = $response.Content | ConvertFrom-Json
    if ($health.status -eq "healthy" -or $health.healthy) {
        Test-Pass "健康检查端点正常"
    } else {
        Test-Fail "健康检查端点返回异常状态"
    }
} catch {
    Test-Fail "健康检查端点异常" $_.Exception.Message
}

# 3. 测试 API 文档
Write-Host "[3/6] 测试 API 文档..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://${ServerIP}:8000/docs" -Method Get -TimeoutSec 10 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Test-Pass "API 文档可访问"
    } else {
        Test-Fail "API 文档返回异常状态码"
    }
} catch {
    Test-Fail "API 文档不可访问" $_.Exception.Message
}

# 4. 测试 OpenAPI Schema
Write-Host "[4/6] 测试 OpenAPI Schema..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://${ServerIP}:8000/openapi.json" -Method Get -TimeoutSec 10 -ErrorAction Stop
    $schema = $response.Content | ConvertFrom-Json
    if ($schema.PSObject.Properties.Name -contains "paths") {
        $pathCount = ($schema.paths.PSObject.Properties | Measure-Object).Count
        Test-Pass "OpenAPI Schema 正常 ($pathCount 个端点)"
    } else {
        Test-Fail "OpenAPI Schema 格式异常"
    }
} catch {
    Test-Fail "OpenAPI Schema 不可访问" $_.Exception.Message
}

# 5. 测试系统优化 API
Write-Host "[5/6] 测试系统优化 API..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://${ServerIP}:8000/openapi.json" -Method Get -TimeoutSec 10
    $schema = $response.Content | ConvertFrom-Json
    $hasOptimization = $schema.paths.PSObject.Properties.Name | Where-Object { $_ -like "*optimization*" }
    if ($hasOptimization) {
        Test-Pass "系统优化 API 端点存在"
    } else {
        Test-Fail "系统优化 API 端点不存在"
    }
} catch {
    Test-Fail "无法检查系统优化 API" $_.Exception.Message
}

# 6. 测试性能监控
Write-Host "[6/6] 测试性能监控..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://${ServerIP}:8000/metrics" -Method Get -TimeoutSec 10 -ErrorAction Stop
    $metrics = $response.Content
    if ($metrics -match "http_requests|prometheus") {
        Test-Pass "Prometheus 指标正常"
    } else {
        Test-Fail "Prometheus 指标格式异常"
    }
} catch {
    Test-Fail "Prometheus 指标端点不可访问" $_.Exception.Message
}

# 输出摘要
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "总测试数: $($script:TotalTests)" -ForegroundColor Cyan
Write-Host "通过: $($script:PassedTests)" -ForegroundColor Green
Write-Host "失败: $($script:FailedTests)" -ForegroundColor Red

if ($script:TotalTests -gt 0) {
    $passRate = [math]::Round(($script:PassedTests / $script:TotalTests) * 100, 1)
    Write-Host "通过率: $passRate%`n" -ForegroundColor Cyan
}

Write-Host "服务地址: http://${ServerIP}:8000" -ForegroundColor Cyan
Write-Host "API 文档: http://${ServerIP}:8000/docs`n" -ForegroundColor Cyan

# 返回退出码
if ($script:FailedTests -eq 0) {
    exit 0
} else {
    exit 1
}

