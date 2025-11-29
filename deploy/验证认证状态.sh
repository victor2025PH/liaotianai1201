#!/bin/bash
# 验证认证相关配置

echo "============================================================"
echo "验证认证状态"
echo "============================================================"
echo ""

# 1. 检查后端服务
echo ">>> [1] 后端服务状态..."
sudo systemctl status liaotian-backend --no-pager | head -10
echo ""

# 2. 测试登录 API
echo ">>> [2] 测试登录 API..."
echo "尝试登录..."
response=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123")

if echo "$response" | grep -q "access_token"; then
    echo "[OK] 登录 API 正常"
    echo "响应: $(echo $response | head -c 100)..."
else
    echo "[错误] 登录失败"
    echo "响应: $response"
fi
echo ""

# 3. 检查后端认证配置
echo ">>> [3] 检查认证配置..."
if [ -f "/home/ubuntu/liaotian/admin-backend/.env" ]; then
    disable_auth=$(sudo grep -i "DISABLE_AUTH" /home/ubuntu/liaotian/admin-backend/.env | grep -v "^#" | cut -d'=' -f2)
    echo "DISABLE_AUTH: ${disable_auth:-未设置}"
else
    echo ".env 文件不存在"
fi
echo ""

# 4. 检查后端日志
echo ">>> [4] 后端日志（最近 10 行，包含 auth）..."
sudo journalctl -u liaotian-backend -n 50 --no-pager | grep -i auth | tail -5 || echo "无认证相关日志"
echo ""

echo "============================================================"
echo "验证完成"
echo "============================================================"
echo ""
echo "如果登录 API 正常，请在前端浏览器中："
echo "1. 访问 http://aikz.usdt2026.cc/login"
echo "2. 使用 admin@example.com / changeme123 登录"
echo "3. 验证 API 请求是否正常"

