# 自动修复502错误并持续监控直到成功

$Server = "ubuntu@165.154.233.55"
$MaxAttempts = 5
$CheckInterval = 30

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "自动修复502错误并持续监控" -ForegroundColor Cyan
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

function Test-URL {
    param($Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    Write-Host "[尝试 $attempt/$MaxAttempts] 执行修复..." -ForegroundColor Yellow
    Write-Host ""
    
    # 1. 拉取最新代码并执行修复脚本
    Write-Host "步骤 1: 更新代码并执行修复脚本..." -ForegroundColor Cyan
    $result = Invoke-SSH "cd ~/liaotian && git pull origin master && chmod +x 完整修复502并验证.sh && bash 完整修复502并验证.sh 2>&1"
    Write-Host $result
    Write-Host ""
    
    # 2. 等待服务启动
    Write-Host "步骤 2: 等待服务启动（60秒）..." -ForegroundColor Cyan
    Start-Sleep -Seconds 60
    Write-Host ""
    
    # 3. 检查服务状态
    Write-Host "步骤 3: 检查服务状态..." -ForegroundColor Cyan
    
    $backendHealth = Invoke-SSH "curl -s http://localhost:8000/health 2>&1"
    if ($backendHealth -match "ok|status") {
        Write-Host "  ✅ 后端服务正常" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 后端服务异常: $backendHealth" -ForegroundColor Red
    }
    
    $frontendCheck = Invoke-SSH "curl -s http://localhost:3000 2>&1 | head -1"
    if ($frontendCheck -match "html|DOCTYPE") {
        Write-Host "  ✅ 前端服务正常" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 前端服务异常" -ForegroundColor Red
    }
    
    $processes = Invoke-SSH "ps aux | grep -E 'uvicorn|next.*dev' | grep -v grep"
    if ($processes) {
        Write-Host "  ✅ 服务进程正在运行" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 未发现服务进程" -ForegroundColor Red
    }
    Write-Host ""
    
    # 4. 检查浏览器访问
    Write-Host "步骤 4: 检查浏览器访问..." -ForegroundColor Cyan
    Start-Sleep -Seconds 5
    
    if (Test-URL "http://aikz.usdt2026.cc/group-ai/accounts") {
        Write-Host "  ✅ 网站可以访问！" -ForegroundColor Green
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "修复成功！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "访问地址: http://aikz.usdt2026.cc/group-ai/accounts" -ForegroundColor Cyan
        exit 0
    } else {
        Write-Host "  ❌ 网站仍然无法访问" -ForegroundColor Red
        Write-Host ""
        
        if ($attempt -lt $MaxAttempts) {
            Write-Host "准备重试..." -ForegroundColor Yellow
            Start-Sleep -Seconds 10
        }
    }
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Red
Write-Host "达到最大尝试次数，修复失败" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""

# 显示诊断信息
Write-Host "诊断信息:" -ForegroundColor Yellow
$diag = Invoke-SSH "echo '后端健康检查:' && curl -s http://localhost:8000/health 2>&1 && echo '' && echo '前端检查:' && curl -s http://localhost:3000 2>&1 | head -3 && echo '' && echo '进程:' && ps aux | grep -E 'uvicorn|next' | grep -v grep && echo '' && echo 'Nginx状态:' && sudo systemctl status nginx --no-pager | head -5"
Write-Host $diag

exit 1
