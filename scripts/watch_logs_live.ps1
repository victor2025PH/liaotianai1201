# 实时监控服务日志
# 使用方法: .\scripts\watch_logs_live.ps1

param(
    [int]$Interval = 2  # 检查间隔（秒）
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$logsDir = Join-Path $projectRoot "logs"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  实时监控服务日志" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "监控目录: $logsDir" -ForegroundColor Gray
Write-Host "检查间隔: $Interval 秒" -ForegroundColor Gray
Write-Host "按 Ctrl+C 停止监控" -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path $logsDir)) {
    Write-Host "[错误] 日志目录不存在: $logsDir" -ForegroundColor Red
    exit 1
}

# 获取最新的日志文件
$backendLog = Get-ChildItem $logsDir -Filter "backend_*.log" -ErrorAction SilentlyContinue | 
    Sort-Object LastWriteTime -Descending | Select-Object -First 1

$frontendLog = Get-ChildItem $logsDir -Filter "frontend_*.log" -ErrorAction SilentlyContinue | 
    Sort-Object LastWriteTime -Descending | Select-Object -First 1

if (-not $backendLog -and -not $frontendLog) {
    Write-Host "[警告] 未找到日志文件，等待服务启动..." -ForegroundColor Yellow
}

$lastBackendSize = 0
$lastFrontendSize = 0
$errorCount = 0

try {
    while ($true) {
        $timestamp = Get-Date -Format "HH:mm:ss"
        
        # 检查后端日志
        if ($backendLog -and (Test-Path $backendLog.FullName)) {
            $currentSize = (Get-Item $backendLog.FullName).Length
            if ($currentSize -gt $lastBackendSize) {
                $newContent = Get-Content $backendLog.FullName -Tail 20 -ErrorAction SilentlyContinue
                if ($newContent) {
                    $newLines = $newContent | Select-Object -Skip ([Math]::Max(0, ($newContent.Count - 10)))
                    foreach ($line in $newLines) {
                        if ($line -match "(?i)(error|exception|traceback|failed|失败|AttributeError|ImportError)") {
                            Write-Host "[$timestamp] [后端] ❌ $line" -ForegroundColor Red
                            $errorCount++
                        } elseif ($line -match "(?i)(started|running|startup complete|uvicorn running)") {
                            Write-Host "[$timestamp] [后端] ✅ $line" -ForegroundColor Green
                        } elseif ($line -match "(?i)(warning|warn)") {
                            Write-Host "[$timestamp] [后端] ⚠️  $line" -ForegroundColor Yellow
                        }
                    }
                }
                $lastBackendSize = $currentSize
            }
        }
        
        # 检查前端日志
        if ($frontendLog -and (Test-Path $frontendLog.FullName)) {
            $currentSize = (Get-Item $frontendLog.FullName).Length
            if ($currentSize -gt $lastFrontendSize) {
                $newContent = Get-Content $frontendLog.FullName -Tail 20 -ErrorAction SilentlyContinue
                if ($newContent) {
                    $newLines = $newContent | Select-Object -Skip ([Math]::Max(0, ($newContent.Count - 10)))
                    foreach ($line in $newLines) {
                        if ($line -match "(?i)(error|failed|失败|cannot|missing|not found|compilation error)") {
                            Write-Host "[$timestamp] [前端] ❌ $line" -ForegroundColor Red
                            $errorCount++
                        } elseif ($line -match "(?i)(ready|compiled|Local:|localhost)") {
                            Write-Host "[$timestamp] [前端] ✅ $line" -ForegroundColor Green
                        } elseif ($line -match "(?i)(warning|warn)") {
                            Write-Host "[$timestamp] [前端] ⚠️  $line" -ForegroundColor Yellow
                        }
                    }
                }
                $lastFrontendSize = $currentSize
            }
        }
        
        # 检查服务健康状态
        if ($errorCount -gt 0 -and ($errorCount % 10 -eq 0)) {
            Write-Host "`n[$timestamp] [统计] 已检测到 $errorCount 个错误/警告" -ForegroundColor Yellow
        }
        
        Start-Sleep -Seconds $Interval
    }
} catch {
    Write-Host "`n监控中断: $_" -ForegroundColor Red
} finally {
    Write-Host "`n监控已停止" -ForegroundColor Yellow
    Write-Host "总错误数: $errorCount" -ForegroundColor $(if ($errorCount -eq 0) { "Green" } else { "Red" })
}

