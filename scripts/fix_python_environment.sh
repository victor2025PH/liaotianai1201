#!/bin/bash
# Fix Python environment and install dependencies
# 修复 Python 环境并安装依赖

set -e

echo "========================================="
echo "修复 Python 环境和依赖"
echo "========================================="
echo ""

cd ~/liaotian || exit 1

echo "=== 步骤 1: 检查 Python 环境 ==="
echo "Python 版本: $(python3 --version)"
echo "pip 版本: $(pip3 --version 2>/dev/null || echo 'pip3 未安装')"

echo ""
echo "=== 步骤 2: 安装 Python 依赖（处理 PEP 668 限制）==="

# 方法 1: 尝试使用 --break-system-packages（Ubuntu 24.04）
if python3 -c "import uvicorn" 2>/dev/null; then
    echo "✅ uvicorn 已安装"
else
    echo "安装 uvicorn 和 fastapi..."
    
    # 尝试使用 --break-system-packages
    if pip3 install uvicorn fastapi --break-system-packages 2>/dev/null; then
        echo "✅ 使用 --break-system-packages 安装成功"
    # 尝试使用 --user
    elif pip3 install uvicorn fastapi --user 2>/dev/null; then
        echo "✅ 使用 --user 安装成功"
    # 尝试使用系统包管理器
    elif apt list --installed 2>/dev/null | grep -q python3-uvicorn; then
        echo "✅ uvicorn 已通过系统包管理器安装"
    else
        echo "⚠️  尝试其他安装方法..."
        
        # 创建虚拟环境（推荐方法）
        if [ ! -d "venv" ]; then
            echo "创建虚拟环境..."
            python3 -m venv venv
        fi
        
        echo "在虚拟环境中安装依赖..."
        source venv/bin/activate
        pip install uvicorn fastapi
        deactivate
        echo "✅ 虚拟环境中安装成功"
    fi
fi

# 验证安装
echo ""
echo "=== 步骤 3: 验证安装 ==="
if python3 -c "import uvicorn" 2>/dev/null; then
    echo "✅ uvicorn 安装成功"
    python3 -c "import uvicorn; print(f'uvicorn 版本: {uvicorn.__version__}')" 2>/dev/null || echo "版本信息不可用"
else
    echo "❌ uvicorn 仍然未安装"
    echo "请手动安装:"
    echo "  pip3 install uvicorn fastapi --break-system-packages"
    echo "  或创建虚拟环境: python3 -m venv venv && source venv/bin/activate && pip install uvicorn fastapi"
fi

# 安装后端其他依赖
echo ""
echo "=== 步骤 4: 安装后端其他依赖 ==="
if [ -f "admin-backend/requirements.txt" ]; then
    echo "发现 requirements.txt，安装依赖..."
    
    # 尝试直接安装
    if pip3 install -r admin-backend/requirements.txt --break-system-packages 2>/dev/null; then
        echo "✅ 依赖安装成功"
    elif pip3 install -r admin-backend/requirements.txt --user 2>/dev/null; then
        echo "✅ 使用 --user 安装成功"
    else
        echo "⚠️  依赖安装可能有问题，请检查"
    fi
else
    echo "⚠️  requirements.txt 未找到"
fi

echo ""
echo "✅ Python 环境修复完成！"
