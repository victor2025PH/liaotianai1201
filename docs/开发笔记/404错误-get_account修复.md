# 404 错误 - get_account 修复

## 问题

访问 `/api/v1/group-ai/accounts/639277358115` 返回 404 Not Found。

## 原因

`get_account` 函数只检查 `AccountManager`（内存中运行的账号），不检查数据库中的远程服务器账号，导致：
- 远程账号在列表中可见（因为 `list_accounts` 从数据库查询）
- 但获取详情时返回 404（因为 `get_account` 只检查 AccountManager）

## 修复方案

修改 `get_account` 函数，使其支持：
1. 先检查 AccountManager（内存中运行的账号）
2. 如果不存在，检查数据库（包含远程服务器账号）
3. 如果数据库中存在，返回账号详情（状态为 offline）
4. 如果都不存在，返回 404

## 修复内容

### 修改 `admin-backend/app/api/group_ai/accounts.py`

- 在 `get_account` 函数中添加数据库查询逻辑
- 如果账号在数据库中，从数据库记录构建 `AccountResponse`
- 添加详细日志以便调试

## 修复后的逻辑流程

```
1. 检查 AccountManager → 找到？返回实时状态
2. 检查数据库 → 找到？返回数据库记录（状态：offline）
3. 都不存在 → 返回 404
```

## 验证

修复后，访问 `/api/v1/group-ai/accounts/639277358115` 应该：
- ✅ 如果账号在数据库中，返回账号详情
- ✅ 状态显示为 "offline"（如果不在 AccountManager 中）
- ✅ 不再返回 404

## 状态

✅ **修复已完成**  
✅ **后端服务已重启**  
⏳ **等待测试验证**

---

**修复完成！请刷新浏览器测试。**
