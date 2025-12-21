#!/bin/bash
# 简单修复 check_permission 装饰器错误

echo "修复 check_permission 装饰器错误..."
cd ~/telegram-ai-system/admin-backend || exit 1

# 1. 在 permission.py 中添加装饰器函数（如果不存在）
if ! grep -q "def check_permission_decorator" app/middleware/permission.py; then
    echo "添加 check_permission_decorator 函数..."
    
    # 找到 check_permission 函数的位置，在其之前插入
    python3 << 'PYEOF'
import re

file_path = 'app/middleware/permission.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到 check_permission 函数定义的行
insert_pos = None
for i, line in enumerate(lines):
    if re.match(r'^def check_permission\(', line):
        insert_pos = i
        break

if insert_pos is None:
    print("❌ 找不到 check_permission 函数定义")
    exit(1)

# 插入装饰器函数
decorator_code = '''def check_permission_decorator(permission_code):
    """
    權限檢查裝飾器（用於 FastAPI 路由）
    """
    def decorator(func):
        from functools import wraps
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from fastapi import HTTPException, status
            from app.crud.permission import user_has_permission
            
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            
            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要認證"
                )
            
            perm_code = permission_code.value if hasattr(permission_code, 'value') else str(permission_code)
            
            if not user_has_permission(db, user=current_user, permission_code=perm_code):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"沒有權限執行此操作，需要權限: {perm_code}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


'''

lines.insert(insert_pos, decorator_code)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ 已添加 check_permission_decorator 函数")
PYEOF
else
    echo "✅ check_permission_decorator 已存在"
fi

# 2. 修复三个文件
echo ""
echo "修复 API 文件..."

for file in app/api/group_ai/keyword_triggers.py app/api/group_ai/group_management.py app/api/group_ai/scheduled_messages.py; do
    if [ -f "$file" ]; then
        echo "修复 $file..."
        
        # 更新导入
        sed -i 's/from app.middleware.permission import check_permission$/from app.middleware.permission import check_permission, check_permission_decorator/' "$file"
        
        # 替换装饰器
        sed -i 's/@check_permission(PermissionCode.GROUP_AI_MANAGE)/@check_permission_decorator(PermissionCode.GROUP_AI_MANAGE)/g' "$file"
        
        echo "✅ $file 修复完成"
    fi
done

# 3. 验证语法
echo ""
echo "验证语法..."
python3 -m py_compile app/middleware/permission.py app/api/group_ai/keyword_triggers.py app/api/group_ai/group_management.py app/api/group_ai/scheduled_messages.py 2>&1

if [ $? -eq 0 ]; then
    echo "✅ 语法验证通过"
    echo ""
    echo "重启后端..."
    pm2 restart backend
    sleep 5
    echo ""
    echo "检查错误日志..."
    pm2 logs backend --err --lines 10 --nostream
else
    echo "❌ 语法验证失败，请检查错误信息"
    exit 1
fi
