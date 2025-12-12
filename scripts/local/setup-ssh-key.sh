#!/bin/bash
# ============================================================
# 配置 SSH 免密登录到服务器 (Linux/Mac)
# ============================================================

KEY_DIR="scripts/local/keys"
KEY_FILE="$KEY_DIR/server_key"
PUB_KEY_FILE="$KEY_DIR/server_key.pub"
SERVER_HOST="165.154.235.170"
SERVER_USER="ubuntu"
SERVER_PASSWORD="8iDcGrYb52Fxpzee"

echo "=========================================="
echo "🔑 配置 SSH 免密登录"
echo "=========================================="
echo ""

# 检查密钥文件是否存在
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ 密钥文件不存在: $KEY_FILE"
    echo ""
    echo "正在生成新的 SSH 密钥对..."
    echo ""
    
    # 创建 keys 目录（如果不存在）
    mkdir -p "$KEY_DIR"
    
    # 生成密钥对
    ssh-keygen -t rsa -b 4096 -f "$KEY_FILE" -N "" -C "telegram-ai-system-server-key"
    
    if [ $? -ne 0 ]; then
        echo "❌ 密钥生成失败"
        exit 1
    fi
    
    echo "✅ 密钥对生成成功"
    echo ""
fi

# 读取公钥
if [ ! -f "$PUB_KEY_FILE" ]; then
    echo "❌ 公钥文件不存在: $PUB_KEY_FILE"
    exit 1
fi

echo "=========================================="
echo "📤 将公钥复制到服务器"
echo "=========================================="
echo ""
echo "服务器: $SERVER_USER@$SERVER_HOST"
echo ""

# 检查是否已安装 sshpass（用于自动输入密码）
if command -v sshpass >/dev/null 2>&1; then
    echo "使用 sshpass 自动复制公钥..."
    sshpass -p "$SERVER_PASSWORD" ssh-copy-id -i "$PUB_KEY_FILE" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_HOST"
    
    if [ $? -eq 0 ]; then
        echo "✅ 公钥已复制到服务器"
    else
        echo "⚠️  ssh-copy-id 失败，尝试手动方法..."
    fi
else
    echo "⚠️  sshpass 未安装，使用手动方法..."
    echo ""
    echo "请手动执行以下命令（需要输入密码）:"
    echo "  密码: $SERVER_PASSWORD"
    echo ""
    echo "  ssh-copy-id -i $PUB_KEY_FILE $SERVER_USER@$SERVER_HOST"
    echo ""
    echo "或者手动复制："
    echo "  cat $PUB_KEY_FILE | ssh $SERVER_USER@$SERVER_HOST 'mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'"
    echo ""
    
    # 尝试使用 ssh-copy-id（会提示输入密码）
    ssh-copy-id -i "$PUB_KEY_FILE" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_HOST"
fi

echo ""
echo "=========================================="
echo "✅ SSH 免密登录配置完成"
echo "=========================================="
echo ""
echo "现在可以使用以下命令免密登录服务器："
echo "  ssh -i $KEY_FILE $SERVER_USER@$SERVER_HOST"
echo ""

