# 全自動部署系統使用指南

## 功能特點

1. **全自動部署** - 無需手動輸入密碼，一鍵部署服務器
2. **智能分配** - 根據風控策略自動分配Session文件到不同服務器
3. **風控保護** - 防止同一IP分配過多帳號，實現地理位置分散
4. **統一管理** - 通過主節點控制器管理所有工作節點

## 快速開始

### 1. 安裝依賴

```bash
pip install -r scripts/deployment/requirements_deploy.txt
```

或者手動安裝：
```bash
pip install pexpect paramiko
```

### 2. 添加服務器

```bash
python scripts/deployment/master_controller.py \
    --add-server "165.154.254.99,root,Along2025!!!,worker-01,5,LosAngeles"
```

參數說明：
- `165.154.254.99`: 服務器IP地址
- `root`: SSH用戶名
- `Along2025!!!`: SSH密碼
- `worker-01`: 節點ID（可選，自動生成）
- `5`: 最大帳號數
- `LosAngeles`: 地理位置標識（用於風控）

### 3. 部署服務器

```bash
# 部署單個服務器
python scripts/deployment/master_controller.py --deploy worker-01

# 部署所有服務器
python scripts/deployment/master_controller.py --deploy-all
```

### 4. 分配Session文件

```bash
# 自動分配Session文件到所有服務器
python scripts/deployment/master_controller.py --distribute --sessions-dir sessions
```

### 5. 查看狀態

```bash
# 查看所有服務器狀態
python scripts/deployment/master_controller.py --status
```

## 使用示例

### 示例1: 部署單個服務器

```bash
# 直接使用auto_deploy.py部署
python scripts/deployment/auto_deploy.py \
    --host 165.154.254.99 \
    --user root \
    --password "Along2025!!!" \
    --node-id worker-01 \
    --max-accounts 5 \
    --telegram-api-id "your_api_id" \
    --telegram-api-hash "your_api_hash" \
    --openai-api-key "your_openai_key"
```

### 示例2: 批量部署多個服務器

```bash
# 1. 添加所有服務器
python scripts/deployment/master_controller.py \
    --add-server "165.154.254.99,root,password1,worker-01,5,LA"

python scripts/deployment/master_controller.py \
    --add-server "165.154.254.100,root,password2,worker-02,5,NY"

python scripts/deployment/master_controller.py \
    --add-server "165.154.254.101,root,password3,worker-03,5,SF"

# 2. 部署所有服務器
python scripts/deployment/master_controller.py --deploy-all

# 3. 分配Session文件
python scripts/deployment/master_controller.py --distribute
```

### 示例3: 手動分配Session文件

```bash
# 使用Session分配器
python scripts/deployment/session_distributor.py \
    --register-node "worker-01,165.154.254.99,8000,5,LA" \
    --register-node "worker-02,165.154.254.100,8000,5,NY" \
    --distribute \
    --sessions-dir sessions \
    --report
```

## 風控策略說明

系統會自動應用以下風控策略：

1. **IP分散**: 避免同一IP分配超過3個帳號
2. **地理位置分散**: 優先分配到不同地區的服務器
3. **負載均衡**: 優先分配到負載較低的節點
4. **時間分散**: 避免同時分配大量帳號
5. **風險等級**: 根據Session風險等級調整分配策略

## 配置文件

配置文件保存在 `data/master_config.json`:

```json
{
  "servers": {
    "worker-01": {
      "host": "165.154.254.99",
      "user": "root",
      "password": "Along2025!!!",
      "node_id": "worker-01",
      "deploy_dir": "/opt/group-ai",
      "max_accounts": 5,
      "location": "LosAngeles",
      "telegram_api_id": "",
      "telegram_api_hash": "",
      "openai_api_key": ""
    }
  }
}
```

## 數據庫

Session分配信息保存在 `data/session_distribution.db`:

- `server_nodes`: 服務器節點信息
- `session_assignments`: Session分配記錄
- `assignment_history`: 分配歷史（用於風控分析）

## 常見問題

### Q: 如何修改風控策略？

A: 編輯 `session_distributor.py` 中的 `RiskControlStrategy` 類，調整風險分數計算邏輯。

### Q: 如何手動上傳Session文件？

A: Session文件會自動上傳，如果自動上傳失敗，可以手動執行：

```bash
scp session_file.session root@165.154.254.99:/opt/group-ai/sessions/
```

### Q: 如何查看分配報告？

A: 執行：

```bash
python scripts/deployment/session_distributor.py --report
```

### Q: 如何重新分配Session文件？

A: 刪除數據庫文件 `data/session_distribution.db`，然後重新執行分配命令。

## 安全建議

1. **保護配置文件**: 不要將包含密碼的配置文件提交到版本控制
2. **使用SSH密鑰**: 部署完成後，建議配置SSH密鑰認證
3. **定期備份**: 定期備份配置文件和數據庫
4. **監控日誌**: 定期檢查服務器日誌，確保正常運行

## 下一步

部署完成後，您可以：

1. 通過前端管理界面管理帳號
2. 監控服務器狀態和帳號運行情況
3. 根據需要調整風控策略
4. 添加更多服務器節點

詳細使用說明請參考：
- [分散式部署方案](../../docs/部署方案/分散式部署方案.md)
- [帳號安全運行指南](../../docs/使用说明/账号安全运行指南.md)

