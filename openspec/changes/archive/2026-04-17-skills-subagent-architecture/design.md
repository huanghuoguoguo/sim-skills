## Context

当前架构：主 agent 直接执行所有任务，SKILL.md 是执行指导文档。

问题：
- 主 agent 自己干活自己评判，没有独立评估层
- 工具错误被静默忽略
- 上下文污染，任务间互相干扰

约束：
- 使用 Claude Code 的 Agent tool 调用 subagent
- SP 方法论要求 prompt 模板文件定义 subagent 行为
- subagent 输出必须有标准化字段供主 agent 评估

## Goals / Non-Goals

**Goals:**
- 主 agent 只调度和评估，不直接执行任务
- 每个任务由独立 subagent 执行，上下文隔离
- 主 agent 必须检查 subagent 输出，拒绝错误结果
- 流程强制：评估层逻辑不可跳过

**Non-Goals:**
- 不改变现有 Python 工具代码（batch-check、paragraph-stats 等）
- 不引入新的外部依赖
- 不实现自动重试机制（subagent 返回 BLOCKED 时需要人工干预）

## Decisions

### Decision 1: Subagent 调用方式

**选择：使用 Agent tool (general-purpose) + prompt 模板文件**

理由：
- Claude Code 的 Agent tool 支持一般性 subagent 调用
- prompt 模板文件定义 subagent 的行为，可复用、可版本控制
- 不需要定义 standalone agent（agents/*.md），因为 subagent 是流程中的一部分

**备选方案：**
- 定义 standalone agent（agents/*.md）：更正式，但会增加文件数量，subagent 不需要独立存在
- 直接在 SKILL.md 中写 subagent prompt：不便于复用和版本控制

### Decision 2: Subagent 输出格式

**选择：标准化 JSON 输出格式**

每个 subagent 输出必须包含：
```json
{
  "status": "DONE" | "BLOCKED" | "NEEDS_CONTEXT",
  "output": { ... },  // 具体任务输出
  "cross_validation": {  // 三源验证记录
    "sources": ["style_definition", "actual_paragraphs", "text_instructions"],
    "conflicts": [],
    "resolution": "..."
  },
  "tool_errors": [],  // 工具错误列表，必须报告
  "common_sense_check": "pass" | "needs_revision" | "error"
}
```

理由：
- 主 agent 可以检查 cross_validation 字段判断是否做了三源验证
- 主 agent 可以检查 tool_errors 字段判断是否有工具报错
- 主 agent 可以检查 common_sense_check 字段判断常识检查结果

### Decision 3: 主 agent 评估逻辑

**选择：主 agent 在 SKILL.md 中定义评估协议**

评估逻辑：
1. 检查 status 字段：BLOCKED → 需要人工干预
2. 检查 cross_validation 字段：缺失 → 拒绝输出，要求重做
3. 检查 tool_errors 字段：非空 → 报告流程异常
4. 检查 common_sense_check 字段：needs_revision → 拒绝输出，要求重做

拒绝条件：
- subagent 输出 status=DONE 但 cross_validation 缺失 → 流程错误
- subagent 输出 status=DONE 但 tool_errors 非空 → 流程错误
- subagent 输出 common_sense_check=needs_revision → 拒绝，要求修正

理由：
- 评估逻辑写在 SKILL.md 中，主 agent 强制执行
- 不依赖代码实现，纯 prompt 约束

### Decision 4: 文件组织

**选择：prompt 模板文件放在 skill 目录下**

```
.claude/skills/
├── extract-spec/
│   ├── SKILL.md                    # 主 skill，定义调度协议
│   ├── font-extractor-prompt.md    # 字体提取 subagent
│   ├── layout-extractor-prompt.md  # 页面设置 subagent
│   └── heading-extractor-prompt.md # 标题提取 subagent
├── evaluate-spec/
│   ├── SKILL.md                    # 主 skill
│   ├── evaluator-prompt.md         # 评估 subagent
├── check-thesis/
│   ├── SKILL.md                    # 主 skill
│   ├── rule-checker-prompt.md      # 确定性规则检查 subagent
│   ├── semantic-checker-prompt.md  # 语义规则检查 subagent
```

理由：
- prompt 模板和 SKILL.md 在同一目录，便于管理
- 符合 SP 的 Embedded 层架构

## Risks / Trade-offs

**Risk: Subagent 调用开销**
→ 每个任务启动独立 subagent，会增加调用次数。Mitigation：合理划分任务粒度，避免过度拆分。

**Risk: 主 agent 评估不完善**
→ 如果评估逻辑遗漏检查项，错误仍可能发生。Mitigation：评估逻辑必须包含 Iron Law 强制检查项。

**Risk: Subagent 返回 BLOCKED**
→ 需要人工干预，可能阻塞流程。Mitigation：在 SKILL.md 中定义 BLOCKED 处理流程，主 agent 报告并等待用户指导。

**Trade-off: 流程复杂度增加**
→ 两层架构比单层架构更复杂。但好处是错误捕捉更可靠。