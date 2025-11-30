# CI/CD 工作流驗證腳本 (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CI/CD 工作流配置驗證" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$WorkflowsDir = Join-Path $ProjectRoot ".github\workflows"

Write-Host "步驟 1: 檢查工作流文件" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$workflowFiles = Get-ChildItem -Path $WorkflowsDir -Filter "*.yml" -ErrorAction SilentlyContinue
$workflowFiles += Get-ChildItem -Path $WorkflowsDir -Filter "*.yaml" -ErrorAction SilentlyContinue

Write-Host "找到 $($workflowFiles.Count) 個工作流文件:" -ForegroundColor Green
foreach ($file in $workflowFiles) {
    Write-Host "  ✅ $($file.Name)" -ForegroundColor Green
}

Write-Host ""
Write-Host "步驟 2: 檢查關鍵功能配置" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

# 檢查 CI 工作流覆蓋率檢查
$ciFile = Join-Path $WorkflowsDir "ci.yml"
if (Test-Path $ciFile) {
    $ciContent = Get-Content $ciFile -Raw
    if ($ciContent -match "--cov-fail-under=70") {
        Write-Host "  ✅ CI 工作流: 覆蓋率閾值檢查已配置" -ForegroundColor Green
    } else {
        Write-Host "  ❌ CI 工作流: 覆蓋率閾值檢查未配置" -ForegroundColor Red
    }
    
    if ($ciContent -match "check-all") {
        Write-Host "  ✅ CI 工作流: 綜合檢查已配置" -ForegroundColor Green
    } else {
        Write-Host "  ❌ CI 工作流: 綜合檢查未配置" -ForegroundColor Red
    }
} else {
    Write-Host "  ❌ ci.yml 文件不存在" -ForegroundColor Red
}

# 檢查測試覆蓋率工作流
$testCovFile = Join-Path $WorkflowsDir "test-coverage.yml"
if (Test-Path $testCovFile) {
    $testCovContent = Get-Content $testCovFile -Raw
    if ($testCovContent -match "--cov-fail-under=70") {
        Write-Host "  ✅ 測試覆蓋率工作流: 覆蓋率閾值檢查已配置" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 測試覆蓋率工作流: 覆蓋率閾值檢查未配置" -ForegroundColor Red
    }
} else {
    Write-Host "  ❌ test-coverage.yml 文件不存在" -ForegroundColor Red
}

Write-Host ""
Write-Host "步驟 3: 檢查新增工作流" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$newWorkflows = @("notification.yml", "performance-test.yml", "lint-and-fix.yml")

foreach ($workflow in $newWorkflows) {
    $workflowFile = Join-Path $WorkflowsDir $workflow
    if (Test-Path $workflowFile) {
        Write-Host "  ✅ $workflow - 已創建" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $workflow - 未找到" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "步驟 4: 驗證工作流基本結構" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

foreach ($file in $workflowFiles) {
    $content = Get-Content $file.FullName -Raw
    
    $hasName = $content -match "^name:"
    $hasOn = $content -match "^on:"
    $hasJobs = $content -match "^jobs:"
    
    if ($hasName -and $hasOn -and $hasJobs) {
        Write-Host "  ✅ $($file.Name) - 基本結構完整" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $($file.Name) - 缺少必需字段" -ForegroundColor Red
        if (-not $hasName) { Write-Host "      - 缺少 'name' 字段" -ForegroundColor Yellow }
        if (-not $hasOn) { Write-Host "      - 缺少 'on' 字段" -ForegroundColor Yellow }
        if (-not $hasJobs) { Write-Host "      - 缺少 'jobs' 字段" -ForegroundColor Yellow }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "驗證完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
