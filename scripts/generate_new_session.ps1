# 重新生成 Session 文件
$ErrorActionPreference = "Continue"
Import-Module Posh-SSH

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  重新生成 Session 文件" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 真实的 API 凭证
$API_ID = "24782266"
$API_HASH = "48ccfcd14b237d4f6753c122f6a798606"

$servers = @(
    @{IP="165.154.255.48"; Name="洛杉矶"; Pass="8iDcGrYb52Fxpzee"},
    @{IP="165.154.233.179"; Name="马尼拉"; Pass="8iDcGrYb52Fxpzee"},
    @{IP="165.154.254.99"; Name="worker-01"; Pass="Along2025!!!"}
)

Write-Host "⚠️  注意: 重新生成 Session 需要交互式输入" -ForegroundColor Yellow
Write-Host "   这需要在服务器上手动执行，或使用支持交互的 SSH 客户端" -ForegroundColor Yellow
Write-Host ""

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
        
        # 1. 检查是否有 login.py 脚本
        Write-Host "1. 检查登录脚本..." -ForegroundColor Cyan
        $r1 = Invoke-SSHCommand -SessionId $session.SessionId -Command "test -f /home/ubuntu/scripts/login.py && echo exists || echo not exists"
        if ($r1.Output -match "not exists") {
            Write-Host "  ✗ login.py 不存在" -ForegroundColor Red
            Write-Host "  创建登录脚本..." -ForegroundColor Yellow
            
            # 创建简单的登录脚本
            $loginScript = @'
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, AuthKeyUnregistered

API_ID = 24782266
API_HASH = "48ccfcd14b237d4f6753c122f6a798606"

async def generate_session():
    print("=" * 50)
    print("Telegram Session 生成工具")
    print("=" * 50)
    print()
    
    phone = input("请输入手机号码（带国家代码，如 +1234567890）: ")
    session_name = input("请输入 Session 名称（默认: my_session）: ").strip() or "my_session"
    
    app = Client(
        session_name,
        api_id=API_ID,
        api_hash=API_HASH,
        workdir="sessions",
    )
    
    await app.connect()
    
    try:
        me = await app.get_me()
        if me:
            print(f"\n✓ 已授权: {me.first_name} (@{me.username or 'N/A'})")
            await app.disconnect()
            print(f"✓ Session 文件已保存: sessions/{session_name}.session")
            return True
    except AuthKeyUnregistered:
        pass
    
    try:
        sent_code = await app.send_code(phone)
        print(f"\n✓ 验证码已发送到 {phone}")
        code = input("请输入验证码: ").strip()
        
        try:
            await app.sign_in(phone, sent_code.phone_code_hash, code)
        except SessionPasswordNeeded:
            password = input("请输入两步验证密码: ").strip()
            await app.check_password(password)
        
        me = await app.get_me()
        print(f"\n✓ 登录成功: {me.first_name} (@{me.username or 'N/A'})")
        await app.disconnect()
        print(f"✓ Session 文件已保存: sessions/{session_name}.session")
        return True
    except Exception as e:
        print(f"\n✗ 登录失败: {e}")
        await app.disconnect()
        return False
    finally:
        if app.is_connected:
            await app.disconnect()

if __name__ == "__main__":
    asyncio.run(generate_session())
'@
            $r2 = Invoke-SSHCommand -SessionId $session.SessionId -Command "mkdir -p /home/ubuntu/scripts && cat > /home/ubuntu/scripts/generate_session.py << 'PYEOF'
$loginScript
PYEOF
"
            Write-Host "  ✓ 登录脚本已创建" -ForegroundColor Green
        } else {
            Write-Host "  ✓ login.py 已存在" -ForegroundColor Green
        }
        Write-Host ""
        
        # 2. 创建 sessions 目录
        Write-Host "2. 创建 sessions 目录..." -ForegroundColor Cyan
        $r3 = Invoke-SSHCommand -SessionId $session.SessionId -Command "mkdir -p /home/ubuntu/sessions && echo OK"
        Write-Host "  ✓ sessions 目录已创建" -ForegroundColor Green
        Write-Host ""
        
        # 3. 提供生成 Session 的说明
        Write-Host "3. 生成 Session 文件..." -ForegroundColor Cyan
        Write-Host "   请在服务器上执行以下命令:" -ForegroundColor Yellow
        Write-Host "   cd /home/ubuntu" -ForegroundColor Cyan
        Write-Host "   python3 scripts/generate_session.py" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "   或者使用交互式 SSH 连接:" -ForegroundColor Yellow
        Write-Host "   ssh ubuntu@$($s.IP)" -ForegroundColor Cyan
        Write-Host "   cd /home/ubuntu" -ForegroundColor Cyan
        Write-Host "   python3 scripts/generate_session.py" -ForegroundColor Cyan
        Write-Host ""
        
        Remove-SSHSession -SessionId $session.SessionId | Out-Null
        
    } catch {
        Write-Host "✗ SSH 连接失败: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  说明" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "由于 Session 生成需要交互式输入（手机号、验证码等），" -ForegroundColor Yellow
Write-Host "建议使用支持交互的 SSH 客户端（如 PuTTY、MobaXterm）" -ForegroundColor Yellow
Write-Host "或直接在服务器上执行生成脚本。" -ForegroundColor Yellow
Write-Host ""

