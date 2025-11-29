# 持续监控并自动修复502错误直到成功

$Server = "ubuntu@165.154.233.55"
$MaxChecks = 20
$CheckInterval = 30

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "持续监控并自动修复502错误" -ForegroundColor Cyan
Write-Host "开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function Invoke-SSH {
    param($Cmd)
    try {
        $result = ssh $Server $Cmd 2>&1
        return $result -join "`n"
    } catch {
        return ""
    }
}

function Test-Website {
    param($Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

$checkCount = 0

while ($checkCount -lt $MaxChecks) {
    $checkCount++
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] 检查 #$checkCount" -ForegroundColor Cyan
    
    # 检查后端
    $backendHealth = Invoke-SSH "curl -s --max-time 5 http://localhost:8000/health 2>&1"
    if ($backendHealth -match "ok|status") {
        Write-Host "  ✅ 后端服务正常" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 后端服务异常，正在修复..." -ForegroundColor Red
        Invoke-SSH "cd ~/liaotian/admin-backend && source .venv/bin/activate && pkill -f 'uvicorn.*app.main:app' || true && sleep 2 && nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_fix.log 2>&1 &" | Out-Null
        Start-Sleep -Seconds 10
    }
    
    # 检查前端
    $frontendCheck = Invoke-SSH "curl -s --max-time 5 http://localhost:3000 2>&1 | head -1"
    if ($frontendCheck -match "html|DOCTYPE") {
        Write-Host "  ✅ 前端服务正常" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 前端服务异常，正在修复..." -ForegroundColor Red
        Invoke-SSH "cd ~/liaotian/saas-demo && pkill -f 'next.*dev\|node.*3000' || true && sleep 2 && nohup npm run dev > /tmp/frontend_fix.log 2>&1 &" | Out-Null
        Start-Sleep -Seconds 15
    }
    
    # 检查网站访问
    Write-Host "  检查网站访问..." -ForegroundColor Cyan
    if (Test-Website "http://aikz.usdt2026.cc/group-ai/accounts") {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "✅ 修复成功！网站可以正常访问！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "访问地址: http://aikz.usdt2026.cc/group-ai/accounts" -ForegroundColor Cyan
        exit 0
    } else {
        Write-Host "  ⚠️  网站仍然无法访问" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Start-Sleep -Seconds $CheckInterval
}

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "达到最大检查次数" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
