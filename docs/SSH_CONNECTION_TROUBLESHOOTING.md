# SSH 連接問題排查指南

## 問題描述

在 GitHub Actions 部署過程中，可能遇到以下 SSH 連接錯誤：

1. `ssh: handshake failed: read tcp ...:22: read: connection reset by peer`
2. `ssh: unexpected packet in response to channel open`
3. `wait: remote command exited without exit status or exit signal`

## 可能原因

1. **網絡不穩定**：GitHub Actions runner 到服務器的網絡路徑不穩定
2. **SSH 服務器配置**：服務器端的 SSH 配置可能限制了連接
3. **防火牆或安全組**：可能阻斷了連接
4. **連接超時**：長時間執行的腳本導致連接超時

## 解決方案

### 1. 檢查服務器端 SSH 配置

在服務器上執行以下命令檢查 SSH 配置：

```bash
# 檢查 SSH 配置
sudo nano /etc/ssh/sshd_config

# 確保以下配置合理：
# ClientAliveInterval 60
# ClientAliveCountMax 3
# MaxStartups 10:30:100
# MaxSessions 10

# 重啟 SSH 服務
sudo systemctl restart sshd
```

### 2. 檢查 SSH 密鑰權限

確保服務器上的 SSH 密鑰權限正確：

```bash
# 在服務器上執行
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### 3. 檢查防火牆設置

確保服務器的防火牆允許來自 GitHub Actions IP 範圍的連接：

```bash
# 查看 UFW 狀態
sudo ufw status

# 確保 SSH 端口開放
sudo ufw allow 22/tcp
```

### 4. 使用 GitHub Actions 重試機制

在 workflow 中添加重試邏輯（需要修改 workflow 文件）：

```yaml
- name: Deploy to Server
  uses: appleboy/ssh-action@v1.2.0
  # ... 其他配置 ...
  continue-on-error: false
  # 注意：appleboy/ssh-action 本身不支持重試，但可以在 step 層級添加重試
```

### 5. 將腳本分步驟執行

將長腳本拆分為多個較短的步驟，減少單次連接的時間：

```yaml
- name: Step 1 - Update Code
  uses: appleboy/ssh-action@v1.2.0
  with:
    script: |
      # 只執行代碼更新
      cd /home/ubuntu/telegram-ai-system
      git pull origin main

- name: Step 2 - Build Frontend
  uses: appleboy/ssh-action@v1.2.0
  with:
    script: |
      # 只執行前端構建
      cd /home/ubuntu/telegram-ai-system/saas-demo
      npm run build

# ... 更多步驟 ...
```

### 6. 將部署腳本上傳到服務器執行

使用 `scp` 或 `rsync` 先上傳腳本，然後執行：

```yaml
- name: Upload Deploy Script
  uses: appleboy/scp-action@master
  with:
    host: ${{ secrets.SERVER_HOST }}
    username: ${{ secrets.SERVER_USER }}
    key: ${{ secrets.SERVER_SSH_KEY }}
    source: "deploy.sh"
    target: "/tmp/"

- name: Execute Deploy Script
  uses: appleboy/ssh-action@v1.2.0
  with:
    script: |
      chmod +x /tmp/deploy.sh
      bash /tmp/deploy.sh
      rm /tmp/deploy.sh
```

### 7. 檢查服務器資源

確保服務器有足夠的資源（內存、CPU）來處理部署：

```bash
# 檢查系統資源
free -h
df -h
top
```

### 8. 檢查 SSH 日誌

在服務器上查看 SSH 日誌以了解連接問題：

```bash
# 查看 SSH 日誌
sudo tail -f /var/log/auth.log

# 或
sudo journalctl -u ssh -f
```

## 如果問題持續存在

如果上述方法都無法解決問題，可以考慮：

1. **手動部署**：使用本地腳本或直接 SSH 到服務器手動執行部署
2. **使用 Webhook**：在服務器上設置 webhook 監聽器，接收 GitHub webhook 觸發部署
3. **使用 CI/CD 服務**：考慮使用其他 CI/CD 服務（如 GitLab CI、Jenkins）或自託管的 runner

## 相關文件

- [GitHub Actions SSH 配置指南](./SETUP_GITHUB_ACTIONS_SSH.md)
- [部署腳本文檔](../deploy/README.md)
