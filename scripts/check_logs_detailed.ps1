# 检查所有服务器的详细日志
$ErrorActionPreference = "Continue"
Import-Module Posh-SSH

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  检查所有服务器的详细日志" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$servers = @(
    @{IP="165.154.255.48"; Name="洛杉矶"; Pass="8iDcGrYb52Fxpzee"},
    @{IP="165.154.233.179"; Name="马尼拉"; Pass="8iDcGrYb52Fxpzee"},
    @{IP="165.154.254.99"; Name="worker-01"; Pass="Along2025!!!"}
)

foreach ($s in $servers) {
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host "$($s.Name) ($($s.IP))" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    
    try {
        $pass = ConvertTo-SecureString $s.Pass -AsPlainText -Force
        $cred = New-Object System.Management.Automation.PSCredential("ubuntu", $pass)
        $session = New-SSHSession -ComputerName $s.IP -Credential $cred -AcceptKey -ErrorAction Stop
        
        Write-Host "✓ SSH 连接成功" -ForegroundColor Green
        Write-Host ""
        
        # 1. 检查所有进程
        Write-Host "1. 运行中的进程..." -ForegroundColor Cyan
        $r1 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ps aux | grep '[m]ain.py'"
        if ($r1.Output) {
            $processCount = ($r1.Output -split "`n").Count
            Write-Host "  ✓ $processCount 个进程正在运行" -ForegroundColor Green
            Write-Host $r1.Output -ForegroundColor Gray
        } else {
            Write-Host "  ✗ 没有运行中的进程" -ForegroundColor Red
        }
        Write-Host ""
        
        # 2. 检查所有日志文件
        Write-Host "2. 日志文件内容..." -ForegroundColor Cyan
        $r2 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ls /home/ubuntu/logs/main_*.log 2>/dev/null"
        if ($r2.Output) {
            $logFiles = ($r2.Output -split "`n") | Where-Object { $_.Trim() -ne "" }
            foreach ($logFile in $logFiles) {
                $logFile = $logFile.Trim()
                $accountName = [System.IO.Path]::GetFileNameWithoutExtension($logFile) -replace "main_", ""
                Write-Host "  账号: $accountName" -ForegroundColor Yellow
                $r3 = Invoke-SSHCommand -SessionId $session.SessionId -Command "tail -50 '$logFile' 2>/dev/null"
                if ($r3.Output -and $r3.Output.Trim() -ne "") {
                    Write-Host $r3.Output -ForegroundColor Gray
                } else {
                    Write-Host "    (日志为空)" -ForegroundColor DarkGray
                }
                Write-Host ""
            }
        } else {
            Write-Host "  (未找到日志文件)" -ForegroundColor DarkGray
        }
        Write-Host ""
        
        Remove-SSHSession -SessionId $session.SessionId | Out-Null
        
    } catch {
        Write-Host "✗ SSH 连接失败: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  检查完成" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

