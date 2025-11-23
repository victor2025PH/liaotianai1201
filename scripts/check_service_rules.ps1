# 检查服务启动规则合规性
# 此脚本用于验证服务启动命令是否符合 .cursor/rules/always-run-in-cursor-terminal.mdc 规则

param(
    [Parameter(Mandatory=$false)]
    [string]$CommandToCheck = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$CheckRunningServices
)

$ErrorActionPreference = "Continue"

# 规则文件路径
$rulesFile = Join-Path $PSScriptRoot "..\.cursor\rules\always-run-in-cursor-terminal.mdc"

Write-Host "`n═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   服务启动规则合规性检查" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

# 检查规则文件是否存在
if (-not (Test-Path $rulesFile)) {
    Write-Host "❌ 错误: 规则文件不存在: $rulesFile" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 规则文件存在: $rulesFile" -ForegroundColor Green

# 禁止的命令模式
$forbiddenPatterns = @(
    "Start-Process.*-WindowStyle",
    "Start-Process.*powershell",
    "Start-Process.*-NoExit",
    "Start-Process.*-WindowStyle\s+(Hidden|Minimized|Normal)",
    "Start-Job.*-ScriptBlock"
)

# 检查命令
if ($CommandToCheck) {
    Write-Host "`n检查命令: $CommandToCheck" -ForegroundColor Yellow
    
    $violations = @()
    foreach ($pattern in $forbiddenPatterns) {
        if ($CommandToCheck -match $pattern) {
            $violations += "违反规则: 使用了禁止的模式 '$pattern'"
        }
    }
    
    if ($violations.Count -gt 0) {
        Write-Host "`n❌ 命令违反规则！" -ForegroundColor Red
        foreach ($violation in $violations) {
            Write-Host "   $violation" -ForegroundColor Red
        }
        Write-Host "`n建议使用以下方式之一：" -ForegroundColor Yellow
        Write-Host "   1. .\scripts\start_backend.ps1" -ForegroundColor Green
        Write-Host "   2. .\scripts\start_frontend.ps1" -ForegroundColor Green
        Write-Host "   3. 直接在终端中运行命令（不使用 Start-Process）" -ForegroundColor Green
        exit 1
    } else {
        Write-Host "✅ 命令符合规则" -ForegroundColor Green
    }
}

# 检查正在运行的服务
if ($CheckRunningServices) {
    Write-Host "`n检查正在运行的服务..." -ForegroundColor Yellow
    
    # 检查是否有外部窗口中的服务
    $externalProcesses = Get-Process | Where-Object {
        ($_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*" -or $_.ProcessName -like "*uvicorn*" -or $_.ProcessName -like "*next*") -and
        $_.MainWindowTitle -ne ""
    }
    
    if ($externalProcesses.Count -gt 0) {
        Write-Host "`n⚠️  发现外部窗口中的服务进程：" -ForegroundColor Yellow
        foreach ($proc in $externalProcesses) {
            Write-Host "   - $($proc.ProcessName) (PID: $($proc.Id), 窗口: $($proc.MainWindowTitle))" -ForegroundColor Yellow
        }
        Write-Host "`n建议：停止这些进程，在 Cursor 终端中重新启动" -ForegroundColor Yellow
    } else {
        Write-Host "✅ 未发现外部窗口中的服务进程" -ForegroundColor Green
    }
    
    # 检查端口占用
    Write-Host "`n检查端口占用情况..." -ForegroundColor Yellow
    $ports = @(8000, 3000, 3001)
    foreach ($port in $ports) {
        $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($connection) {
            $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
            if ($process) {
                $isExternal = $process.MainWindowTitle -ne ""
                $status = if ($isExternal) { "❌ 外部窗口" } else { "✅ Cursor 终端" }
                Write-Host "   端口 $port : $status - $($process.ProcessName) (PID: $($process.Id))" -ForegroundColor $(if ($isExternal) { "Yellow" } else { "Green" })
            }
        } else {
            Write-Host "   端口 $port : 未使用" -ForegroundColor Gray
        }
    }
}

Write-Host "`n═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   检查完成" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

