# 分配剧本问题 - 账号ID匹配修复

## 问题发现

在分配剧本时，即使扫描到了远程服务器上的账号，也可能因为账号ID匹配失败而导致"账号不存在"的错误。

## 根本原因

账号ID匹配时可能出现的类型不一致问题：
- 请求中的 `account_id` 可能是字符串 `"639277358115"`
- 扫描到的账号ID可能是字符串，但格式不同（可能有空格、类型不同等）

## 修复方案

### 修复账号ID匹配逻辑

在 `update_account` 函数中，增强账号ID匹配逻辑：

```python
# 修复前
server_account = next((acc for acc in server_accounts if acc.account_id == account_id), None)

# 修复后
account_id_str = str(account_id).strip()
server_account = next(
    (acc for acc in server_accounts if str(acc.account_id).strip() == account_id_str),
    None
)
logger.info(f"账号ID匹配: 目标='{account_id_str}', 类型={type(account_id).__name__}, 找到={server_account is not None}")
```

**改进点**：
- 统一转换为字符串类型
- 去除前后空格
- 添加匹配日志，便于调试

## 完整的错误处理流程

1. **接收请求** → 记录日志
2. **检查 AccountManager** → 记录结果
3. **检查数据库** → 记录结果
4. **如果有 server_id**：
   - 检查服务器是否存在
   - 扫描服务器账号
   - **账号ID匹配**（修复后）
   - 创建数据库记录
5. **详细错误日志** → 如果失败，记录所有相关信息

## 测试验证

修复后，日志应该显示：
```
账号ID匹配: 目标='639277358115', 类型=str, 找到=True
```

或者如果匹配失败：
```
账号ID匹配: 目标='639277358115', 类型=str, 找到=False
扫描到的账号ID列表: ['639277358115', '639277358116', ...]
```

## 状态

✅ 账号ID匹配逻辑已修复  
✅ 详细日志已添加  
⏳ 等待服务重启后测试
