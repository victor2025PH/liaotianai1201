#!/bin/bash
# 修复 permissions.py 中的语法错误

echo "修复 permissions.py 语法错误..."

cd ~/telegram-ai-system/admin-backend || exit 1

# 备份原文件
cp app/core/permissions.py app/core/permissions.py.bak

# 检查并修复 GROUP_AI_MANAGE 权限定义
if ! grep -q "GROUP_AI_MANAGE = \"group_ai:manage\"" app/core/permissions.py; then
    echo "添加 GROUP_AI_MANAGE 权限定义..."
    # 在 AUTOMATION_TASK_LOG_VIEW 之后添加
    sed -i '/AUTOMATION_TASK_LOG_VIEW = "automation_task:log:view"/a\
    \
    # ============ 群組AI管理 ============\
    GROUP_AI_MANAGE = "group_ai:manage"  # 群組AI統一管理權限（關鍵詞觸發、定時消息、群組加入配置等)' app/core/permissions.py
fi

# 检查并修复权限组定义
if ! grep -q '"group_ai_management":' app/core/permissions.py; then
    echo "添加 group_ai_management 权限组..."
    # 在 automation_management 之后添加
    sed -i '/"automation_management": \[/,/    \],/{
        /    \],/a\
    "group_ai_management": [\
        PermissionCode.GROUP_AI_MANAGE,\
    ],
    }' app/core/permissions.py
else
    # 如果已存在但可能有语法错误，先删除再重新添加
    echo "修复现有的 group_ai_management 权限组..."
    # 删除可能损坏的权限组定义（从 "group_ai_management" 到下一个权限组之前）
    sed -i '/"group_ai_management":/,/^    "export_management":/{
        /"group_ai_management":/d
        /PermissionCode.GROUP_AI_MANAGE,/d
        /    \],/d
    }' app/core/permissions.py
    
    # 重新添加正确的权限组定义
    sed -i '/"automation_management": \[/,/    \],/{
        /    \],/a\
    "group_ai_management": [\
        PermissionCode.GROUP_AI_MANAGE,\
    ],
    }' app/core/permissions.py
fi

# 验证 Python 语法
echo "验证 Python 语法..."
python3 -m py_compile app/core/permissions.py 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Python 语法验证通过"
else
    echo "❌ Python 语法验证失败，恢复备份..."
    cp app/core/permissions.py.bak app/core/permissions.py
    exit 1
fi

# 测试导入
echo "测试导入 PermissionCode..."
python3 -c "import sys; sys.path.insert(0, '.'); from app.core.permissions import PermissionCode; print('GROUP_AI_MANAGE =', PermissionCode.GROUP_AI_MANAGE)" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ PermissionCode 导入成功"
else
    echo "❌ PermissionCode 导入失败，恢复备份..."
    cp app/core/permissions.py.bak app/core/permissions.py
    exit 1
fi

echo ""
echo "修复完成，重启后端..."
pm2 restart backend
sleep 5
pm2 logs backend --lines 30 --nostream
