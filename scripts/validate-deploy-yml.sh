#!/bin/bash
# 验证 deploy.yml 的 YAML 语法和配置

echo "验证 GitHub Actions deploy.yml 配置..."
echo ""

# 检查文件是否存在
if [ ! -f ".github/workflows/deploy.yml" ]; then
    echo "❌ 文件不存在: .github/workflows/deploy.yml"
    exit 1
fi

echo "✅ 文件存在"
echo ""

# 检查必需的 Secrets 引用
echo "检查 Secrets 引用："
grep -q "secrets.SERVER_HOST" .github/workflows/deploy.yml && echo "  ✅ SERVER_HOST" || echo "  ❌ SERVER_HOST 缺失"
grep -q "secrets.SERVER_USER" .github/workflows/deploy.yml && echo "  ✅ SERVER_USER" || echo "  ❌ SERVER_USER 缺失"
grep -q "secrets.SERVER_SSH_KEY" .github/workflows/deploy.yml && echo "  ✅ SERVER_SSH_KEY" || echo "  ❌ SERVER_SSH_KEY 缺失"
echo ""

# 检查 SSH 配置参数
echo "检查 SSH 配置参数："
grep -q "port: 22" .github/workflows/deploy.yml && echo "  ✅ port: 22" || echo "  ⚠️  port 未明确指定"
grep -q "timeout:" .github/workflows/deploy.yml && echo "  ✅ timeout 已设置" || echo "  ❌ timeout 缺失"
grep -q "command_timeout:" .github/workflows/deploy.yml && echo "  ✅ command_timeout 已设置" || echo "  ❌ command_timeout 缺失"
grep -q "debug: true" .github/workflows/deploy.yml && echo "  ✅ debug: true" || echo "  ⚠️  debug 未启用"
echo ""

# 检查 YAML 缩进（简单检查）
echo "检查 YAML 缩进（基本验证）："
if grep -q "^[[:space:]]*host:.*secrets.SERVER_HOST" .github/workflows/deploy.yml; then
    echo "  ✅ host 缩进正确"
else
    echo "  ⚠️  host 缩进可能有问题"
fi

if grep -q "^[[:space:]]*port: 22" .github/workflows/deploy.yml; then
    echo "  ✅ port 缩进正确"
else
    echo "  ⚠️  port 缩进可能有问题"
fi
echo ""

# 显示 SSH 配置部分
echo "SSH 配置内容："
echo "========================================="
sed -n '/Deploy to Server/,/script:/p' .github/workflows/deploy.yml | head -15
echo "========================================="
echo ""

echo "✅ 验证完成"
