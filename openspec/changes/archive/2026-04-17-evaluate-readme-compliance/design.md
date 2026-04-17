## Context

sim_docs 系统是从早期分散的 skill 脚本架构迁移而来的统一 Python 包。当前存在以下问题：

1. **代码 bug**：`pdf_engine.py` 第 207 行 `extract_tables` 参数遮蔽同名函数，当 `extract_tables=True` 时会触发 `TypeError`
2. **重复代码**：`compare_engine.py` 和 `cli.py` 都有 `_generate_diff_report` 函数，功能略有差异
3. **路径依赖分散**：6 个模块各自注入 `.claude/skills/__libs__` 到 `sys.path`，结构脆弱
4. **文档与代码不一致**：三份文档描述的模块路径、CLI 命令、架构图与实际代码存在偏差

## Goals / Non-Goals

**Goals:**
- 修复运行时 bug，确保 `pdf_engine.extract_pdf(extract_tables=True)` 正常工作
- 消除重复代码，统一 diff report 生成逻辑
- 集中 sys.path 操作，降低路径依赖的脆弱性
- 同步文档与代码实际状态

**Non-Goals:**
- 不重构整体架构（保持 Agent + generic tools 模式）
- 不增加新功能（仅修复和同步）
- 不移动 validate_engine 对外部 validators 的依赖（保持向后兼容）
- 不增加测试覆盖（当前任务范围外）

## Decisions

### 1. 修复 pdf_engine 参数遮蔽

**方案**：将参数名 `extract_tables` 改为 `include_tables`

**理由**：
- 语义清晰："是否包含表格"而非"提取表格"
- 不改变函数签名结构，仅重命名参数
- 调用方需同步更新参数名

**替代方案**：
- 在函数内部用别名（如 `_extract_tables`）→ 增加混乱，不推荐
- 移动函数到单独模块 → 过度重构，不必要

### 2. 统一 diff report 逻辑

**方案**：保留 `compare_engine.generate_diff_report`（支持 style diff），删除 `cli.py` 中的重复版本，在 `cli.py` 中调用 engine 版本

**理由**：
- engine 版本功能更完整（含 style diff）
- 保持 engine 作为单一真实来源
- CLI 仅做参数转换和输出格式化

### 3. sys.path 集中化

**方案**：在 `sim_docs/__init__.py` 中统一注入路径，其他模块直接 import

**理由**：
- 包初始化时一次性设置
- 消除各模块重复的 `sys.path.insert`
- 未来迁移时可集中修改

**风险**：若 `__init__.py` 未被导入则路径未设置 → 缓解：CLI 入口 `cli.py` 确保先导入 `__init__.py`

### 4. 文档同步策略

**方案**：逐项核对三份文档，更新不一致部分

- `sim_docs/README.md`：补充 Skill Layout 中缺失的文件
- `README.md`：验证 Legacy Scripts 段落路径有效性
- `CLAUDE.md`：移除已删除的旧脚本引用，更新 Skill Layout

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| `include_tables` 参数名改变可能影响现有调用方 | CLI 已使用 `--tables` flag，内部映射不变；Python API 调用方需更新 |
| sys.path 集中化可能导致某些边缘导入失败 | 保持现有导入方式不变，仅改变路径设置时机 |
| 文档更新后可能再次 drift | 非代码层面的风险，需人工维护 |