#!/bin/bash
# 安装 Telethon 及其依赖（Linux/Mac）

echo "========================================"
echo "安装 Telethon 及其依赖"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 未安装，请先安装 Python 3.9+"
    exit 1
fi

echo "[1/3] 检查当前安装的包..."
python3 -m pip list | grep -E "telethon|requests|openpyxl" || echo "未找到相关包"
echo ""

echo "[2/3] 安装 Telethon 及其依赖..."
echo "使用清华大学镜像源（国内用户推荐）..."
python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
python3 -m pip install telethon requests openpyxl -i https://pypi.tuna.tsinghua.edu.cn/simple

if [ $? -ne 0 ]; then
    echo "[WARN] 镜像源安装失败，尝试使用默认源..."
    python3 -m pip install telethon requests openpyxl --upgrade
    if [ $? -ne 0 ]; then
        echo "[ERROR] 依赖安装失败"
        exit 1
    fi
fi
echo ""

echo "[3/3] 验证安装..."
python3 -c "import telethon; print(f'Telethon 版本: {telethon.__version__}')"
python3 -c "import requests; print(f'Requests 版本: {requests.__version__}')"
python3 -c "import openpyxl; print(f'OpenPyXL 版本: {openpyxl.__version__}')"
echo ""

echo "========================================"
echo "安装完成！"
echo "========================================"
