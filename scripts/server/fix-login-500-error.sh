#!/bin/bash
# ============================================================
# 修复登录 500 错误
# ============================================================

echo "=========================================="
echo "🔧 修复登录 500 错误"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"

# 1. 检查后端服务状态
echo "[1/6] 检查后端服务状态..."
echo "----------------------------------------"
PM2_STATUS=$(sudo -u ubuntu pm2 list 2>/dev/null | grep backend || echo "")
if echo "$PM2_STATUS" | grep -q "online"; then
    echo "✅ 后端服务运行中"
else
    echo "❌ 后端服务未运行"
    echo "启动后端服务..."
    sudo -u ubuntu pm2 restart backend
    sleep 5
fi
echo ""

# 2. 检查后端日志（查找 500 错误）
echo "[2/6] 检查后端日志（查找登录相关错误）..."
echo "----------------------------------------"
echo "最近的错误日志:"
sudo -u ubuntu pm2 logs backend --lines 100 --nostream 2>&1 | grep -i "error\|exception\|traceback\|500\|login\|auth" | tail -30 || echo "未发现相关错误"
echo ""

echo "最近的登录请求日志:"
sudo -u ubuntu pm2 logs backend --lines 50 --nostream 2>&1 | grep -i "login\|/auth" | tail -20 || echo "未发现登录请求"
echo ""

# 3. 测试登录 API
echo "[3/6] 测试登录 API..."
echo "----------------------------------------"
echo "测试 /api/v1/auth/login (直接访问后端):"
LOGIN_TEST=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@example.com","password":"changeme123"}' 2>&1)
echo "$LOGIN_TEST" | head -10
echo ""

# 4. 检查数据库
echo "[4/6] 检查数据库..."
echo "----------------------------------------"
if [ -f "$BACKEND_DIR/admin.db" ]; then
    echo "✅ 数据库文件存在"
    DB_SIZE=$(du -h "$BACKEND_DIR/admin.db" | cut -f1)
    echo "   大小: $DB_SIZE"
    
    # 检查数据库是否可以访问
    if command -v sqlite3 &> /dev/null; then
        echo "测试数据库连接..."
        sqlite3 "$BACKEND_DIR/admin.db" "SELECT COUNT(*) FROM users;" 2>/dev/null
        if [ $? -eq 0 ]; then
            USER_COUNT=$(sqlite3 "$BACKEND_DIR/admin.db" "SELECT COUNT(*) FROM users;" 2>/dev/null)
            echo "✅ 数据库可访问，用户数量: $USER_COUNT"
        else
            echo "❌ 数据库无法访问"
        fi
    else
        echo "⚠️  sqlite3 未安装，无法测试数据库"
    fi
else
    echo "⚠️  数据库文件不存在（如果是首次运行，这是正常的）"
    echo "   需要初始化数据库"
fi
echo ""

# 5. 检查 .env 配置
echo "[5/6] 检查后端配置..."
echo "----------------------------------------"
if [ -f "$BACKEND_DIR/.env" ]; then
    echo "✅ .env 文件存在"
    if grep -q "DATABASE_URL" "$BACKEND_DIR/.env"; then
        echo "✅ DATABASE_URL 已配置"
    else
        echo "⚠️  DATABASE_URL 未配置"
    fi
    
    if grep -q "JWT_SECRET" "$BACKEND_DIR/.env"; then
        echo "✅ JWT_SECRET 已配置"
    else
        echo "⚠️  JWT_SECRET 未配置"
    fi
else
    echo "❌ .env 文件不存在"
    echo "创建 .env 文件..."
    cat > "$BACKEND_DIR/.env" <<EOF
JWT_SECRET=production_secret_key_change_me_$(date +%s)
LOG_LEVEL=INFO
CORS_ORIGINS=https://aikz.usdt2026.cc,http://aikz.usdt2026.cc,http://localhost:3000
DATABASE_URL=sqlite:///./admin.db
EOF
    echo "✅ .env 文件已创建"
fi
echo ""

# 6. 检查虚拟环境
echo "[6/6] 检查虚拟环境..."
echo "----------------------------------------"
if [ -f "$BACKEND_DIR/venv/bin/uvicorn" ]; then
    echo "✅ 虚拟环境中的 uvicorn 存在"
    
    # 检查关键依赖
    echo "检查关键依赖:"
    "$BACKEND_DIR/venv/bin/python" -c "import fastapi" 2>/dev/null && echo "✅ fastapi" || echo "❌ fastapi 缺失"
    "$BACKEND_DIR/venv/bin/python" -c "import sqlalchemy" 2>/dev/null && echo "✅ sqlalchemy" || echo "❌ sqlalchemy 缺失"
    "$BACKEND_DIR/venv/bin/python" -c "import passlib" 2>/dev/null && echo "✅ passlib" || echo "❌ passlib 缺失"
    "$BACKEND_DIR/venv/bin/python" -c "import jwt" 2>/dev/null && echo "✅ jwt" || echo "❌ jwt 缺失"
else
    echo "❌ 虚拟环境不完整"
    echo "重建虚拟环境..."
    cd "$BACKEND_DIR" || exit 1
    rm -rf venv
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    echo "✅ 虚拟环境已重建"
fi
echo ""

# 7. 初始化数据库（如果需要）
echo "=========================================="
echo "🔧 初始化数据库（如果需要）"
echo "=========================================="
echo ""

if [ ! -f "$BACKEND_DIR/admin.db" ]; then
    echo "数据库不存在，正在初始化..."
    cd "$BACKEND_DIR" || exit 1
    
    if [ -f "venv/bin/python" ]; then
        source venv/bin/activate
        python -c "
from app.db import Base, engine
from app.models import user, role, permission
Base.metadata.create_all(bind=engine)
print('Database initialized')
" 2>&1
        
        if [ $? -eq 0 ]; then
            echo "✅ 数据库已初始化"
            
            # 创建默认管理员用户
            echo "创建默认管理员用户..."
            python -c "
from app.db import SessionLocal
from app.crud.user import create_user, get_user_by_email
from app.crud.role import create_role
from app.core.security import get_password_hash

db = SessionLocal()
try:
    # 检查用户是否已存在
    user = get_user_by_email(db, 'admin@example.com')
    if not user:
        # 创建默认角色
        admin_role = create_role(db, name='admin', description='Administrator')
        
        # 创建默认用户
        user = create_user(
            db,
            email='admin@example.com',
            password='changeme123',
            full_name='Administrator'
        )
        
        # 分配角色
        from app.crud.user import assign_role_to_user
        assign_role_to_user(db, user.id, admin_role.id)
        
        print('Default admin user created')
    else:
        print('Admin user already exists')
finally:
    db.close()
" 2>&1
        else
            echo "❌ 数据库初始化失败"
        fi
    else
        echo "❌ 虚拟环境不存在，无法初始化数据库"
    fi
else
    echo "✅ 数据库已存在"
fi
echo ""

# 8. 重启后端服务
echo "=========================================="
echo "🔄 重启后端服务"
echo "=========================================="
echo ""
cd "$PROJECT_DIR" || exit 1
sudo -u ubuntu pm2 restart backend
sleep 5

echo "检查服务状态:"
sudo -u ubuntu pm2 list | grep backend
echo ""

# 9. 再次测试登录
echo "=========================================="
echo "🧪 再次测试登录 API"
echo "=========================================="
echo ""

echo "等待服务启动 (5秒)..."
sleep 5

echo "测试 /api/v1/auth/login:"
LOGIN_TEST2=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@example.com","password":"changeme123"}' 2>&1)

if echo "$LOGIN_TEST2" | grep -q "access_token\|token"; then
    echo "✅ 登录成功！"
    echo "$LOGIN_TEST2" | head -5
elif echo "$LOGIN_TEST2" | grep -q "401\|Unauthorized\|invalid"; then
    echo "⚠️  登录失败：用户名或密码错误"
    echo "$LOGIN_TEST2" | head -5
elif echo "$LOGIN_TEST2" | grep -q "500\|Internal Server Error"; then
    echo "❌ 登录仍然返回 500 错误"
    echo "$LOGIN_TEST2" | head -10
    echo ""
    echo "查看详细错误日志:"
    sudo -u ubuntu pm2 logs backend --lines 50 --nostream 2>&1 | tail -30
else
    echo "⚠️  未知响应:"
    echo "$LOGIN_TEST2" | head -10
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请检查:"
echo "1. 后端日志: sudo -u ubuntu pm2 logs backend --lines 100"
echo "2. 数据库文件: ls -la $BACKEND_DIR/admin.db"
echo "3. 虚拟环境: ls -la $BACKEND_DIR/venv/bin/"
echo ""

