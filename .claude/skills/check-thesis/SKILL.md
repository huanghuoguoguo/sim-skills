---
name: check-thesis
description: "Use this skill to check a .docx document against formatting rules and produce a Markdown report. Triggers: when user provides a Word document and formatting rules (from spec.md, PDF, plain text, or verbal description) and wants a compliance check. Uses batch-check for deterministic rules (font, size, spacing, margins) and Agent reasoning for semantic rules (abstract, references, TOC). Do NOT use for extracting rules — use extract-spec instead. Do NOT use for .doc or .pdf as the main check target."
---

# check-thesis

检查文档是否符合给定的格式规则，输出 Markdown 检查报告。

## 输入

- 待检查文档：`.docx`
- 格式规则：任意来源（spec.md、PDF、纯文本、用户口述）

## 可用工具

| 工具 | 用途 |
|------|------|
| `parse-word` | 解析文档结构事实 |
| `batch-check` | 批量确定性属性比对（`--schema` 查看支持的 check 类型） |
| `paragraph-stats` | 按条件筛段落并统计属性分布 |
| `query-word-text` | 按关键词检索段落 |
| `query-word-style` | 查询样式属性 |
| `render-word-page` | 渲染指定页为图片 |
| `visual-check` | 视觉辅助检查工作流（需要 vision 能力） |

## 工作方式

Agent 自主规划，典型流程：

### 1. 理解规则

- 阅读用户提供的规则（任何格式）
- 拆分为确定性规则和语义性规则

### 2. 获取事实

- 调用 `parse-word` 解析文档，输出 facts.json
- 必要时调用 `query-word-text` 定位摘要、目录、参考文献等区域

### 3. 确定性检查

Agent 根据规则构造 check 指令 JSON，调用 `batch-check` 执行：

```bash
# 先查看支持哪些 check 类型
python3 -m sim_docs check --schema

# 执行比对
python3 -m sim_docs check <facts.json> <checks.json>
```

Agent 直接构造 check 指令，不需要中间的 spec 翻译步骤。例如：

```json
[
  {"type": "font", "scope": "east_asia", "selector": "style:Normal", "style_aliases": ["Normal", "正文", "Body Text"], "expected": "宋体"},
  {"type": "font_size", "selector": "style:Normal", "style_aliases": ["Normal", "正文", "Body Text"], "expected": 12},
  {"type": "margin", "side": "left", "expected": 3.0}
]
```

**`style_aliases` 必须完整**：一条规则适用于多个样式名时（如正文同时有 `Normal` 和 `Body Text`），必须将所有样式名列入 `style_aliases`。遗漏任何一个会导致该样式下的段落漏检。如果 spec.md 中列出了"适用样式"，直接使用；否则先调用 `paragraph-stats` 确认文档中实际存在哪些相关样式。

### 4. 语义检查

由 Agent 直接判断：

- 摘要格式
- 参考文献格式
- 目录结构
- 其他依赖上下文的规则

结论标注为 `Agent 判断`，并给出匹配依据。

### 5. 视觉检查

对于结构化工具无法覆盖的规则（页码位置、页眉内容、封面版式、目录格式等），参考 `visual-check` skill 的工作流程：

1. 筛出需要视觉验证的规则
2. 渲染关键页面（封面、目录页、正文首页等，通常 3-5 页）
3. Agent 用 vision 逐条分析，输出判断 + 依据 + 置信度

**前提**：Agent 所用模型必须具备 vision 能力。如果不具备，跳过此步骤并将相关规则标记为"待人工确认"。

### 6. 深入调查

对 batch-check 报告的异常，Agent 可按需：

- 调用 `query-word-text` 查看具体段落
- 调用 `render-word-page` 做视觉复核

**`unresolved` 结果的处理**：`unresolved`（matched_count 为 0）通常意味着 selector 或 style_aliases 有误，而非文档真的没有该类段落。遇到 unresolved 时必须：

1. 先调用 `paragraph-stats` 确认文档中实际有哪些样式名
2. 检查 style_aliases 是否遗漏了文档中使用的样式名
3. 修正 aliases 后重新执行 batch-check
4. 只有在确认文档确实不包含该类段落时，才将 unresolved 报告为"不适用"

### 7. 输出报告

Markdown 报告，每条结果包含：

- 规则描述
- 检查结果：通过 / 不通过 / 待人工确认
- 期望值 vs 实际值
- 定位信息
- 来源标注：`Python 检查` 或 `Agent 判断` 或 `视觉检查`

同一规则下的多处失败应聚合展示，不要逐段堆叠。

### 8. 完整性回溯

检查结束后回到原始规则逐条核对，确保无遗漏。

## 进阶参考

完整工作流示例、确定性 vs 语义规则分类表、unresolved 处理流程、报告模板见 [REFERENCE.md](REFERENCE.md)。
