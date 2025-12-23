# Git Push 认证配置指南

## 问题说明

当使用 HTTPS 方式连接 GitHub 时（`https://github.com/...`），每次 `git push` 都需要输入用户名和密码。

## 解决方案

### 方案 1: 使用 Personal Access Token（推荐，最简单）

**步骤 1: 在 GitHub 创建 Personal Access Token**

1. 打开：https://github.com/settings/tokens
2. 点击 **Generate new token (classic)**
3. 填写信息：
   - Note: `Git Push - Server`（随意命名）
   - Expiration: 选择合适的时间（如 90 天或 No expiration）
   - 勾选权限：至少需要 `repo` 权限
4. 点击 **Generate token**
5. **重要：立即复制 token**（只显示一次，类似 `ghp_xxxxxxxxxxxxxxxxxxxx`）

**步骤 2: 在服务器上配置**

```bash
# 方法 A: 使用 credential helper 存储 token（推荐）
git config --global credential.helper store

# 方法 B: 直接使用 token 作为密码
# 当 git push 提示输入密码时，粘贴 token（不是 GitHub 密码）
```

**步骤 3: 首次推送（输入 token）**

```bash
git push origin main
# Username for 'https://github.com': victor2025PH
# Password for 'https://github.com/victor2025PH': <粘贴你的 token>
```

之后就不需要再输入密码了。

---

### 方案 2: 改用 SSH 方式（更安全，推荐长期使用）

**步骤 1: 在服务器上生成 SSH 密钥**

```bash
# 生成 SSH 密钥（如果还没有）
ssh-keygen -t ed25519 -C "server-git-push" -f ~/.ssh/id_ed25519_github
# 直接按 Enter（不设置密码）

# 查看公钥
cat ~/.ssh/id_ed25519_github.pub
```

**步骤 2: 将公钥添加到 GitHub**

1. 复制公钥内容（`cat ~/.ssh/id_ed25519_github.pub` 的输出）
2. 打开：https://github.com/settings/ssh/new
3. 填写：
   - Title: `Server Git Push`（随意命名）
   - Key: 粘贴公钥内容
4. 点击 **Add SSH key**

**步骤 3: 配置 Git 使用 SSH**

```bash
# 查看当前 remote URL
git remote -v

# 改为 SSH 方式
git remote set-url origin git@github.com:victor2025PH/liaotianai1201.git

# 配置 SSH 使用特定密钥
cat >> ~/.ssh/config << 'EOF'
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github
    IdentitiesOnly yes
EOF
chmod 600 ~/.ssh/config

# 测试连接
ssh -T git@github.com
# 应该看到: Hi victor2025PH! You've successfully authenticated...
```

**步骤 4: 现在可以直接 push**

```bash
git push origin main
# 不再需要输入密码
```

---

### 方案 3: 使用 credential helper 缓存（临时方案）

```bash
# 缓存密码 15 分钟
git config --global credential.helper 'cache --timeout=900'

# 或永久存储（注意：密码以明文存储在 ~/.git-credentials）
git config --global credential.helper store
```

---

## 快速配置脚本

在服务器上执行：

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/configure_git_push.sh
```

脚本会引导您完成配置。

---

## 推荐方案对比

| 方案 | 安全性 | 便捷性 | 推荐度 |
|------|--------|--------|--------|
| Personal Access Token | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| SSH 密钥 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Credential Helper | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

**推荐**: 方案 2（SSH 方式），最安全且长期使用更方便。

