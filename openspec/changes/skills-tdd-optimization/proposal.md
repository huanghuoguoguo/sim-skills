## Why

当前 skills 缺乏 SP（superpowers）方法论中的关键约束机制：
- **没有铁律**（Iron Law）：Agent 可以跳过前置条件
- **没有红旗**（Red Flags）：Agent 无法自检错误行为
- **没有借口表格**（Rationalization Table）：Agent 找借口时没有反驳
- **评估者不起作用**：evaluate-spec 没有程序化的常识检测

今天从天津理工大学模板提取 spec 时暴露了这些问题：
- Agent 把"宋体"当作西文字体写入 spec（常识错误）
- 工具调用报错被静默忽略
- evaluate-spec 没被调用

## What Changes

### Skills 方法论改造

采用 SP 的约束技术栈，改造核心 workflow skills：

| Skill | 改造内容 |
|-------|----------|
| `extract-spec` | 添加铁律、红旗、借口表格、Gate Function |
| `evaluate-spec` | 添加常识检测（程序化）、强制调用机制 |
| `check-thesis` | 添加红旗、完整性回溯强制 |

### 新增程序化检测

在 `sim_docs/spec_engine.py` 添加常识检测模式：

- 检测"中文字体作为西文字体"的常识冲突
- 检测"样式定义与实际使用不一致"是否被标注

### 强制调用链

建立 skill 链式调用：
- extract-spec **REQUIRED:** 调用 evaluate-spec
- evaluate-spec **REQUIRED:** 调用 spec-check 程序化检测

## Capabilities

### New Capabilities

- `skill-iron-law`: 铁律约束模式（NO X WITHOUT Y）
- `skill-rationalization-table`: 借口反驳表格模式
- `spec-common-sense-check`: spec.md 常识检测（程序化）

### Modified Capabilities

- `extract-spec`: 添加约束机制，确保 agent 不遗漏交叉验证
- `evaluate-spec`: 添加常识检测项，程序化验证

## Impact

- `.claude/skills/extract-spec/SKILL.md` — 添加约束章节
- `.claude/skills/evaluate-spec/SKILL.md` — 添加常识检测要求
- `.claude/skills/check-thesis/SKILL.md` — 添加红旗列表
- `sim_docs/spec_engine.py` — 添加常识检测逻辑
- `sim_docs/cli.py` — 添加 `--mode common-sense` 参数