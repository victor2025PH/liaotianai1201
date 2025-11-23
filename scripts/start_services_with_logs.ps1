# 在 Cursor 终端中启动服务并实时显示日志
# 使用日志文件 + tail 方式，确保日志实时显示

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoMonitor
)

$ErrorActionPreference = "Stop"

# 项目根目录
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "admin-backend"
$frontendDir = Join-Path $projectRoot "saas-demo"
$logsDir = Join-Path $projectRoot "logs"

# 创建日志目录
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

$backendLogFile = Join-Path $logsDir "backend.log"
$frontendLogFile = Join-Path $logsDir "frontend.log"

Write-Host "`n🚀 在 Cursor 终端中启动服务（带日志监控）..." -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray

# 停止现有服务
Write-Host "`n1️⃣ 停止现有服务..." -ForegroundColor Yellow
Get-Process | Where-Object {
    ($_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*") -and
    ($_.Path -like "*$projectRoot*")
} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 清理旧日志
if (Test-Path $backendLogFile) { Remove-Item $backendLogFile -Force -ErrorAction SilentlyContinue }
if (Test-Path $frontendLogFile) { Remove-Item $frontendLogFile -Force -ErrorAction SilentlyContinue }

# 启动后端服务
if (-not $FrontendOnly) {
    Write-Host "`n2️⃣ 启动后端服务..." -ForegroundColor Yellow
    
    $backendProcess = Start-Process -FilePath "python" -ArgumentList @(
        "-m", "uvicorn", "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ) -WorkingDirectory $backendDir -PassThru -NoNewWindow -RedirectStandardOutput $backendLogFile -RedirectStandardError $backendLogFile
    
    Write-Host "   后端服务已启动（PID: $($backendProcess.Id)）" -ForegroundColor Green
    Write-Host "   日志文件: $backendLogFile" -ForegroundColor Gray
}

# 启动前端服务
if (-not $BackendOnly) {
    Write-Host "`n3️⃣ 启动前端服务..." -ForegroundColor Yellow
    
    $frontendProcess = Start-Process -FilePath "npm" -ArgumentList @("run", "dev") -WorkingDirectory $frontendDir -PassThru -NoNewWindow -RedirectStandardOutput $frontendLogFile -RedirectStandardError $frontendLogFile
    
    Write-Host "   前端服务已启动（PID: $($frontendProcess.Id)）" -ForegroundColor Green
    Write-Host "   日志文件: $frontendLogFile" -ForegroundColor Gray
}

# 等待服务启动
Write-Host "`n⏳ 等待服务启动（10秒）..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 检查服务状态
Write-Host "`n4️⃣ 检查服务状态..." -ForegroundColor Yellow
if (-not $FrontendOnly) {
    try {
        $backendHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "   后端: ✅ $($backendHealth.status)" -ForegroundColor Green
    } catch {
        Write-Host "   后端: ❌ $($_.Exception.Message)" -ForegroundColor Red
    }
}

if (-not $BackendOnly) {
    try {
        $frontendCheck = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "   前端: ✅ HTTP $($frontendCheck.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "   前端: ❌ $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 实时监控日志
if (-not $NoMonitor) {
    Write-Host "`n" -NoNewline
    Write-Host "=" * 80 -ForegroundColor Gray
    Write-Host "📊 实时日志监控（按 Ctrl+C 停止）" -ForegroundColor Cyan
    Write-Host "=" * 80 -ForegroundColor Gray
    Write-Host ""
    
    $backendReader = $null
    $frontendReader = $null
    
    try {
        # 打开日志文件用于读取
        if (-not $FrontendOnly -and (Test-Path $backendLogFile)) {
            $backendStream = [System.IO.File]::Open($backendLogFile, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
            $backendReader = New-Object System.IO.StreamReader($backendStream)
            $backendReader.BaseStream.Seek(0, [System.IO.SeekOrigin]::End) | Out-Null
        }
        
        if (-not $BackendOnly -and (Test-Path $frontendLogFile)) {
            $frontendStream = [System.IO.File]::Open($frontendLogFile, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
            $frontendReader = New-Object System.IO.StreamReader($frontendStream)
            $frontendReader.BaseStream.Seek(0, [System.IO.SeekOrigin]::End) | Out-Null
        }
        
        while ($true) {
            # 读取后端日志
            if ($backendReader) {
                $backendLine = $backendReader.ReadLine()
                if ($backendLine) {
                    $timestamp = Get-Date -Format "HH:mm:ss"
                    Write-Host "[$timestamp] [后端] " -ForegroundColor Yellow -NoNewline
                    Write-Host $backendLine
                }
            }
            
            # 读取前端日志
            if ($frontendReader) {
                $frontendLine = $frontendReader.ReadLine()
                if ($frontendLine) {
                    $timestamp = Get-Date -Format "HH:mm:ss"
                    Write-Host "[$timestamp] [前端] " -ForegroundColor Magenta -NoNewline
                    Write-Host $frontendLine
                }
            }
            
            Start-Sleep -Milliseconds 200
        }
    } catch {
        Write-Host "`n⚠️  监控中断: $($_.Exception.Message)" -ForegroundColor Yellow
    } finally {
        if ($backendReader) { $backendReader.Close() }
        if ($frontendReader) { $frontendReader.Close() }
        
        Write-Host "`n🛑 正在停止服务..." -ForegroundColor Yellow
        if ($backendProcess -and -not $backendProcess.HasExited) {
            Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
        }
        if ($frontendProcess -and -not $frontendProcess.HasExited) {
            Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
        }
        Write-Host "✅ 服务已停止" -ForegroundColor Green
    }
} else {
    Write-Host "`n💡 服务已在后台运行，日志文件：" -ForegroundColor Cyan
    if (-not $FrontendOnly) { Write-Host "   后端: $backendLogFile" -ForegroundColor White }
    if (-not $BackendOnly) { Write-Host "   前端: $frontendLogFile" -ForegroundColor White }
    Write-Host "`n使用以下命令查看日志：" -ForegroundColor Yellow
    Write-Host "   Get-Content $backendLogFile -Wait -Tail 50" -ForegroundColor White
    Write-Host "   Get-Content $frontendLogFile -Wait -Tail 50" -ForegroundColor White
}

