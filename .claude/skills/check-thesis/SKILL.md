---
name: check-thesis
description: 基于格式规则检查文档，混合使用 Python 工具处理确定性规则，使用 Agent 处理语义性规则。
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
python3 .claude/skills/batch-check/scripts/run.py --schema

# 执行比对
python3 .claude/skills/batch-check/scripts/run.py <facts.json> <checks.json>
```

Agent 直接构造 check 指令，不需要中间的 spec 翻译步骤。例如：

```json
[
  {"type": "font", "scope": "east_asia", "selector": "style:Normal", "style_aliases": ["Normal", "正文"], "expected": "宋体"},
  {"type": "font_size", "selector": "style:Normal", "style_aliases": ["Normal", "正文"], "expected": 12},
  {"type": "margin", "side": "left", "expected": 3.0}
]
```

### 4. 语义检查

由 Agent 直接判断：

- 摘要格式
- 参考文献格式
- 目录结构
- 其他依赖上下文的规则

结论标注为 `Agent 判断`，并给出匹配依据。

### 5. 深入调查

对 batch-check 报告的异常，Agent 可按需：

- 调用 `query-word-text` 查看具体段落
- 调用 `render-word-page` 做视觉复核

### 6. 输出报告

Markdown 报告，每条结果包含：

- 规则描述
- 检查结果：通过 / 不通过 / 待人工确认
- 期望值 vs 实际值
- 定位信息
- 来源标注：`Python 检查` 或 `Agent 判断`

同一规则下的多处失败应聚合展示，不要逐段堆叠。

### 7. 完整性回溯

检查结束后回到原始规则逐条核对，确保无遗漏。
