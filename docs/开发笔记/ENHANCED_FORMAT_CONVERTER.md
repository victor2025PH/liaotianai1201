# 增强格式转换器文档

## 概述

增强格式转换器（`EnhancedFormatConverter`）是一个智能文档格式转换工具，支持多种文档格式的自动识别和转换，包括角色信息识别、自动修复和详细的错误提示。

## 主要功能

### 1. 多格式支持

#### 支持的格式类型

- **新格式YAML**：包含 `script_id` 和 `scenes` 字段的标准格式
- **旧格式YAML（列表）**：包含 `step`、`actor`、`action`、`lines` 字段的列表格式
- **旧格式YAML（字典）**：包含 `steps` 字段的字典格式
- **Markdown格式**：以 `#` 开头的Markdown文档
- **纯文本格式**：普通文本内容

#### 格式检测

```python
format_type, format_info = converter.detect_format(content)
# format_type: "new_yaml", "old_yaml_list", "old_yaml_dict", "markdown", "plain_text"
# format_info: {"structure": "...", "needs_conversion": True/False}
```

### 2. 角色信息识别

#### 支持的角色类型

- **管理员**：管理员、admin、administrator、管理
- **审核员**：审核员、reviewer、审核、审核人员
- **接待员**：接待员、receptionist、接待、客服
- **siya**：siya、Siya、SIYA
- **huge**：huge、Huge、HUGE
- **用户**：用户、user、成员、member

#### 角色提取

```python
roles = converter.extract_roles(content)
# 返回: [
#   {
#     "name": "管理员",
#     "keywords": ["管理员", "admin", ...],
#     "occurrences": [...],
#     "count": 3
#   },
#   ...
# ]
```

#### 角色匹配

```python
role_mapping = converter.match_roles_to_actors(roles, actors)
# 返回: {"管理员": "admin", "审核员": "reviewer", ...}
```

### 3. 自动验证和修复

#### 验证项目

- ✅ `script_id` 类型验证（确保是字符串）
- ✅ `version` 类型验证（确保是字符串）
- ✅ `scenes` 结构验证（确保是列表）
- ✅ 场景完整性验证（确保有 id、triggers、responses）
- ✅ 字段类型修复（自动转换错误类型）

#### 修复示例

```python
data, warnings = converter.validate_and_fix(data)
# warnings: [
#   "script_id 类型错误 (int)，已转换为字符串",
#   "场景 0 缺少 id，已自动生成: scene_1",
#   ...
# ]
```

### 4. 错误提示和建议

#### 错误类型和建议

- **YAML解析错误**：
  - 检查YAML格式是否正确
  - 确保缩进使用空格而非Tab
  - 检查是否有未闭合的引号或括号

- **script_id错误**：
  - 确保YAML中包含 script_id 字段（新格式）或 step/actor 字段（旧格式）
  - 如果是旧格式，请先使用「智能转换」功能

- **scenes错误**：
  - 确保包含 scenes 字段（新格式）或 steps 字段（旧格式）
  - 检查场景结构是否正确

- **类型错误**：
  - 检查字段类型是否正确（script_id 和 version 应为字符串）
  - 确保数值字段格式正确

## 使用示例

### 基本使用

```python
from group_ai_service.enhanced_format_converter import EnhancedFormatConverter

converter = EnhancedFormatConverter()

# 转换文档
converted_data, warnings = converter.convert_with_enhanced_detection(
    content=old_yaml_content,
    script_id="my_script",
    script_name="我的剧本"
)

# 验证和修复
fixed_data, fix_warnings = converter.validate_and_fix(converted_data)
warnings.extend(fix_warnings)

# 使用转换后的数据
print(f"转换成功，共 {len(fixed_data['scenes'])} 个场景")
if warnings:
    print(f"警告: {', '.join(warnings)}")
```

### API使用

```python
# POST /api/v1/group-ai/scripts/convert
{
    "yaml_content": "...",
    "script_id": "001",
    "script_name": "我的剧本",
    "optimize": false
}

# 响应
{
    "success": true,
    "yaml_content": "...",
    "script_id": "001",
    "version": "1.0",
    "description": "我的剧本",
    "scene_count": 5,
    "message": "格式轉換成功。注意：識別到 2 個角色: 管理员, 审核员"
}
```

## 错误处理

### 错误响应格式

```json
{
    "detail": "格式轉換失敗: YAML解析失败: ...\n\n建議：\n  • 检查YAML格式是否正确，确保缩进使用空格而非Tab\n  • 确保所有键值对格式正确（key: value）\n  • 检查是否有未闭合的引号或括号"
}
```

### 常见错误和解决方案

1. **类型错误**：
   - 问题：`script_id` 或 `version` 不是字符串
   - 解决：系统自动转换为字符串，无需手动处理

2. **格式识别失败**：
   - 问题：无法识别文档格式
   - 解决：检查文档是否包含必要的字段标识

3. **角色识别失败**：
   - 问题：无法识别角色信息
   - 解决：确保文档中包含角色关键词（管理员、审核员等）

## 技术细节

### 格式检测算法

1. 检查新格式标识（`script_id:` + `scenes:`）
2. 检查旧格式列表标识（`step:` + `actor:` + `action:` + `lines:`）
3. 检查旧格式字典标识（`steps:`）
4. 检查Markdown标识（`#` 或 ````）
5. 尝试YAML解析
6. 默认为纯文本

### 角色识别算法

1. 遍历所有角色关键词
2. 在文档中搜索关键词
3. 提取上下文（前后2行）
4. 统计出现次数
5. 生成角色信息列表

### 验证和修复流程

1. 类型检查（script_id、version）
2. 结构检查（scenes）
3. 场景完整性检查
4. 自动修复错误
5. 生成警告信息

## 最佳实践

1. **提供script_id**：即使文档中没有，也应在转换时提供
2. **检查警告**：转换后检查警告信息，了解自动修复的内容
3. **验证结果**：转换后验证场景数量和结构
4. **错误处理**：根据错误建议进行修正

## 性能考虑

- 格式检测：O(n)，n为文档行数
- 角色识别：O(n*m)，n为行数，m为角色关键词数
- 转换：取决于文档大小和格式复杂度
- 验证：O(s)，s为场景数量

## 扩展性

### 添加新格式支持

```python
# 在 FORMAT_PATTERNS 中添加
FORMAT_PATTERNS["custom_format"] = {
    "indicators": ["custom_key:"],
    "structure": "dict"
}
```

### 添加新角色类型

```python
# 在 ROLE_KEYWORDS 中添加
ROLE_KEYWORDS["新角色"] = ["新角色", "new_role", "新角色关键词"]
```

## 总结

增强格式转换器提供了：
- ✅ 多格式自动识别
- ✅ 角色信息提取
- ✅ 自动验证和修复
- ✅ 详细的错误提示
- ✅ 转换建议

这些功能确保了各类文档都能成功转换，并提供了清晰的错误处理方案。

