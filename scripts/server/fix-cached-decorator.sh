#!/bin/bash
# 修复 cached 装饰器的 key_prefix 参数错误

echo "=== 修复 cached 装饰器参数错误 ==="
echo ""

cd ~/telegram-ai-system/admin-backend || exit 1

# 备份
echo "1. 备份文件..."
cp app/api/group_ai/keyword_triggers.py app/api/group_ai/keyword_triggers.py.bak.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp app/api/group_ai/group_management.py app/api/group_ai/group_management.py.bak.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp app/api/group_ai/scheduled_messages.py app/api/group_ai/scheduled_messages.py.bak.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
echo "✅ 备份完成"
echo ""

# 修复 key_prefix -> prefix
echo "2. 修复 cached 装饰器参数..."
sed -i 's/@cached(ttl=\([0-9]*\), key_prefix="\([^"]*\)")/@cached(prefix="\2", ttl=\1)/g' app/api/group_ai/keyword_triggers.py
sed -i 's/@cached(ttl=\([0-9]*\), key_prefix="\([^"]*\)")/@cached(prefix="\2", ttl=\1)/g' app/api/group_ai/group_management.py
sed -i 's/@cached(ttl=\([0-9]*\), key_prefix="\([^"]*\)")/@cached(prefix="\2", ttl=\1)/g' app/api/group_ai/scheduled_messages.py

echo "✅ 已修复 keyword_triggers.py"
echo "✅ 已修复 group_management.py"
echo "✅ 已修复 scheduled_messages.py"
echo ""

# 验证语法
echo "3. 验证 Python 语法..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 已激活虚拟环境"
fi

python3 -m py_compile app/api/group_ai/keyword_triggers.py app/api/group_ai/group_management.py app/api/group_ai/scheduled_messages.py 2>&1

if [ $? -eq 0 ]; then
    echo "✅ 语法验证通过"
else
    echo "❌ 语法验证失败"
    exit 1
fi

# 检查 fastapi 是否安装
echo ""
echo "4. 检查 fastapi 模块..."
python3 -c "import fastapi; print('✅ fastapi 已安装')" 2>&1 || {
    echo "❌ fastapi 未安装"
    echo "尝试安装依赖..."
    if [ -f "requirements.txt" ]; then
        if [ -d "venv" ]; then
            source venv/bin/activate
            pip install fastapi 2>&1 || echo "⚠️  安装失败，请手动执行: pip install fastapi"
        else
            pip3 install fastapi 2>&1 || echo "⚠️  安装失败，请手动执行: pip3 install fastapi"
        fi
    else
        echo "⚠️  未找到 requirements.txt，请手动安装: pip install fastapi"
    fi
}

echo ""
echo "5. 重启后端..."
pm2 restart backend
sleep 8

echo ""
echo "6. 检查后端状态..."
pm2 list | grep backend

echo ""
echo "7. 检查错误日志（最近20行）..."
pm2 logs backend --err --lines 20 --nostream 2>&1 | tail -20

echo ""
echo "=== 修复完成 ==="
