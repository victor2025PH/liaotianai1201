# 深度搜索所有可能的 Session 文件
$ErrorActionPreference = "Continue"
Import-Module Posh-SSH

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  深度搜索所有可能的 Session 文件" -ForegroundColor Cyan
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
        
        # 1. 在整个 /home/ubuntu 目录下深度搜索
        Write-Host "1. 在整个 /home/ubuntu 目录下深度搜索..." -ForegroundColor Cyan
        $r1 = Invoke-SSHCommand -SessionId $session.SessionId -Command "find /home/ubuntu -type f -name '*.session' 2>/dev/null | xargs ls -lh 2>/dev/null | awk '{print `$9, `$5}'"
        if ($r1.Output) {
            Write-Host "  找到的 Session 文件:" -ForegroundColor Green
            Write-Host $r1.Output -ForegroundColor Gray
        } else {
            Write-Host "  (未找到)" -ForegroundColor DarkGray
        }
        Write-Host ""
        
        # 2. 检查其他常见位置
        Write-Host "2. 检查其他常见位置..." -ForegroundColor Cyan
        $otherPaths = @(
            "/root/sessions",
            "/root",
            "/tmp",
            "/var/tmp",
            "/opt",
            "/usr/local"
        )
        
        foreach ($path in $otherPaths) {
            $r2 = Invoke-SSHCommand -SessionId $session.SessionId -Command "find $path -type f -name '*.session' 2>/dev/null | head -10"
            if ($r2.Output -and $r2.Output.Trim() -ne "") {
                Write-Host "  ✓ 在 $path 找到:" -ForegroundColor Green
                Write-Host $r2.Output -ForegroundColor Gray
            }
        }
        Write-Host ""
        
        # 3. 检查是否有其他格式的 Session 文件（如 .session-journal）
        Write-Host "3. 检查 Session 相关文件（包括 journal 文件）..." -ForegroundColor Cyan
        $r3 = Invoke-SSHCommand -SessionId $session.SessionId -Command "find /home/ubuntu -type f \( -name '*.session*' -o -name '*session*' \) 2>/dev/null | head -20"
        if ($r3.Output) {
            Write-Host "  找到的 Session 相关文件:" -ForegroundColor Green
            Write-Host $r3.Output -ForegroundColor Gray
        }
        Write-Host ""
        
        # 4. 列出所有目录，看看是否有其他可能的 Session 存储位置
        Write-Host "4. 列出 /home/ubuntu 下的所有目录..." -ForegroundColor Cyan
        $r4 = Invoke-SSHCommand -SessionId $session.SessionId -Command "find /home/ubuntu -type d -maxdepth 3 2>/dev/null | sort"
        if ($r4.Output) {
            Write-Host "  目录列表:" -ForegroundColor Green
            Write-Host $r4.Output -ForegroundColor Gray
        }
        Write-Host ""
        
        # 5. 检查是否有备份或压缩的 Session 文件
        Write-Host "5. 检查备份或压缩的 Session 文件..." -ForegroundColor Cyan
        $r5 = Invoke-SSHCommand -SessionId $session.SessionId -Command "find /home/ubuntu -type f \( -name '*.session.gz' -o -name '*.session.zip' -o -name '*.session.bak' -o -name '*session*.tar*' \) 2>/dev/null"
        if ($r5.Output) {
            Write-Host "  找到备份文件:" -ForegroundColor Green
            Write-Host $r5.Output -ForegroundColor Gray
        } else {
            Write-Host "  (未找到备份文件)" -ForegroundColor DarkGray
        }
        Write-Host ""
        
        Remove-SSHSession -SessionId $session.SessionId | Out-Null
        
    } catch {
        Write-Host "✗ SSH 连接失败: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  搜索完成" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "如果找到了其他位置的 Session 文件，请告诉我具体路径" -ForegroundColor Yellow
Write-Host "我可以创建脚本使用这些 Session 文件" -ForegroundColor Yellow

