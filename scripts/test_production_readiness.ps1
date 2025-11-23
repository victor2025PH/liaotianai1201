# 生产环境就绪性全面测试脚本 (PowerShell 版本)
# 测试所有核心功能、监控和部署能力

$ErrorActionPreference = "Continue"

# 测试结果统计
$script:TotalTests = 0
$script:PassedTests = 0
$script:FailedTests = 0
$script:SkippedTests = 0

# 测试报告文件
$ReportFile = "test_reports/production_readiness_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"
$ReportDir = "test_reports"
if (-not (Test-Path $ReportDir)) {
    New-Item -ItemType Directory -Path $ReportDir | Out-Null
}

# 测试函数
function Test-Pass {
    param([string]$Name, [string]$Details = "")
    $script:TotalTests++
    $script:PassedTests++
    Write-Host "✓ $Name" -ForegroundColor Green
    Add-Content -Path $ReportFile -Value "✓ $Name"
    if ($Details) {
        Add-Content -Path $ReportFile -Value "  $Details"
    }
}

function Test-Fail {
    param([string]$Name, [string]$Error = "")
    $script:TotalTests++
    $script:FailedTests++
    Write-Host "✗ $Name" -ForegroundColor Red
    Add-Content -Path $ReportFile -Value "✗ $Name"
    if ($Error) {
        Write-Host "  错误: $Error" -ForegroundColor Red
        Add-Content -Path $ReportFile -Value "  错误: $Error"
    }
}

function Test-Skip {
    param([string]$Name, [string]$Reason = "")
    $script:TotalTests++
    $script:SkippedTests++
    Write-Host "⊘ $Name (跳过)" -ForegroundColor Yellow
    Add-Content -Path $ReportFile -Value "⊘ $Name (跳过)"
    if ($Reason) {
        Add-Content -Path $ReportFile -Value "  原因: $Reason"
    }
}

# 初始化报告
function Initialize-Report {
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $envInfo = (Get-ComputerInfo).WindowsProductName
    @"
# 生产环境就绪性测试报告

**测试时间**: $timestamp
**测试环境**: $envInfo

---

## 测试结果摘要

"@ | Out-File -FilePath $ReportFile -Encoding UTF8
}

# 生成报告摘要
function Generate-Summary {
    $passRate = if ($script:TotalTests -gt 0) {
        [math]::Round(($script:PassedTests / $script:TotalTests) * 100, 1)
    } else { 0 }
    
    @"

---

## 测试统计

- **总测试数**: $($script:TotalTests)
- **通过**: $($script:PassedTests)
- **失败**: $($script:FailedTests)
- **跳过**: $($script:SkippedTests)
- **通过率**: $passRate%

---

## 详细测试结果

"@ | Add-Content -Path $ReportFile -Encoding UTF8
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "生产环境就绪性全面测试" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Initialize-Report

# ============================================
# 1. 环境检查
# ============================================
Write-Host "[1/6] 环境检查" -ForegroundColor Cyan
Add-Content -Path $ReportFile -Value "## 1. 环境检查"

# 检查 Python
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Test-Pass "Python 已安装: $pythonVersion"
    } else {
        Test-Fail "Python 未安装"
    }
} catch {
    Test-Fail "Python 检查失败: $_"
}

# 检查 Node.js
try {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Test-Pass "Node.js 已安装: $nodeVersion"
    } else {
        Test-Fail "Node.js 未安装"
    }
} catch {
    Test-Skip "Node.js 未安装（可选）"
}

# 检查 Docker
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Test-Pass "Docker 已安装: $dockerVersion"
    } else {
        Test-Skip "Docker 未安装（可选）"
    }
} catch {
    Test-Skip "Docker 未安装（可选）"
}

Write-Host ""

# ============================================
# 2. 后端服务测试
# ============================================
Write-Host "[2/6] 后端服务测试" -ForegroundColor Cyan
Add-Content -Path $ReportFile -Value "`n## 2. 后端服务测试"

$BackendUrl = if ($env:BACKEND_URL) { $env:BACKEND_URL } else { "http://localhost:8000" }

try {
    $response = Invoke-WebRequest -Uri "$BackendUrl/health" -Method Get -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Test-Pass "后端服务运行中 ($BackendUrl)"
        
        # 测试详细健康检查
        try {
            $detailedResponse = Invoke-WebRequest -Uri "$BackendUrl/health?detailed=true" -Method Get -TimeoutSec 5
            if ($detailedResponse.StatusCode -eq 200) {
                Test-Pass "详细健康检查端点正常"
            }
        } catch {
            Test-Fail "详细健康检查端点异常: $_"
        }
        
        # 测试 API 文档
        try {
            $docsResponse = Invoke-WebRequest -Uri "$BackendUrl/docs" -Method Get -TimeoutSec 5
            if ($docsResponse.StatusCode -eq 200) {
                Test-Pass "API 文档可访问"
            }
        } catch {
            Test-Fail "API 文档不可访问: $_"
        }
    }
} catch {
    Test-Fail "后端服务未运行 ($BackendUrl)" "提示: 请启动后端服务"
}

Write-Host ""

# ============================================
# 3. 监控功能测试
# ============================================
Write-Host "[3/6] 监控功能测试" -ForegroundColor Cyan
Add-Content -Path $ReportFile -Value "`n## 3. 监控功能测试"

try {
    $metricsResponse = Invoke-WebRequest -Uri "$BackendUrl/metrics" -Method Get -TimeoutSec 5 -ErrorAction Stop
    if ($metricsResponse.StatusCode -eq 200) {
        $metrics = $metricsResponse.Content
        if ($metrics -match "http_requests_total|prometheus") {
            Test-Pass "Prometheus 指标端点正常"
        } else {
            Test-Fail "Prometheus 指标格式异常"
        }
    }
} catch {
    Test-Skip "监控功能测试" "后端服务未运行"
}

Write-Host ""

# ============================================
# 4. Session 管理测试
# ============================================
Write-Host "[4/6] Session 管理测试" -ForegroundColor Cyan
Add-Content -Path $ReportFile -Value "`n## 4. Session 管理测试"

$sessionsDir = "sessions"
if (Test-Path $sessionsDir) {
    Test-Pass "Session 目录存在"
    
    $sessionFiles = Get-ChildItem -Path $sessionsDir -Filter "*.session" -ErrorAction SilentlyContinue
    $encFiles = Get-ChildItem -Path $sessionsDir -Filter "*.enc" -ErrorAction SilentlyContinue
    $totalSessions = ($sessionFiles.Count + $encFiles.Count)
    
    if ($totalSessions -gt 0) {
        Test-Pass "找到 $totalSessions 个 Session 文件"
    } else {
        Test-Skip "未找到 Session 文件（可选）"
    }
} else {
    Test-Skip "Session 目录不存在（可选）"
}

Write-Host ""

# ============================================
# 5. 部署配置测试
# ============================================
Write-Host "[5/6] 部署配置测试" -ForegroundColor Cyan
Add-Content -Path $ReportFile -Value "`n## 5. 部署配置测试"

# 检查 Dockerfile
$dockerfiles = @(
    "admin-backend/Dockerfile",
    "admin-frontend/Dockerfile",
    "saas-demo/Dockerfile"
)

foreach ($dockerfile in $dockerfiles) {
    if (Test-Path $dockerfile) {
        Test-Pass "Dockerfile 存在: $(Split-Path $dockerfile -Leaf)"
    } else {
        $name = Split-Path $dockerfile -Parent
        Test-Skip "Dockerfile 不存在: $name"
    }
}

# 检查 Kubernetes 配置
if (Test-Path "deploy/k8s") {
    $k8sFiles = Get-ChildItem -Path "deploy/k8s" -Filter "*.yaml" -Recurse -ErrorAction SilentlyContinue
    if ($k8sFiles.Count -gt 0) {
        Test-Pass "Kubernetes 配置文件存在 ($($k8sFiles.Count) 个文件)"
    } else {
        Test-Skip "Kubernetes 配置文件目录为空"
    }
} else {
    Test-Skip "Kubernetes 配置目录不存在（可选）"
}

# 检查 CI/CD 配置
if (Test-Path ".github/workflows") {
    $workflowFiles = Get-ChildItem -Path ".github/workflows" -Filter "*.yml" -ErrorAction SilentlyContinue
    if ($workflowFiles.Count -gt 0) {
        Test-Pass "GitHub Actions 工作流存在 ($($workflowFiles.Count) 个文件)"
    } else {
        Test-Skip "GitHub Actions 工作流不存在"
    }
} else {
    Test-Skip "GitHub Actions 配置目录不存在（可选）"
}

Write-Host ""

# ============================================
# 6. 文档完整性测试
# ============================================
Write-Host "[6/6] 文档完整性测试" -ForegroundColor Cyan
Add-Content -Path $ReportFile -Value "`n## 6. 文档完整性测试"

$requiredDocs = @(
    "docs/使用说明/DEPLOYMENT_GUIDE.md",
    "docs/使用说明/故障排查指南.md",
    "docs/使用说明/API文档使用指南.md",
    "docs/使用说明/SESSION跨服务器部署指南.md",
    "README.md"
)

foreach ($doc in $requiredDocs) {
    if (Test-Path $doc) {
        Test-Pass "文档存在: $(Split-Path $doc -Leaf)"
    } else {
        Test-Fail "文档缺失: $doc"
    }
}

Write-Host ""

# ============================================
# 生成报告摘要
# ============================================
Generate-Summary

# 输出摘要
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "总测试数: $($script:TotalTests)" -ForegroundColor Cyan
Write-Host "通过: $($script:PassedTests)" -ForegroundColor Green
Write-Host "失败: $($script:FailedTests)" -ForegroundColor Red
Write-Host "跳过: $($script:SkippedTests)" -ForegroundColor Yellow

if ($script:TotalTests -gt 0) {
    $passRate = [math]::Round(($script:PassedTests / $script:TotalTests) * 100, 1)
    Write-Host "通过率: $passRate%`n" -ForegroundColor Cyan
}

Write-Host "详细报告: $ReportFile`n" -ForegroundColor Cyan

# 返回退出码
if ($script:FailedTests -eq 0) {
    exit 0
} else {
    exit 1
}

