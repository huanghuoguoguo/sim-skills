## Context

### 当前状态

Skills 现状：
- `extract-spec`: 有详细的步骤说明，但缺乏约束机制（铁律、红旗）
- `evaluate-spec`: 有评估维度，但缺乏程序化常识检测
- `check-thesis`: 有工作流，但缺乏完整性强制回溯

今天暴露的问题：
- Agent 提取天津理工大学模板时，把"宋体"当作西文字体写入 spec
- 工具调用报错被静默忽略
- evaluate-spec 没被调用

### SP 方法论核心

| 技术 | 形式 | 作用 |
|------|------|------|
| 铁律 | `NO X WITHOUT Y` | 强制前置条件 |
| 红旗 | 列表 + STOP | 自检触发器 |
| 借口表格 | Excuse → Reality | 堵借口 |
| Gate Function | 伪代码流程 | 强制步骤 |
| Skill 链 | REQUIRED SUB-SKILL | 流程完整性 |
| Review Loop | Subagent review | 质量闸门 |

## Goals / Non-Goals

**Goals:**
- extract-spec 添加铁律、红旗、借口表格，确保交叉验证不被跳过
- evaluate-spec 添加常识检测，程序化验证"中文字体≠西文字体"
- 建立 skill 链：extract-spec → evaluate-spec（强制）
- 工具错误必须报告，不能静默忽略

**Non-Goals:**
- 不改造 capability skills（parse-word 等）
- 不改变现有 Python 代码逻辑（只添加常识检测）
- 不创建新 skills

## Decisions

### Decision 1: 铁律形式

**Choice:** 在 SKILL.md 中用代码块包裹铁律

```markdown
## The Iron Law

NO RULE WRITTEN WITHOUT CROSS-VALIDATION

**No exceptions:**
- Not for "template shows X"
- Not for "style definition says X"
- Not for "quick check is enough"
```

**Alternatives considered:**
- 用 checklist 代替 → 弱，Agent 会跳过
- 不用铁律 → 无法强制前置条件

**Rationale:** 代码块形式的铁律在 SP 实践中证明有效，Agent 会先检查条件。

### Decision 2: 常识检测实现方式

**Choice:** 在 `spec_engine.py` 添加 `check_common_sense()` 函数

检测逻辑：
1. 扫描 spec.md 中所有字体声明
2. 检测 east_asia 字体名是否出现在 ascii 字体位置
3. 返回冲突列表

**Alternatives considered:**
- 纯 Agent 检测 → 不稳定，可能漏
- 写入 SKILL.md 作为 Agent 指导 → 不强制

**Rationale:** 程序化检测强制执行，Agent 无法跳过。

### Decision 3: Skill 链调用方式

**Choice:** 在 SKILL.md 中用 `**REQUIRED:**` 语法

```markdown
## The Skill Chain

**REQUIRED:** After extraction, call evaluate-spec
**REQUIRED:** In evaluate-spec, run spec-check --mode common-sense
```

**Alternatives considered:**
- 用流程图 → 不够强制
- 不用链 → Agent 会跳过评估

**Rationale:** REQUIRED 标记是 SP 的标准做法，明确告知 Agent 必须调用。

## Risks / Trade-offs

**Risk: 常识检测规则不完整**
→ Mitigation: 先实现"中文字体≠西文字体"，后续迭代添加更多规则

**Risk: 铁律过长影响 token 效率**
→ Mitigation: 铁律部分控制在 50 词以内，借口表格用紧凑格式

**Trade-off: 强制调用可能打断 Agent 灵活性**
→ Acceptable: 文档检查流程需要强制步骤，不能灵活跳过

## Skill 改造模板

### extract-spec 改造模板

```markdown
## The Iron Law

NO RULE WRITTEN WITHOUT CROSS-VALIDATION

Cross-validation means:
1. Style definition (query-style)
2. Actual paragraph properties (paragraph-stats)
3. Text instructions (query-text)

**No exceptions:**
- Not for "template clearly shows X"
- Not for "style definition is unambiguous"
- Not for "I already checked one source"

## Red Flags - STOP

If you catch yourself thinking:
- "The template paragraph shows 宋体/宋体, that's the answer"
- "Style definition says 宋体, done"
- "query-text failed, skip text instructions"
- "paragraph-stats takes too long"

**ALL of these mean: STOP. Cross-validate all three sources.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Template shows 宋体/宋体" | 中文论文西文通常是 Times New Roman，检查文字说明 |
| "Style definition is 宋体" | 样式定义常不准确，必须用 paragraph-stats 验证 |
| "query-text found nothing" | 搜索"字体"、"Times"、"西文"关键词 |
| "paragraph-stats failed" | 工具失败必须报告，不能静默忽略 |

## The Gate Function

BEFORE writing any font rule:
1. QUERY: query-style for style definition
2. STATS: paragraph-stats for actual distribution
3. TEXT: query-text for "字体"/"Times" keywords
4. COMPARE: Do all three agree?
   - IF conflict → Note in spec.md as "来源不一致，待确认"
   - IF agree → Write rule with confidence level
5. ONLY THEN: Write the rule

## Font Common Sense

中文字体不应作为西文字体：
- 宋体、黑体、楷体、仿宋 = 中文专用
- 西文字体通常是：Times New Roman、Arial

**如果看到 east_asia=宋体, ascii=宋体：**
1. 先检查文字说明（搜索"Times"、"西文"）
2. 文字说明优先级 > 样式定义 > 实际段落
3. 如果文字说明说 Times New Roman → 标注"样式与说明冲突"
```

### evaluate-spec 改造模板

```markdown
## The Iron Law

NO SPEC DELIVERY WITHOUT COMMON-SENSE CHECK

**REQUIRED:** Run `python3 -m sim_docs spec-check --mode common-sense spec.md`

## Common Sense Checks

程序化检测（自动运行）：
1. 中文字体≠西文字体
2. 行距模式必须明确（不能只写"20pt"）

Agent 检测（手动检查）：
1. 正文规则是否有 paragraph-stats 证据支撑
2. 标题规则是否经过实际段落验证
```

## Open Questions

- 是否需要添加更多常识检测规则？（公式格式、图表编号等）
- Gate Function 的伪代码风格是否需要统一？