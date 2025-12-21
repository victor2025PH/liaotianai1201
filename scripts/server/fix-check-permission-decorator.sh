#!/bin/bash
# 修复 check_permission 装饰器错误

echo "修复 check_permission 装饰器使用错误..."
echo ""

cd ~/telegram-ai-system/admin-backend || exit 1

# 备份文件
echo "1. 备份文件..."
cp app/middleware/permission.py app/middleware/permission.py.bak.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp app/api/group_ai/keyword_triggers.py app/api/group_ai/keyword_triggers.py.bak.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp app/api/group_ai/group_management.py app/api/group_ai/group_management.py.bak.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp app/api/group_ai/scheduled_messages.py app/api/group_ai/scheduled_messages.py.bak.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
echo "✅ 备份完成"
echo ""

# 2. 检查并添加装饰器函数到 permission.py
echo "2. 检查 permission.py 中的装饰器函数..."
if ! grep -q "def check_permission_decorator" app/middleware/permission.py; then
    echo "添加 check_permission_decorator 函数..."
    
    # 在 check_permission 函数之前添加装饰器
    cat >> /tmp/check_permission_decorator_code.py << 'DECORATOR_EOF'
def check_permission_decorator(permission_code):
    """
    權限檢查裝飾器（用於 FastAPI 路由）
    
    Usage:
        @router.post("/endpoint")
        @check_permission_decorator(PermissionCode.ACCOUNT_VIEW)
        async def my_endpoint(
            current_user: User = Depends(get_current_active_user),
            db: Session = Depends(get_db)
        ):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 從 kwargs 中獲取 current_user 和 db
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            
            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要認證"
                )
            
            # 獲取權限代碼字符串
            perm_code = permission_code.value if hasattr(permission_code, 'value') else str(permission_code)
            
            # 檢查權限
            if not user_has_permission(db, user=current_user, permission_code=perm_code):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"沒有權限執行此操作，需要權限: {perm_code}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

DECORATOR_EOF
    
    # 在 return permission_checker 之后、check_permission 之前插入
    sed -i '/^def check_permission(/i\
\
' app/middleware/permission.py
    
    # 读取装饰器代码并插入
    python3 << 'PYTHON_SCRIPT'
import re

file_path = 'app/middleware/permission.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 检查是否已存在
if 'def check_permission_decorator' in content:
    print("✅ check_permission_decorator 已存在")
else:
    # 在 check_permission 函数之前添加
    decorator_code = '''def check_permission_decorator(permission_code):
    """
    權限檢查裝飾器（用於 FastAPI 路由）
    
    Usage:
        @router.post("/endpoint")
        @check_permission_decorator(PermissionCode.ACCOUNT_VIEW)
        async def my_endpoint(
            current_user: User = Depends(get_current_active_user),
            db: Session = Depends(get_db)
        ):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 從 kwargs 中獲取 current_user 和 db
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            
            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要認證"
                )
            
            # 獲取權限代碼字符串
            perm_code = permission_code.value if hasattr(permission_code, 'value') else str(permission_code)
            
            # 檢查權限
            if not user_has_permission(db, user=current_user, permission_code=perm_code):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"沒有權限執行此操作，需要權限: {perm_code}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


'''
    
    # 在 check_permission 函数定义之前插入
    pattern = r'(def check_permission\()'
    replacement = decorator_code + r'\1'
    content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 已添加 check_permission_decorator 函数")

PYTHON_SCRIPT
else
    echo "✅ check_permission_decorator 已存在"
fi
echo ""

# 3. 修复 keyword_triggers.py
echo "3. 修复 keyword_triggers.py..."
# 更新导入
if ! grep -q "check_permission_decorator" app/api/group_ai/keyword_triggers.py; then
    sed -i 's/from app.middleware.permission import check_permission$/from app.middleware.permission import check_permission, check_permission_decorator/' app/api/group_ai/keyword_triggers.py
fi
# 替换装饰器使用
sed -i 's/@check_permission(PermissionCode.GROUP_AI_MANAGE)/@check_permission_decorator(PermissionCode.GROUP_AI_MANAGE)/g' app/api/group_ai/keyword_triggers.py
echo "✅ keyword_triggers.py 修复完成"
echo ""

# 4. 修复 group_management.py
echo "4. 修复 group_management.py..."
if ! grep -q "check_permission_decorator" app/api/group_ai/group_management.py; then
    sed -i 's/from app.middleware.permission import check_permission$/from app.middleware.permission import check_permission, check_permission_decorator/' app/api/group_ai/group_management.py
fi
sed -i 's/@check_permission(PermissionCode.GROUP_AI_MANAGE)/@check_permission_decorator(PermissionCode.GROUP_AI_MANAGE)/g' app/api/group_ai/group_management.py
echo "✅ group_management.py 修复完成"
echo ""

# 5. 修复 scheduled_messages.py
echo "5. 修复 scheduled_messages.py..."
if ! grep -q "check_permission_decorator" app/api/group_ai/scheduled_messages.py; then
    sed -i 's/from app.middleware.permission import check_permission$/from app.middleware.permission import check_permission, check_permission_decorator/' app/api/group_ai/scheduled_messages.py
fi
sed -i 's/@check_permission(PermissionCode.GROUP_AI_MANAGE)/@check_permission_decorator(PermissionCode.GROUP_AI_MANAGE)/g' app/api/group_ai/scheduled_messages.py
echo "✅ scheduled_messages.py 修复完成"
echo ""

# 6. 验证语法
echo "6. 验证 Python 语法..."
python3 -m py_compile app/middleware/permission.py 2>&1 && echo "✅ permission.py 语法正确" || echo "❌ permission.py 语法错误"
python3 -m py_compile app/api/group_ai/keyword_triggers.py 2>&1 && echo "✅ keyword_triggers.py 语法正确" || echo "❌ keyword_triggers.py 语法错误"
python3 -m py_compile app/api/group_ai/group_management.py 2>&1 && echo "✅ group_management.py 语法正确" || echo "❌ group_management.py 语法错误"
python3 -m py_compile app/api/group_ai/scheduled_messages.py 2>&1 && echo "✅ scheduled_messages.py 语法正确" || echo "❌ scheduled_messages.py 语法错误"
echo ""

# 7. 重启后端
echo "7. 重启后端..."
pm2 restart backend
sleep 5

# 8. 检查日志
echo ""
echo "8. 检查后端日志（最近20行）..."
pm2 logs backend --lines 20 --nostream --err 2>&1 | tail -20

echo ""
echo "=== 修复完成 ==="
echo "如果仍有错误，请检查上面的日志输出"
