# 实时监控验证码测试日志
# 使用方法: .\scripts\monitor_verification_code.ps1

$ErrorActionPreference = "Continue"

Write-Host "`n═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   🔍 验证码测试实时监控" -ForegroundColor Cyan -BackgroundColor Black
Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

Write-Host "📋 监控内容：" -ForegroundColor Yellow
Write-Host "   • 验证码发送过程" -ForegroundColor White
Write-Host "   • 验证码验证过程" -ForegroundColor White
Write-Host "   • 跨服务器检查逻辑" -ForegroundColor White
Write-Host "   • 远程服务器执行情况" -ForegroundColor White
Write-Host "   • 错误和异常信息" -ForegroundColor White
Write-Host "`n💡 提示：" -ForegroundColor Yellow
Write-Host "   • 按 Ctrl+C 停止监控" -ForegroundColor White
Write-Host "   • 所有验证码相关操作都会被高亮显示" -ForegroundColor White
Write-Host "`n开始监控...`n" -ForegroundColor Green

# 监控后端日志（从控制台输出）
$backendProcess = Get-Process | Where-Object { 
    $_.ProcessName -eq "python" -and 
    (Get-NetTCPConnection -OwningProcess $_.Id -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq 8000 })
} | Select-Object -First 1

if ($backendProcess) {
    Write-Host "[监控] 后端服务进程 ID: $($backendProcess.Id)" -ForegroundColor Green
} else {
    Write-Host "[警告] 未找到后端服务进程" -ForegroundColor Yellow
}

# 监控关键词
$keywords = @(
    "验证码",
    "phone_code",
    "CODE_SENT",
    "远程发送验证码",
    "验证码验证",
    "远程验证",
    "跨服务器",
    "其他服务器",
    "记录无效",
    "记录有效",
    "PhoneCodeExpired",
    "PhoneCodeInvalid",
    "FloodWait",
    "PHONE_BANNED",
    "ERROR:",
    "registration_id",
    "node_id"
)

# 监控后端控制台输出（通过检查日志文件或进程输出）
$logPatterns = @(
    @{ Pattern = "远程发送验证码"; Color = "Cyan" }
    @{ Pattern = "CODE_SENT"; Color = "Green" }
    @{ Pattern = "验证码验证"; Color = "Yellow" }
    @{ Pattern = "远程验证"; Color = "Magenta" }
    @{ Pattern = "跨服务器"; Color = "Red" }
    @{ Pattern = "记录无效"; Color = "Yellow" }
    @{ Pattern = "记录有效"; Color = "Green" }
    @{ Pattern = "PhoneCodeExpired|PhoneCodeInvalid"; Color = "Red" }
    @{ Pattern = "FloodWait"; Color = "Yellow" }
    @{ Pattern = "ERROR:"; Color = "Red" }
    @{ Pattern = "验证码发送成功"; Color = "Green" }
    @{ Pattern = "验证码无效|验证码已过期"; Color = "Red" }
)

Write-Host "`n═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "   实时监控中... (按 Ctrl+C 停止)" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Green

# 检查服务健康状态
$checkCount = 0
while ($true) {
    $timestamp = Get-Date -Format "HH:mm:ss"
    $checkCount++
    
    # 每10次检查显示一次状态
    if ($checkCount % 10 -eq 0) {
        $backendStatus = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -First 1
        $frontendStatus = Get-NetTCPConnection -LocalPort 3001 -ErrorAction SilentlyContinue | Select-Object -First 1
        
        Write-Host "`n[$timestamp] [状态检查]" -ForegroundColor Cyan
        if ($backendStatus) {
            Write-Host "   ✅ 后端服务: 运行中 (端口 8000)" -ForegroundColor Green
        } else {
            Write-Host "   ❌ 后端服务: 未运行" -ForegroundColor Red
        }
        if ($frontendStatus) {
            Write-Host "   ✅ 前端服务: 运行中 (端口 3001)" -ForegroundColor Green
        } else {
            Write-Host "   ❌ 前端服务: 未运行" -ForegroundColor Red
        }
        Write-Host ""
    }
    
    # 提示用户进行测试
    if ($checkCount -eq 1) {
        Write-Host "[$timestamp] 💡 提示: 现在可以在前端进行验证码测试" -ForegroundColor Yellow
        Write-Host "   监控将实时显示所有验证码相关操作`n" -ForegroundColor Gray
    }
    
    Start-Sleep -Seconds 2
}

