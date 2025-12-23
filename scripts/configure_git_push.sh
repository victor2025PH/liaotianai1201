#!/bin/bash
# Git Push 认证配置脚本
# 帮助用户在服务器上配置 Git push 认证

set -e

echo "🔧 Git Push 认证配置脚本"
echo "=========================="
echo ""

# 检查当前 remote URL
CURRENT_URL=$(git remote get-url origin 2>/dev/null || echo "")
echo "当前 remote URL: $CURRENT_URL"
echo ""

# 判断当前使用的方式
if echo "$CURRENT_URL" | grep -q "^https://"; then
    CURRENT_METHOD="HTTPS"
elif echo "$CURRENT_URL" | grep -q "^git@"; then
    CURRENT_METHOD="SSH"
else
    CURRENT_METHOD="UNKNOWN"
fi

echo "当前连接方式: $CURRENT_METHOD"
echo ""

# 提供选项
echo "请选择配置方式:"
echo "1) 使用 Personal Access Token（HTTPS，简单快速）"
echo "2) 改用 SSH 方式（推荐，更安全）"
echo "3) 配置 credential helper 缓存密码"
echo "4) 退出"
echo ""

read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "=== 配置 Personal Access Token ==="
        echo ""
        echo "步骤 1: 创建 Personal Access Token"
        echo "1. 打开: https://github.com/settings/tokens"
        echo "2. 点击 'Generate new token (classic)'"
        echo "3. 勾选 'repo' 权限"
        echo "4. 生成并复制 token"
        echo ""
        read -p "已创建 token 并复制？(y/n): " confirm
        
        if [ "$confirm" != "y" ]; then
            echo "请先创建 token，然后重新运行此脚本"
            exit 1
        fi
        
        # 配置 credential helper
        git config --global credential.helper store
        echo "✅ 已配置 credential helper"
        echo ""
        echo "步骤 2: 测试推送"
        echo "执行: git push origin main"
        echo "Username: victor2025PH"
        echo "Password: <粘贴你的 token>"
        echo ""
        echo "之后就不需要再输入密码了"
        ;;
        
    2)
        echo ""
        echo "=== 配置 SSH 方式 ==="
        echo ""
        
        # 检查是否已有 SSH 密钥
        SSH_KEY="$HOME/.ssh/id_ed25519_github"
        if [ -f "$SSH_KEY" ]; then
            echo "⚠️  发现已存在的 SSH 密钥: $SSH_KEY"
            read -p "是否使用现有密钥？(y/n): " use_existing
            if [ "$use_existing" != "y" ]; then
                SSH_KEY="$HOME/.ssh/id_ed25519_github_$(date +%s)"
            fi
        else
            # 生成新的 SSH 密钥
            echo "生成新的 SSH 密钥..."
            ssh-keygen -t ed25519 -C "server-git-push-$(hostname)" -f "$SSH_KEY" -N ""
            echo "✅ SSH 密钥已生成: $SSH_KEY"
        fi
        
        # 显示公钥
        echo ""
        echo "=== 请将以下公钥添加到 GitHub ==="
        echo ""
        cat "${SSH_KEY}.pub"
        echo ""
        echo "1. 打开: https://github.com/settings/ssh/new"
        echo "2. Title: Server Git Push ($(hostname))"
        echo "3. Key: 粘贴上面的公钥内容"
        echo "4. 点击 'Add SSH key'"
        echo ""
        read -p "已添加公钥到 GitHub？(y/n): " confirm
        
        if [ "$confirm" != "y" ]; then
            echo "请先添加公钥，然后重新运行此脚本"
            exit 1
        fi
        
        # 配置 SSH config
        mkdir -p ~/.ssh
        chmod 700 ~/.ssh
        
        if [ ! -f ~/.ssh/config ]; then
            touch ~/.ssh/config
            chmod 600 ~/.ssh/config
        fi
        
        # 检查是否已有 github.com 配置
        if ! grep -q "Host github.com" ~/.ssh/config; then
            cat >> ~/.ssh/config << EOF

Host github.com
    HostName github.com
    User git
    IdentityFile $SSH_KEY
    IdentitiesOnly yes
EOF
            echo "✅ 已配置 SSH config"
        else
            echo "⚠️  SSH config 中已有 github.com 配置，请手动检查"
        fi
        
        # 测试 SSH 连接
        echo ""
        echo "测试 SSH 连接..."
        if ssh -T -i "$SSH_KEY" git@github.com 2>&1 | grep -q "successfully authenticated"; then
            echo "✅ SSH 连接成功！"
        else
            echo "⚠️  SSH 连接测试未完全成功，但可能仍可正常工作"
        fi
        
        # 更改 remote URL 为 SSH
        git remote set-url origin git@github.com:victor2025PH/liaotianai1201.git
        echo "✅ 已更改 remote URL 为 SSH 方式"
        echo ""
        echo "现在可以执行: git push origin main（无需密码）"
        ;;
        
    3)
        echo ""
        echo "=== 配置 Credential Helper ==="
        echo ""
        echo "选择缓存时间:"
        echo "1) 15 分钟（临时）"
        echo "2) 1 小时"
        echo "3) 永久存储（不推荐，密码明文存储）"
        echo ""
        read -p "请输入选项 (1-3): " cache_choice
        
        case $cache_choice in
            1)
                git config --global credential.helper 'cache --timeout=900'
                echo "✅ 已配置 15 分钟缓存"
                ;;
            2)
                git config --global credential.helper 'cache --timeout=3600'
                echo "✅ 已配置 1 小时缓存"
                ;;
            3)
                git config --global credential.helper store
                echo "✅ 已配置永久存储（密码将保存在 ~/.git-credentials）"
                ;;
            *)
                echo "❌ 无效选项"
                exit 1
                ;;
        esac
        echo ""
        echo "下次 git push 时输入密码后，会在指定时间内自动使用"
        ;;
        
    4)
        echo "退出"
        exit 0
        ;;
        
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "✅ 配置完成！"
echo "=========================================="
echo ""

