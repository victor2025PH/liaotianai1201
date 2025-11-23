#!/bin/bash
# 在服务器上修复导入错误

DEPLOY_DIR="${1:-/home/ubuntu}"

cd "$DEPLOY_DIR/admin-backend"

echo "=== 修复 session_export.py ==="
sed -i 's/from app.core.permissions import PermissionCode, check_permission/from app.core.permissions import PermissionCode\nfrom app.middleware.permission import check_permission/' app/api/group_ai/session_export.py

echo "=== 修复 optimization.py ==="
sed -i 's/from app.core.permissions import PermissionCode, check_permission/from app.core.permissions import PermissionCode\nfrom app.middleware.permission import check_permission/' app/api/system/optimization.py

echo "✓ 导入错误已修复"


