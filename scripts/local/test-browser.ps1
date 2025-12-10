# ============================================================
# 浏览器测试脚本 (Windows PowerShell)
# ============================================================
# 功能：打开浏览器测试所有功能
# 使用方法：powershell scripts/local/test-browser.ps1
# ============================================================

$ErrorActionPreference = "Stop"

# 配置
$BASE_URL = "http://localhost:8000"
$FRONTEND_URL = "http://localhost:3000"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🌐 浏览器功能测试" -ForegroundColor Cyan
Write-Host "============================================================"
Write-Host ""

# 检查服务是否运行
Write-Host "[1] 检查服务状态..." -ForegroundColor Yellow

try {
    $healthResponse = Invoke-WebRequest -Uri "$BASE_URL/health" -UseBasicParsing -TimeoutSec 5
    if ($healthResponse.StatusCode -eq 200) {
        Write-Host "✅ 后端服务运行正常" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ 后端服务未运行或无法访问" -ForegroundColor Red
    Write-Host "   请先启动后端服务" -ForegroundColor Yellow
    exit 1
}

# 打开浏览器测试页面
Write-Host ""
Write-Host "[2] 打开测试页面..." -ForegroundColor Yellow

$testPages = @(
    @{
        Name = "后端 API 文档 (Swagger)"
        Url = "$BASE_URL/docs"
    },
    @{
        Name = "后端 API 文档 (ReDoc)"
        Url = "$BASE_URL/redoc"
    },
    @{
        Name = "后端健康检查"
        Url = "$BASE_URL/health"
    },
    @{
        Name = "前端首页"
        Url = "https://aikz.usdt2026.cc"
    }
)

foreach ($page in $testPages) {
    Write-Host "   打开: $($page.Name) - $($page.Url)" -ForegroundColor Cyan
    Start-Process $page.Url
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ 浏览器测试页面已打开" -ForegroundColor Green
Write-Host "============================================================"
Write-Host ""
Write-Host "📝 测试清单:" -ForegroundColor Yellow
Write-Host "   1. 检查 Swagger UI 是否正常加载"
Write-Host "   2. 检查 API 端点是否可访问"
Write-Host "   3. 测试登录功能"
Write-Host "   4. 测试各个功能模块"
Write-Host "   5. 检查前端页面是否正常显示"
Write-Host ""
Write-Host "💡 提示: 如果遇到问题，查看日志:" -ForegroundColor Yellow
Write-Host "   bash scripts/server/view-logs.sh backend -f"
Write-Host ""

