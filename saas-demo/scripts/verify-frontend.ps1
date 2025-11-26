# 前端功能验证脚本 (PowerShell)
# 用于检查前端和后端服务是否正常运行

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "前端功能验证脚本" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查后端服务
Write-Host "1. 检查后端服务..." -ForegroundColor Yellow
$backendUrl = if ($env:NEXT_PUBLIC_API_BASE_URL) { 
    $env:NEXT_PUBLIC_API_BASE_URL -replace '/api/v1$', '' 
} else { 
    "http://localhost:8000" 
}
$backendHealth = "$backendUrl/health"

try {
    $response = Invoke-WebRequest -Uri $backendHealth -Method Get -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ 后端服务运行正常" -ForegroundColor Green
        Write-Host "  ($backendHealth)" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ 后端服务无法访问" -ForegroundColor Red
    Write-Host "  ($backendHealth)" -ForegroundColor Gray
    Write-Host "  请确保后端服务已启动：" -ForegroundColor Yellow
    Write-Host "  cd admin-backend" -ForegroundColor White
    Write-Host "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000" -ForegroundColor White
    exit 1
}

# 检查前端服务
Write-Host ""
Write-Host "2. 检查前端服务..." -ForegroundColor Yellow
$frontendUrl = if ($env:FRONTEND_URL) { $env:FRONTEND_URL } else { "http://localhost:3000" }

try {
    $response = Invoke-WebRequest -Uri $frontendUrl -Method Get -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ 前端服务运行正常" -ForegroundColor Green
        Write-Host "  ($frontendUrl)" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ 前端服务无法访问" -ForegroundColor Red
    Write-Host "  ($frontendUrl)" -ForegroundColor Gray
    Write-Host "  请确保前端服务已启动：" -ForegroundColor Yellow
    Write-Host "  cd saas-demo" -ForegroundColor White
    Write-Host "  npm run dev" -ForegroundColor White
    exit 1
}

# 检查 API 端点
Write-Host ""
Write-Host "3. 检查关键 API 端点..." -ForegroundColor Yellow

# 检查健康检查端点
try {
    $response = Invoke-WebRequest -Uri $backendHealth -Method Get -TimeoutSec 5 -ErrorAction Stop
    $content = $response.Content | ConvertFrom-Json
    if ($content.status -eq "ok") {
        Write-Host "✓ 健康检查端点正常" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠ 健康检查端点异常" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "服务检查完成！" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "1. 打开浏览器访问: $frontendUrl" -ForegroundColor White
Write-Host "2. 按照验证清单逐项检查功能" -ForegroundColor White
Write-Host "3. 参考文档: admin-backend/前端功能驗證清單.md" -ForegroundColor White
Write-Host ""

