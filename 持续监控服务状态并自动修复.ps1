# 持续监控服务状态并自动修复

$Server = "ubuntu@165.154.233.55"
$MaxChecks = 10
$CheckInterval = 30

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "持续监控服务状态并自动修复" -ForegroundColor Cyan
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

for ($check = 1; $check -le $MaxChecks; $check++) {
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] 检查 #$check/$MaxChecks" -ForegroundColor Cyan
    Write-Host ""
    
    # 检查后端
    Write-Host "  检查后端服务..." -ForegroundColor Gray
    $backendHealth = Invoke-SSH "curl -s --max-time 5 http://localhost:8000/health 2>&1"
    if ($backendHealth -match "ok|status") {
        Write-Host "    ✅ 后端服务正常" -ForegroundColor Green
        $backendOk = $true
    } else {
        Write-Host "    ❌ 后端服务异常: $backendHealth" -ForegroundColor Red
        $backendOk = $false
    }
    
    # 检查前端
    Write-Host "  检查前端服务..." -ForegroundColor Gray
    $frontendCheck = Invoke-SSH "curl -s --max-time 5 http://localhost:3000 2>&1 | head -1"
    if ($frontendCheck -match "html|DOCTYPE") {
        Write-Host "    ✅ 前端服务正常" -ForegroundColor Green
        $frontendOk = $true
    } else {
        Write-Host "    ❌ 前端服务未运行" -ForegroundColor Red
        $frontendOk = $false
    }
    
    # 检查进程
    Write-Host "  检查服务进程..." -ForegroundColor Gray
    $processes = Invoke-SSH "ps aux | grep -E 'uvicorn.*8000|next.*dev|node.*3000' | grep -v grep"
    if ($processes) {
        Write-Host "    ✅ 发现服务进程" -ForegroundColor Green
        $processes -split "`n" | ForEach-Object {
            if ($_.Trim()) {
                Write-Host "      $_" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "    ⚠️  未发现服务进程" -ForegroundColor Yellow
    }
    
    Write-Host ""
    
    # 如果需要修复
    if (-not $backendOk -or -not $frontendOk) {
        Write-Host "  🔧 执行自动修复..." -ForegroundColor Yellow
        
        $fixResult = Invoke-SSH "cd ~/liaotian && bash 自动诊断并修复-基于日志分析.sh 2>&1 | tail -30"
        Write-Host $fixResult
        Write-Host ""
        
        Write-Host "  等待服务启动（30秒）..." -ForegroundColor Gray
        Start-Sleep -Seconds 30
        Write-Host ""
    }
    
    # 检查网站访问
    Write-Host "  检查网站访问..." -ForegroundColor Gray
    if (Test-Website "http://aikz.usdt2026.cc/group-ai/accounts") {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "✅ 修复成功！网站可以正常访问！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "访问地址: http://aikz.usdt2026.cc/group-ai/accounts" -ForegroundColor Cyan
        exit 0
    } else {
        Write-Host "    ⚠️  网站仍然无法访问，继续监控..." -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "  等待 $CheckInterval 秒后进行下一次检查..." -ForegroundColor Gray
    Write-Host ""
    
    if ($check -lt $MaxChecks) {
        Start-Sleep -Seconds $CheckInterval
    }
}

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "达到最大检查次数" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
