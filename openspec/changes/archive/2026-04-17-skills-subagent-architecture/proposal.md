## Why

当前 skills 架构存在根本问题：主 agent 直接执行所有任务，没有评估层。这导致：

1. **错误静默发生**：主 agent 自己干活自己评判，没有独立检查
2. **流程不完整**：evaluate-spec 未被强制调用，common-sense check 被跳过
3. **工具报错被忽略**：缺少"必须报告错误"的机制
4. **上下文污染**：所有任务在同一上下文，互相干扰

**解决方案**：引入 subagent 架构。主 agent 只调度和评估，不直接执行任务。具体任务由独立 subagent 执行，主 agent 检查 subagent 输出的完整性和正确性。

## What Changes

- **新架构**：两层架构 - 主 agent（调度者/评估者）+ subagent（执行者）
- **新 prompt 模板**：为 extract-spec、evaluate-spec、check-thesis 创建 subagent prompt 模板文件
- **评估层逻辑**：主 agent 必须检查 subagent 输出的 cross_validation、tool_errors、common_sense_check 字段
- **拒绝机制**：subagent 输出不符合要求时，主 agent 拒绝并要求重做

## Capabilities

### New Capabilities

- `font-extractor-subagent`: 字体规则提取 subagent，执行三源交叉验证（样式定义 → paragraph-stats → query-text）
- `layout-extractor-subagent`: 页面设置提取 subagent
- `heading-extractor-subagent`: 标题规则提取 subagent
- `spec-evaluator-subagent`: spec 评估 subagent，执行 common-sense check、structure check、conflicts check
- `rule-checker-subagent`: 确定性规则检查 subagent（batch-check 执行）

### Modified Capabilities

- `extract-spec`: 从"主 agent 直接执行"改为"主 agent 调度 font/layout/heading subagent 并评估输出"
- `evaluate-spec`: 从"主 agent 直接评估"改为"主 agent 调度 evaluator subagent 并检查评估完整性"
- `check-thesis`: 从"主 agent 直接检查"改为"主 agent 调度 checker subagent 并核实检查覆盖"

## Impact

- **SKILL.md 文件**：extract-spec、evaluate-spec、check-thesis 的 SKILL.md 需重写，定义调度协议而非执行指令
- **新增 prompt 模板文件**：约 6-8 个 subagent prompt 模板文件
- **流程强制**：主 agent 必须执行评估层逻辑，不能跳过
- **输出格式标准化**：subagent 输出必须包含 status、cross_validation、tool_errors、common_sense_check 字段