#!/bin/bash
# ============================================================
# 修复 TypeScript 错误并重新构建前端
# ============================================================

set -e

echo "=========================================="
echo "🔧 修复 TypeScript 错误并重新构建前端"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"
TARGET_FILE="$FRONTEND_DIR/src/app/group-ai/groups/page.tsx"
FRONTEND_SERVICE="liaotian-frontend"

# 1. 修复权限
echo "[1/5] 修复权限..."
echo "----------------------------------------"
chown -R ubuntu:ubuntu "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"
echo "✅ 权限已修复"
echo ""

# 2. 拉取最新代码（包含 TypeScript 修复）
echo "[2/5] 拉取最新代码..."
echo "----------------------------------------"
cd "$PROJECT_DIR"
git pull origin main
echo "✅ 代码已更新"
echo ""

# 3. 检查并修复 TypeScript 错误
echo "[3/5] 检查并修复 TypeScript 错误..."
echo "----------------------------------------"
cd "$FRONTEND_DIR"

if [ ! -f "$TARGET_FILE" ]; then
    echo "❌ 文件不存在: $TARGET_FILE"
    exit 1
fi

# 检查是否还有未修复的 group.username.replace 调用
UNSAFE_CALLS=$(grep -n "group\.username\.replace" "$TARGET_FILE" | grep -v "if.*group\.username" | grep -v "group\.username ||" || true)

if [ -n "$UNSAFE_CALLS" ]; then
    echo "发现未修复的 group.username.replace 调用:"
    echo "$UNSAFE_CALLS"
    echo ""
    echo "正在修复..."
    
    # 使用 Python 脚本进行更精确的修复
    python3 << 'PYTHON_SCRIPT'
import re
import sys

file_path = sys.argv[1]

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复模式 1: group.username.replace('@', '') 在 onClick 回调中
# 查找 onClick={() => { ... group.username.replace ... }}
pattern1 = r'(onClick=\{[^}]*?)(group\.username\.replace\([^)]+\))'
def replace1(match):
    prefix = match.group(1)
    replace_call = match.group(2)
    # 检查前缀中是否已有 if 检查
    if 'if (!group.username)' in prefix or 'if (group.username)' in prefix:
        return match.group(0)
    # 添加空值检查
    return prefix + 'if (!group.username) return; const username = group.username.replace(\'@\', \'); ' + replace_call.replace('group.username.replace(\'@\', \')', 'username')

content = re.sub(pattern1, replace1, content, flags=re.DOTALL)

# 修复模式 2: 直接使用 (group.username || '').replace(...)
pattern2 = r'group\.username\.replace\(([^)]+)\)'
def replace2(match):
    args = match.group(1)
    return f'(group.username || "").replace({args})'

# 只在没有 if 检查的地方替换
lines = content.split('\n')
fixed_lines = []
in_onclick = False
onclick_start = -1

for i, line in enumerate(lines):
    # 检测 onClick 开始
    if 'onClick={()' in line or 'onClick={async ()' in line:
        in_onclick = True
        onclick_start = i
        fixed_lines.append(line)
        continue
    
    # 检测 onClick 结束
    if in_onclick and '}}' in line and i > onclick_start + 1:
        in_onclick = False
        fixed_lines.append(line)
        continue
    
    # 在 onClick 内部，检查是否有 group.username.replace
    if in_onclick and 'group.username.replace' in line:
        # 检查前面是否有 if 检查
        has_check = False
        for j in range(max(0, i-5), i):
            if 'if (!group.username)' in lines[j] or 'if (group.username)' in lines[j]:
                has_check = True
                break
        
        if not has_check:
            # 添加空值检查
            indent = len(line) - len(line.lstrip())
            fixed_lines.append(' ' * indent + 'if (!group.username) return;')
            # 修复 replace 调用
            line = re.sub(r'group\.username\.replace\(([^)]+)\)', r'group.username.replace(\1)', line)
            # 如果是在变量赋值中，需要先提取 username
            if 'const' in line or 'let' in line or 'var' in line:
                line = re.sub(
                    r'(const|let|var)\s+(\w+)\s*=\s*group\.username\.replace',
                    r'if (!group.username) return; \1 \2 = group.username.replace',
                    line
                )
        
        fixed_lines.append(line)
    else:
        # 不在 onClick 中，直接修复
        if 'group.username.replace' in line and 'if' not in line and '||' not in line:
            line = re.sub(r'group\.username\.replace\(([^)]+)\)', r'(group.username || "").replace(\1)', line)
        fixed_lines.append(line)

content = '\n'.join(fixed_lines)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ TypeScript 错误已修复")
PYTHON_SCRIPT
    
    python3 -c "$(cat << 'PYTHON_SCRIPT'
import re
import sys

file_path = sys.argv[1]

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_lines = []
in_onclick = False
onclick_indent = 0

i = 0
while i < len(lines):
    line = lines[i]
    
    # 检测 onClick 开始
    if 'onClick={()' in line or 'onClick={async ()' in line:
        in_onclick = True
        onclick_indent = len(line) - len(line.lstrip())
        fixed_lines.append(line)
        i += 1
        continue
    
    # 在 onClick 内部
    if in_onclick:
        # 检测 onClick 结束
        if '}}' in line and i > 0:
            in_onclick = False
            fixed_lines.append(line)
            i += 1
            continue
        
        # 检查是否有 group.username.replace
        if 'group.username.replace' in line:
            # 检查前面几行是否有 if 检查
            has_check = False
            for j in range(max(0, len(fixed_lines)-5), len(fixed_lines)):
                if 'if (!group.username)' in fixed_lines[j] or 'if (group.username)' in fixed_lines[j]:
                    has_check = True
                    break
            
            if not has_check:
                # 添加空值检查
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(' ' * indent + 'if (!group.username) return;\n')
            
            # 修复 replace 调用 - 如果是在变量赋值中
            if 'const' in line or 'let' in line:
                # 提取变量名和参数
                match = re.search(r'(const|let)\s+(\w+)\s*=\s*group\.username\.replace\(([^)]+)\)', line)
                if match:
                    var_type = match.group(1)
                    var_name = match.group(2)
                    replace_args = match.group(3)
                    indent = len(line) - len(line.lstrip())
                    # 替换为安全的版本
                    line = ' ' * indent + f'const {var_name} = group.username.replace({replace_args});\n'
            
            fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    else:
        # 不在 onClick 中，直接修复不安全的调用
        if 'group.username.replace' in line and 'if' not in line and '||' not in line and '?' not in line:
            line = re.sub(r'group\.username\.replace\(([^)]+)\)', r'(group.username || "").replace(\1)', line)
        fixed_lines.append(line)
    
    i += 1

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("✅ TypeScript 错误已修复")
PYTHON_SCRIPT
)" "$TARGET_FILE"
    
    echo "✅ 代码已修复"
else
    echo "✅ 未发现需要修复的问题"
fi
echo ""

# 4. 清理并重新构建
echo "[4/5] 清理并重新构建前端..."
echo "----------------------------------------"
cd "$FRONTEND_DIR"

# 清理构建目录
if [ -d ".next" ]; then
    echo "清理 .next 目录..."
    rm -rf .next
fi

# 确保权限正确
chown -R ubuntu:ubuntu .

# 构建
echo "开始构建（这可能需要几分钟）..."
if npm run build; then
    echo "✅ 构建成功"
else
    echo "❌ 构建失败"
    echo "查看构建错误信息..."
    exit 1
fi

# 验证 standalone 目录
if [ ! -d ".next/standalone" ]; then
    echo "❌ standalone 目录不存在，构建可能不完整"
    exit 1
fi

if [ ! -f ".next/standalone/server.js" ]; then
    echo "❌ standalone/server.js 不存在"
    exit 1
fi

echo "✅ standalone 构建验证通过"
echo ""

# 5. 修复服务配置并重启
echo "[5/5] 修复服务配置并重启..."
echo "----------------------------------------"
# 更新前端服务配置
cat > /etc/systemd/system/$FRONTEND_SERVICE.service <<EOF
[Unit]
Description=Liaotian Next.js Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$FRONTEND_DIR/.next/standalone
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=NODE_OPTIONS=--max-old-space-size=1024
ExecStart=/usr/bin/node $FRONTEND_DIR/.next/standalone/server.js
Restart=always
RestartSec=5
LimitNOFILE=65535

StandardOutput=journal
StandardError=journal
SyslogIdentifier=liaotian-frontend

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "✅ 服务配置已更新"

# 重启前端服务
echo "重启前端服务..."
systemctl restart "$FRONTEND_SERVICE"
sleep 5

if systemctl is-active --quiet "$FRONTEND_SERVICE"; then
    echo "✅ 前端服务已启动"
else
    echo "❌ 前端服务启动失败"
    systemctl status "$FRONTEND_SERVICE" --no-pager -l | head -20
    exit 1
fi

# 重启 Nginx
echo "重启 Nginx..."
systemctl restart nginx
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 已重启"
else
    echo "⚠️  Nginx 重启失败，检查配置"
    nginx -t
fi
echo ""

# 验证
echo "=========================================="
echo "✅ 修复完成，开始验证..."
echo "=========================================="
echo ""

sleep 3

# 检查服务状态
echo "服务状态:"
systemctl status "$FRONTEND_SERVICE" --no-pager -l | head -10
echo ""

# 检查端口
PORT_3000=$(lsof -ti:3000 2>/dev/null || true)
if [ -n "$PORT_3000" ]; then
    echo "✅ 端口 3000 正在监听 (PID: $PORT_3000)"
else
    echo "❌ 端口 3000 未监听"
fi

# 测试服务
FRONTEND_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/login 2>/dev/null || echo "000")
if [ "$FRONTEND_TEST" = "200" ]; then
    echo "✅ 前端登录页面: HTTP 200"
else
    echo "⚠️  前端登录页面: HTTP $FRONTEND_TEST"
fi

echo ""
echo "=========================================="
echo "✅ 所有修复完成"
echo "=========================================="
echo ""

