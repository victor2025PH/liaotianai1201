#!/bin/bash
# 完整修复 permissions.py - 使用 Python 脚本确保语法正确

echo "修复 permissions.py 语法错误..."

cd ~/telegram-ai-system/admin-backend || exit 1

# 备份
cp app/core/permissions.py app/core/permissions.py.bak

# 使用 Python 脚本来修复
python3 << 'PYTHON_SCRIPT'
import re

file_path = 'app/core/permissions.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 检查并添加 GROUP_AI_MANAGE 权限定义
if 'GROUP_AI_MANAGE = "group_ai:manage"' not in content:
    # 在 AUTOMATION_TASK_LOG_VIEW 之后添加
    pattern = r'(AUTOMATION_TASK_LOG_VIEW = "automation_task:log:view")'
    replacement = r'\1\n    \n    # ============ 群組AI管理 ============\n    GROUP_AI_MANAGE = "group_ai:manage"  # 群組AI統一管理權限（關鍵詞觸發、定時消息、群組加入配置等）'
    content = re.sub(pattern, replacement, content)
    print("✅ 已添加 GROUP_AI_MANAGE 权限定义")

# 2. 检查并修复权限组定义
if '"group_ai_management":' not in content:
    # 在 automation_management 之后添加
    pattern = r'("automation_management": \[[^\]]+\],)'
    replacement = r'\1\n    "group_ai_management": [\n        PermissionCode.GROUP_AI_MANAGE,\n    ],'
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    print("✅ 已添加 group_ai_management 权限组")
else:
    # 如果已存在但可能有语法错误，修复它
    # 删除可能损坏的定义
    content = re.sub(r'"group_ai_management":\s*\[[^\]]*\]\s*,?\s*', '', content, flags=re.DOTALL)
    # 重新添加正确的定义
    pattern = r'("automation_management": \[[^\]]+\],)'
    replacement = r'\1\n    "group_ai_management": [\n        PermissionCode.GROUP_AI_MANAGE,\n    ],'
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    print("✅ 已修复 group_ai_management 权限组")

# 保存文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

# 验证语法
try:
    compile(content, file_path, 'exec')
    print("✅ Python 语法验证通过")
except SyntaxError as e:
    print(f"❌ Python 语法错误: {e}")
    exit(1)

PYTHON_SCRIPT

if [ $? -ne 0 ]; then
    echo "❌ 修复失败，恢复备份..."
    cp app/core/permissions.py.bak app/core/permissions.py
    exit 1
fi

# 测试导入
echo "测试导入 PermissionCode..."
python3 -c "import sys; sys.path.insert(0, '.'); from app.core.permissions import PermissionCode; print('✅ GROUP_AI_MANAGE =', PermissionCode.GROUP_AI_MANAGE)" 2>&1

if [ $? -ne 0 ]; then
    echo "❌ 导入测试失败，恢复备份..."
    cp app/core/permissions.py.bak app/core/permissions.py
    exit 1
fi

echo ""
echo "修复完成，重启后端..."
pm2 restart backend
sleep 5
pm2 logs backend --lines 30 --nostream
