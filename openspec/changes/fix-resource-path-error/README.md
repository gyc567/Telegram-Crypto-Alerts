# Bug修复：资源文件路径错误

## 📋 概述

本OpenSpec提案用于修复资源文件路径计算错误，该错误导致应用无法启动。

---

## 🐛 Bug描述

### 错误信息
```python
FileNotFoundError: [Errno 2] No such file or directory:
'/home/runner/workspace/src/config/resources/default_config.json'

FileNotFoundError: [Errno 2] No such file or directory:
'/home/runner/workspace/src/config/resources/indicator_format_reference.json'
```

### 问题位置
**文件**: `src/config/__init__.py`
**行号**: 98-104
**错误类型**: FileNotFoundError

### 根因分析
在实施吃单监控时间窗口可配置化功能时（提交 `053917f`），我们将 `config.py` 的内容移动到 `config/__init__.py`，但**路径计算逻辑没有相应调整**。

**错误路径计算**:
```python
# 错误代码
__file__ = "src/config/__init__.py"
RESOURCES_ROOT = join(dirname(abspath(__file__)), "resources")
# 结果: src/config/resources/ ❌ (不存在)
```

**正确路径应该是**:
```python
# 正确代码
__file__ = "src/config/__init__.py"
src_dir = dirname(dirname(abspath(__file__)))  # 向上2级到src/
RESOURCES_ROOT = join(src_dir, "resources")
# 结果: src/resources/ ✅ (存在)
```

### 影响范围
- **应用无法启动**: setup.py 和 indicators.py 都会失败
- **功能完全不可用**: 用户无法使用任何功能
- **严重程度**: 高 (P0)

---

## 🎯 修复目标

1. **修正路径计算**
   - 将 `RESOURCES_ROOT` 从 `src/config/resources/` 改为 `src/resources/`
   - 将 `TA_DB_PATH` 从 `src/config/resources/indicator_format_reference.json` 改为 `src/resources/indicator_format_reference.json`
   - 将 `WHITELIST_ROOT` 从 `src/config/whitelist/` 改为 `src/whitelist/`
   - 将 `AGG_DATA_LOCATION` 从 `src/config/temp/ta_aggregate.json` 改为 `src/temp/ta_aggregate.json`

2. **使用更可靠的路径计算方法**
   - 避免嵌套的 `dirname()` 调用
   - 添加清晰的注释说明路径层级

---

## 📁 相关文件

- **问题文件**: `src/config/__init__.py`
- **影响文件**:
  - `src/user_configuration.py` (第26行, 40行)
  - `src/indicators.py` (第50行)
- **严重程度**: 高 (P0) - 应用无法启动

---

## 🛠️ 修复方案

### 修复内容 (src/config/__init__.py)

**修复前**:
```python
"""DATABASE PREFERENCES & PATHS"""
USE_MONGO_DB = False
WHITELIST_ROOT = join(dirname(abspath(__file__)), "whitelist")
RESOURCES_ROOT = join(dirname(abspath(__file__)), "resources")
TA_DB_PATH = join(
    dirname(abspath(__file__)), "resources/indicator_format_reference.json"
)
AGG_DATA_LOCATION = join(dirname(abspath(__file__)), "temp/ta_aggregate.json")
```

**修复后**:
```python
"""DATABASE PREFERENCES & PATHS"""
USE_MONGO_DB = False
# Calculate paths relative to the src directory (parent of config directory)
# __file__ is src/config/__init__.py, so we go up 2 levels to get to src/
src_dir = dirname(dirname(abspath(__file__)))
WHITELIST_ROOT = join(src_dir, "whitelist")
RESOURCES_ROOT = join(src_dir, "resources")
TA_DB_PATH = join(RESOURCES_ROOT, "indicator_format_reference.json")
AGG_DATA_LOCATION = join(src_dir, "temp/ta_aggregate.json")
```

### 关键变更
1. **计算 `src_dir`**: `src_dir = dirname(dirname(abspath(__file__)))`
2. **使用 `src_dir` 构建所有路径**: 避免重复的 `dirname()` 调用
3. **添加注释**: 解释路径层级关系
4. **简化 `TA_DB_PATH`**: 使用 `RESOURCES_ROOT` 变量而不是重复路径

---

## 🔍 验证方案

### 测试步骤
1. **导入测试**
   ```python
   from src.config import RESOURCES_ROOT, TA_DB_PATH
   ```

2. **路径验证**
   ```python
   import os
   assert os.path.exists(RESOURCES_ROOT)
   assert os.path.exists(TA_DB_PATH)
   assert "src/resources" in RESOURCES_ROOT
   ```

3. **功能测试**
   ```python
   from src.user_configuration import LocalUserConfiguration
   from src.indicators import TADatabaseClient
   ```

### 预期结果
- ✅ 资源文件路径正确 (`src/resources/`)
- ✅ 所有文件存在性检查通过
- ✅ 应用可以正常启动
- ✅ setup.py 正常工作
- ✅ 所有功能可用

---

## ⏰ 实施时间

**预计时间**: 5分钟
**优先级**: 高 (P0)
**复杂度**: 低

---

## 📊 影响评估

### 影响范围
- **功能影响**: 应用无法启动 → 应用可以正常启动
- **用户影响**: 所有用户无法使用 → 所有功能可用
- **业务影响**: 服务完全中断 → 服务恢复正常

### 风险评估
- **风险等级**: 低
- **回滚难度**: 容易（只需恢复前一版本）
- - **数据风险**: 无（只修改路径，不修改数据）

---

## 📝 预防措施

1. **路径计算标准化**
   - 为 `config` 模块创建专门的路径工具函数
   - 统一路径计算逻辑
   - 添加单元测试验证路径正确性

2. **代码审查增强**
   - 所有路径修改必须经过审查
   - 重点关注文件系统交互代码
   - 添加自动化测试检查文件存在性

3. **CI/CD 增强**
   - 在 CI 中添加文件存在性检查
   - 添加导入测试
   - 添加路径验证测试

---

## 📞 支持

如有问题或需要支持，请：

1. 查看错误日志确认路径错误
2. 检查 `src/config/__init__.py` 路径设置
3. 验证资源文件存在性
4. 参考修复方案

---

**Bug编号**: BUG-2025-0117
**创建日期**: 2025-11-10
**状态**: ✅ 已修复
**优先级**: 高 (P0)
**负责人**: Claude Code

---

## ✅ 修复完成

**修复时间**: 2025-11-10
**提交ID**: `a6520c3`

**修复内容**:
1. ✅ 修正 `RESOURCES_ROOT` 路径: `src/config/resources/` → `src/resources/`
2. ✅ 修正 `TA_DB_PATH` 路径: `src/config/resources/indicator_format_reference.json` → `src/resources/indicator_format_reference.json`
3. ✅ 修正 `WHITELIST_ROOT` 路径: `src/config/whitelist/` → `src/whitelist/`
4. ✅ 修正 `AGG_DATA_LOCATION` 路径: `src/config/temp/` → `src/temp/`
5. ✅ 使用更可靠的路径计算方法: `src_dir = dirname(dirname(abspath(__file__)))`
6. ✅ 添加清晰的注释说明路径层级

**验证结果**:
- ✅ 模块导入成功: `from src.config import RESOURCES_ROOT, TA_DB_PATH`
- ✅ 路径正确: `RESOURCES_ROOT = /path/to/src/resources`
- ✅ 文件存在性检查通过: `default_config.json`, `indicator_format_reference.json`
- ✅ 相关模块导入成功: `LocalUserConfiguration`, `TADatabaseClient`, `TelegramBot`
- ✅ 无 `FileNotFoundError`
- ✅ 应用可以正常启动

**统计信息**:
- 变更文件: 2个 (src/config/__init__.py, openspec文档)
- 新增行数: 207行
- 删除行数: 6行
- 新增文件: 1个 (bug修复文档)
