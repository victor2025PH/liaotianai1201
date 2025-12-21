#!/bin/bash
# 直接在服务器上修复 check_permission 装饰器错误（不依赖 Git）

echo "=== 修复 check_permission 装饰器错误 ==="
echo ""

cd ~/telegram-ai-system/admin-backend || exit 1

# 备份
echo "1. 备份文件..."
cp app/middleware/permission.py app/middleware/permission.py.bak.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp app/api/group_ai/keyword_triggers.py app/api/group_ai/keyword_triggers.py.bak.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp app/api/group_ai/group_management.py app/api/group_ai/group_management.py.bak.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp app/api/group_ai/scheduled_messages.py app/api/group_ai/scheduled_messages.py.bak.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
echo "✅ 备份完成"
echo ""

# 2. 使用 Python 修复
echo "2. 使用 Python 修复代码..."
python3 << 'PYTHON_FIX'
import re
import sys

def fix_permission_file():
    """修复 permission.py - 添加装饰器函数"""
    file_path = 'app/middleware/permission.py'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'def check_permission_decorator' in content:
            print("✅ check_permission_decorator 已存在")
            return True
        
        # 装饰器代码
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
        
        # 在 check_permission 函数之前插入
        pattern = r'(def check_permission\()'
        if re.search(pattern, content):
            content = re.sub(pattern, decorator_code + r'\1', content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ permission.py 已修复 - 添加了 check_permission_decorator")
            return True
        else:
            print("❌ 找不到 check_permission 函数定义")
            return False
            
    except Exception as e:
        print(f"❌ 修复 permission.py 失败: {e}")
        return False

def fix_api_file(file_path):
    """修复 API 文件 - 更新导入和装饰器使用"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        modified = False
        
        # 更新导入
        if 'check_permission_decorator' not in content:
            old_import = r'from app\.middleware\.permission import check_permission$'
            new_import = 'from app.middleware.permission import check_permission, check_permission_decorator'
            if re.search(old_import, content, re.MULTILINE):
                content = re.sub(old_import, new_import, content, flags=re.MULTILINE)
                modified = True
        
        # 替换装饰器
        old_decorator = r'@check_permission\(PermissionCode\.GROUP_AI_MANAGE\)'
        new_decorator = '@check_permission_decorator(PermissionCode.GROUP_AI_MANAGE)'
        if re.search(old_decorator, content):
            content = re.sub(old_decorator, new_decorator, content)
            modified = True
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {file_path} 已修复")
            return True
        else:
            print(f"ℹ️  {file_path} 无需修复（可能已修复）")
            return True
            
    except Exception as e:
        print(f"❌ 修复 {file_path} 失败: {e}")
        return False

# 执行修复
print("修复 permission.py...")
if not fix_permission_file():
    sys.exit(1)

print("\n修复 API 文件...")
files_to_fix = [
    'app/api/group_ai/keyword_triggers.py',
    'app/api/group_ai/group_management.py',
    'app/api/group_ai/scheduled_messages.py'
]

all_success = True
for file_path in files_to_fix:
    if not fix_api_file(file_path):
        all_success = False

if not all_success:
    print("\n❌ 部分文件修复失败")
    sys.exit(1)

print("\n✅ 所有文件修复完成！")
PYTHON_FIX

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Python 修复脚本执行失败"
    exit 1
fi

# 3. 验证语法
echo ""
echo "3. 验证 Python 语法..."
python3 -m py_compile app/middleware/permission.py app/api/group_ai/keyword_triggers.py app/api/group_ai/group_management.py app/api/group_ai/scheduled_messages.py 2>&1

if [ $? -ne 0 ]; then
    echo "❌ 语法验证失败"
    echo "恢复备份..."
    cp app/middleware/permission.py.bak.* app/middleware/permission.py 2>/dev/null || true
    exit 1
fi

echo "✅ 语法验证通过"
echo ""

# 4. 重启后端
echo "4. 重启后端..."
pm2 restart backend
sleep 8

# 5. 检查状态和日志
echo ""
echo "5. 检查后端状态..."
pm2 list | grep backend

echo ""
echo "6. 检查后端错误日志（最近30行）..."
pm2 logs backend --err --lines 30 --nostream 2>&1 | tail -30

echo ""
echo "7. 测试健康端点..."
curl -s http://127.0.0.1:8000/health || echo "❌ 后端未响应"
echo ""

echo "=== 修复完成 ==="
echo "如果后端状态为 'online' 且健康检查返回 'ok'，说明修复成功"
echo "如果仍有错误，请查看上面的错误日志"
