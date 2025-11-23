# 通过 SSH 修复 Query 导入并启动服务
param(
    [string]$ServerIP,
    [string]$Username = "ubuntu",
    [string]$Password,
    [string]$ServerName
)

Import-Module Posh-SSH

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "修复: $ServerName ($ServerIP)" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

$pass = ConvertTo-SecureString $Password -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential($Username, $pass)
$session = New-SSHSession -ComputerName $ServerIP -Credential $cred -AcceptKey

try {
    Write-Host "步骤 1: 修复 Query 导入..." -ForegroundColor Cyan
    $fixCmd = @'
cd /home/ubuntu/admin-backend && python3 << 'PYEOF'
f = open("app/main.py", "r")
lines = f.readlines()
f.close()
if "Query" not in lines[0]:
    lines[0] = lines[0].replace("from fastapi import FastAPI, Request", "from fastapi import FastAPI, Request, Query")
    f = open("app/main.py", "w")
    f.writelines(lines)
    f.close()
    print("Fixed")
else:
    print("Already fixed")
PYEOF
'@
    $r1 = Invoke-SSHCommand -SessionId $session.SessionId -Command $fixCmd
    Write-Host $r1.Output
    
    Write-Host "`n步骤 2: 验证修复..." -ForegroundColor Cyan
    $r2 = Invoke-SSHCommand -SessionId $session.SessionId -Command "head -1 /home/ubuntu/admin-backend/app/main.py"
    Write-Host $r2.Output
    
    if ($r2.Output -match "Query") {
        Write-Host "  ✓ Query 已修复" -ForegroundColor Green
        
        Write-Host "`n步骤 3: 停止旧服务..." -ForegroundColor Cyan
        $r3 = Invoke-SSHCommand -SessionId $session.SessionId -Command "pkill -f uvicorn; sleep 2"
        
        Write-Host "步骤 4: 启动服务..." -ForegroundColor Cyan
        $r4 = Invoke-SSHCommand -SessionId $session.SessionId -Command "cd /home/ubuntu/admin-backend && export PATH=`$HOME/.local/bin:`$PATH && nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &"
        Write-Host "  等待服务启动..." -ForegroundColor Yellow
        Start-Sleep -Seconds 12
        
        Write-Host "`n步骤 5: 检查服务状态..." -ForegroundColor Cyan
        $r5 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ps aux | grep uvicorn | grep -v grep"
        if ($r5.Output) {
            Write-Host "  ✓ 服务运行中" -ForegroundColor Green
            Write-Host $r5.Output -ForegroundColor Gray
        } else {
            Write-Host "  ✗ 服务未运行" -ForegroundColor Red
            $r6 = Invoke-SSHCommand -SessionId $session.SessionId -Command "tail -25 /home/ubuntu/logs/backend.log 2>/dev/null"
            Write-Host $r6.Output -ForegroundColor Red
        }
        
        Write-Host "`n步骤 6: 检查端口..." -ForegroundColor Cyan
        $r7 = Invoke-SSHCommand -SessionId $session.SessionId -Command "ss -tlnp 2>/dev/null | grep :8000"
        if ($r7.Output) {
            Write-Host "  ✓ 端口 8000 监听中" -ForegroundColor Green
        } else {
            Write-Host "  ✗ 端口未监听" -ForegroundColor Red
        }
        
        Write-Host "`n步骤 7: 测试健康检查..." -ForegroundColor Cyan
        $r8 = Invoke-SSHCommand -SessionId $session.SessionId -Command "curl -s http://localhost:8000/health 2>/dev/null | head -10"
        if ($r8.Output -match "status|healthy") {
            Write-Host "  ✓ 健康检查通过" -ForegroundColor Green
            Write-Host $r8.Output -ForegroundColor Gray
        } else {
            Write-Host "  ✗ 健康检查失败" -ForegroundColor Red
            if ($r8.Output) {
                Write-Host $r8.Output -ForegroundColor Red
            }
        }
    } else {
        Write-Host "  ✗ Query 未修复" -ForegroundColor Red
    }
} finally {
    Remove-SSHSession -SessionId $session.SessionId | Out-Null
}

