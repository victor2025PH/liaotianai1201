# 启动所有前端和后端服务，监控日志，并测试远程服务器的 session 文件
param(
    [switch]$MonitorLogs = $true
)

$ErrorActionPreference = "Continue"
$projectRoot = "E:\002-工作文件\重要程序\聊天AI群聊程序"

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  启动所有服务并测试远程 Session" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 检查并停止已运行的服务
Write-Host "[0/5] 检查并停止已运行的服务..." -ForegroundColor Yellow
$existingBackend = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" }
$existingFrontend = Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*vite*" -or $_.CommandLine -like "*next*" }

if ($existingBackend) {
    Write-Host "  停止已运行的后端服务..." -ForegroundColor Yellow
    $existingBackend | Stop-Process -Force
    Start-Sleep -Seconds 2
}

if ($existingFrontend) {
    Write-Host "  停止已运行的前端服务..." -ForegroundColor Yellow
    $existingFrontend | Stop-Process -Force
    Start-Sleep -Seconds 2
}

# 1. 启动后端服务
Write-Host "`n[1/5] 启动后端服务..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot\admin-backend
    $env:PYTHONPATH = (Get-Location).Parent.FullName
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 2>&1
} -Name "BackendService"

Write-Host "  后端服务已启动 (Job ID: $($backendJob.Id))" -ForegroundColor Green
Write-Host "  地址: http://localhost:8000" -ForegroundColor Gray
Write-Host "  API 文档: http://localhost:8000/docs" -ForegroundColor Gray

# 等待后端启动
Start-Sleep -Seconds 5

# 2. 启动前端服务 (saas-demo)
Write-Host "`n[2/5] 启动前端服务 (saas-demo)..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot\saas-demo
    npm run dev 2>&1
} -Name "FrontendService"

Write-Host "  前端服务已启动 (Job ID: $($frontendJob.Id))" -ForegroundColor Green
Write-Host "  地址: http://localhost:3000" -ForegroundColor Gray

# 3. 启动管理前端 (admin-frontend)
Write-Host "`n[3/5] 启动管理前端 (admin-frontend)..." -ForegroundColor Yellow
$adminFrontendJob = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot\admin-frontend
    npm run dev 2>&1
} -Name "AdminFrontendService"

Write-Host "  管理前端已启动 (Job ID: $($adminFrontendJob.Id))" -ForegroundColor Green
Write-Host "  地址: http://localhost:5173" -ForegroundColor Gray

# 等待前端启动
Start-Sleep -Seconds 8

# 4. 检查服务状态
Write-Host "`n[4/5] 检查服务状态..." -ForegroundColor Yellow
$backendOk = $false
$frontendOk = $false
$adminFrontendOk = $false

# 检查后端
for ($i = 0; $i -lt 5; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $backendOk = $true
            Write-Host "  ✓ 后端服务正常" -ForegroundColor Green
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $backendOk) {
    Write-Host "  ✗ 后端服务可能还在启动中..." -ForegroundColor Yellow
}

# 检查前端
for ($i = 0; $i -lt 5; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $frontendOk = $true
            Write-Host "  ✓ 前端服务正常" -ForegroundColor Green
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $frontendOk) {
    Write-Host "  ✗ 前端服务可能还在启动中..." -ForegroundColor Yellow
}

# 检查管理前端
for ($i = 0; $i -lt 5; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $adminFrontendOk = $true
            Write-Host "  ✓ 管理前端服务正常" -ForegroundColor Green
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $adminFrontendOk) {
    Write-Host "  ✗ 管理前端服务可能还在启动中..." -ForegroundColor Yellow
}

# 5. 测试远程服务器的 session 文件
Write-Host "`n[5/5] 测试远程服务器的 session 文件..." -ForegroundColor Yellow
$servers = @(
    @{IP="165.154.255.48"; Name="洛杉矶"; Pass="8iDcGrYb52Fxpzee"},
    @{IP="165.154.233.179"; Name="马尼拉"; Pass="8iDcGrYb52Fxpzee"},
    @{IP="165.154.254.99"; Name="worker-01"; Pass="Along2025!!!"}
)

foreach ($s in $servers) {
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host "测试: $($s.Name) ($($s.IP))" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    
    pwsh -ExecutionPolicy Bypass -Command "Import-Module Posh-SSH; `$pass = ConvertTo-SecureString '$($s.Pass)' -AsPlainText -Force; `$cred = New-Object System.Management.Automation.PSCredential('ubuntu', `$pass); `$s = New-SSHSession -ComputerName '$($s.IP)' -Credential `$cred -AcceptKey; Write-Host '1. 检查 session 文件...' -ForegroundColor Cyan; `$r1 = Invoke-SSHCommand -SessionId `$s.SessionId -Command 'find /home/ubuntu -name \"*.session\" -o -name \"*.session.*\" 2>/dev/null | head -10'; if (`$r1.Output) { Write-Host `$r1.Output -ForegroundColor Gray } else { Write-Host '  ✗ 未找到 session 文件' -ForegroundColor Red }; Write-Host ''; Write-Host '2. 检查 main.py 进程...' -ForegroundColor Cyan; `$r2 = Invoke-SSHCommand -SessionId `$s.SessionId -Command 'ps aux | grep \"[m]ain.py\"'; if (`$r2.Output) { Write-Host '  ✓ main.py 运行中' -ForegroundColor Green; Write-Host `$r2.Output -ForegroundColor Gray } else { Write-Host '  ✗ main.py 未运行' -ForegroundColor Red }; Write-Host ''; Write-Host '3. 检查日志（最后20行）...' -ForegroundColor Cyan; `$r3 = Invoke-SSHCommand -SessionId `$s.SessionId -Command 'tail -20 /home/ubuntu/logs/*.log 2>/dev/null | tail -20'; if (`$r3.Output) { Write-Host `$r3.Output -ForegroundColor Gray } else { Write-Host '  ✗ 未找到日志文件' -ForegroundColor Red }; Write-Host ''; Write-Host '4. 检查 Telegram 连接状态...' -ForegroundColor Cyan; `$r4 = Invoke-SSHCommand -SessionId `$s.SessionId -Command 'grep -i \"connected\|ready\|started\" /home/ubuntu/logs/*.log 2>/dev/null | tail -5'; if (`$r4.Output) { Write-Host '  ✓ 找到连接记录' -ForegroundColor Green; Write-Host `$r4.Output -ForegroundColor Gray } else { Write-Host '  ✗ 未找到连接记录' -ForegroundColor Red }; Remove-SSHSession -SessionId `$s.SessionId | Out-Null"
}

# 监控日志
if ($MonitorLogs) {
    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "  开始监控服务日志 (按 Ctrl+C 停止)" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    while ($true) {
        Clear-Host
        Write-Host "============================================================" -ForegroundColor Cyan
        Write-Host "  服务日志监控 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
        Write-Host "============================================================" -ForegroundColor Cyan
        Write-Host ""
        
        Write-Host "--- 后端服务日志 (最后10行) ---" -ForegroundColor Yellow
        $backendLogs = Receive-Job -Job $backendJob -Keep | Select-Object -Last 10
        if ($backendLogs) {
            Write-Host $backendLogs -ForegroundColor Gray
        } else {
            Write-Host "  (暂无日志)" -ForegroundColor DarkGray
        }
        
        Write-Host "`n--- 前端服务日志 (最后10行) ---" -ForegroundColor Yellow
        $frontendLogs = Receive-Job -Job $frontendJob -Keep | Select-Object -Last 10
        if ($frontendLogs) {
            Write-Host $frontendLogs -ForegroundColor Gray
        } else {
            Write-Host "  (暂无日志)" -ForegroundColor DarkGray
        }
        
        Write-Host "`n--- 管理前端日志 (最后10行) ---" -ForegroundColor Yellow
        $adminFrontendLogs = Receive-Job -Job $adminFrontendJob -Keep | Select-Object -Last 10
        if ($adminFrontendLogs) {
            Write-Host $adminFrontendLogs -ForegroundColor Gray
        } else {
            Write-Host "  (暂无日志)" -ForegroundColor DarkGray
        }
        
        Write-Host "`n按 Ctrl+C 停止监控..." -ForegroundColor Cyan
        Start-Sleep -Seconds 5
    }
} else {
    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "  服务已启动" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "后端服务: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "前端服务: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "管理前端: http://localhost:5173" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "查看日志: Receive-Job -Job BackendService,FrontendService,AdminFrontendService -Keep" -ForegroundColor Gray
    Write-Host "停止服务: Stop-Job -Job BackendService,FrontendService,AdminFrontendService" -ForegroundColor Gray
}

