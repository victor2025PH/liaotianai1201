# 格式转换错误修复说明

## 问题分析

### 问题描述
用户粘贴旧格式YAML后直接点击「创建」按钮，系统报错："剧本格式错误:缺少 script_id 字段"。

### 根本原因
1. **缺少自动检测**：系统没有在创建前自动检测YAML格式
2. **转换逻辑不完善**：规则转换对某些格式变体处理不当
3. **错误提示不明确**：没有明确提示用户需要先转换格式

## 解决方案

### 1. 自动格式检测和转换

在 `handleCreate` 函数中添加了自动检测逻辑：

```typescript
// 检查是否为旧格式
const isOldFormat = yamlContent.includes("step:") && 
                   yamlContent.includes("actor:") && 
                   !yamlContent.includes("script_id:")

if (isOldFormat) {
  // 提示用户是否自动转换
  const shouldConvert = confirm("檢測到舊格式YAML，是否自動轉換為新格式？")
  
  if (shouldConvert) {
    // 自动转换并创建
    await convertFormat(...)
    await createScript(...)
  }
}
```

### 2. 改进规则转换逻辑

#### 2.1 处理列表格式
```python
if isinstance(old_data, list):
    # 处理步骤列表
    for idx, step in enumerate(old_data):
        if not isinstance(step, dict):
            continue
        # 转换逻辑...
```

#### 2.2 处理lines字段
```python
lines = step.get("lines", [])
if isinstance(lines, list):
    for line in lines:
        if line:  # 跳过空行
            scene["responses"].append({"template": str(line).strip()})
elif isinstance(lines, str):
    # 如果lines是字符串，直接添加
    scene["responses"].append({"template": lines.strip()})
```

#### 2.3 验证转换结果
```python
# 验证转换结果
if not new_data.get("scenes"):
    raise ValueError("转换后没有生成任何场景，请检查输入格式")
```

### 3. 增强AI转换验证

#### 3.1 降级机制
```python
try:
    converted = self._convert_with_ai(old_data, script_id, script_name)
    # 验证转换结果
    if not converted.get("script_id"):
        logger.warning("AI转换结果缺少script_id，使用规则转换")
        converted = self._convert_with_rules(old_data, script_id, script_name)
    return converted
except Exception as e:
    logger.warning(f"AI转换失败，使用规则转换: {e}")
    return self._convert_with_rules(old_data, script_id, script_name)
```

#### 3.2 结果验证
```python
def _validate_and_optimize(self, data, script_id, script_name):
    # 确保必要字段存在
    if not data.get("script_id"):
        data["script_id"] = script_id or "converted_script"
    
    # 验证scenes格式
    if "scenes" not in data:
        data["scenes"] = []
    elif not isinstance(data["scenes"], list):
        # 如果是字典，转换为列表
        if isinstance(data["scenes"], dict):
            data["scenes"] = [data["scenes"]]
        else:
            data["scenes"] = []
    
    # 验证每个场景
    for scene in data["scenes"]:
        if "id" not in scene:
            scene["id"] = f"scene_{idx + 1}"
        # ...
```

## 修复内容总结

### 后端修复
1. ✅ 改进 `_convert_with_rules` 方法，更好地处理各种格式变体
2. ✅ 增强 `_validate_and_optimize` 方法，确保转换结果完整
3. ✅ 添加AI转换失败时的自动降级机制
4. ✅ 改进错误处理和验证逻辑

### 前端修复
1. ✅ 在创建前自动检测旧格式
2. ✅ 自动提示用户是否转换
3. ✅ 支持自动转换后直接创建
4. ✅ 改进错误提示信息

## 测试建议

### 测试场景1：直接创建旧格式
1. 粘贴旧格式YAML
2. 填写script_id和name
3. 直接点击「创建」
4. **预期**：系统提示是否自动转换

### 测试场景2：手动转换
1. 粘贴旧格式YAML
2. 点击「智能转换」
3. 确认转换结果
4. 点击「创建」
5. **预期**：成功创建

### 测试场景3：自动转换创建
1. 粘贴旧格式YAML
2. 填写script_id和name
3. 点击「创建」
4. 在提示中选择「确定」
5. **预期**：自动转换并创建成功

## 注意事项

1. **script_id必须填写**：即使自动转换，也需要用户提供script_id
2. **转换可能失败**：如果转换失败，会提示用户手动转换
3. **AI服务依赖**：如果OpenAI API不可用，会自动使用规则转换

## 后续优化

1. **更智能的格式检测**：使用更精确的规则检测格式
2. **批量转换**：支持批量转换多个剧本
3. **转换历史**：保存转换历史，支持回滚
4. **预览功能**：转换前预览转换结果

