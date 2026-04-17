---
name: extract-spec
description: "Use this skill to extract formatting rules from reference materials and produce a spec.md for user review. Triggers: when user provides a template (.docx/.dotm), a sample thesis, or a formatting guide document, and wants rules extracted. Output: a human-readable spec.md covering page setup, body text, headings, captions, abstract, references, TOC, headers/footers. Do NOT use for checking a document — use check-thesis instead. Do NOT use if rules are already written in a spec.md."
---

# extract-spec

从分散的参考材料收敛成一份自然语言规则文档 `spec.md`。

## 角色：调度者 + 验证者

**主 Agent 角色**：
1. 调度 Unified Extractor Agent 执行提取
2. 验证提取结果质量（可调用工具抽样检查）
3. 分类处理问题（确定性错误/灰区问题/缺失上下文）
4. 自迭代闭环（发现问题→重试→验证）
5. 合并输出到最终 spec.md

---

## 输入

- 模板文件：`.docx` / `.dotm` 或成品论文
- 说明文档：写明格式规则的文本（可选）

---

## 执行流程

### Step 1: 解析文档（主 Agent 执行）

```bash
python3 -m sim_docs parse <file.docx> --output facts.json
```

### Step 2: 调度 Unified Extractor Agent

**主 Agent 调度单个 Agent 处理所有 section：**

```
Agent tool:
  description: "提取所有格式规则"
  prompt: |
    [使用 unified-extractor-prompt.md 模板]
    
    输入文件：{file_path}
    facts 文件：{facts_path}
    
    # Unified Extractor 内部流程：
    # 1. 加载 profile 获取 required sections
    # 2. 对每个 section 执行提取 + 三源验证 + 常识检查
    # 3. 输出 extraction_result.json
```

**Unified Extractor 输出**：`extraction_result.json`

包含所有 section 的提取数据，每个 section 都有：
- `cross_validation.sources` 标注数据来源
- `common_sense_check` 标注常识检查结果
- `source` 标注主要数据来源

### Step 3: 验证提取结果（主 Agent 责任）

主 Agent 读取 `extraction_result.json`，执行验证：

#### 3.1 形式检查

| 检查项 | 通过条件 | 处理 |
|--------|----------|------|
| status | `DONE` | 否 → NEEDS_CONTEXT 询问用户 |
| cross_validation 存在 | ✓ | 否 → 重新 dispatch |
| required sections 完整 | ✓ | 否 → 重新 dispatch |
| tool_errors 为空 | ✓ | 否 → 报告异常 |

#### 3.2 内容验证（主 Agent 可调用工具）

**验证边界（修订后 IRON LAW）：**

主 Agent **允许**的验证行为：
- ✓ 读取 `extraction_result.json`
- ✓ 调用 `stats` 抽样验证实际段落分布
- ✓ 调用 `query-style` 验证样式定义
- ✓ 调用 `query-text` 搜索文字说明
- ✓ 执行质量规则检查（确定性规则）
- ✓ 标注问题

主 Agent **禁止**的执行行为：
- ✗ 解析原始文档
- ✗ 从零提取规则内容
- ✗ 自己推断缺失值

**区分标准**：
- 执行 = 从原始数据产生新内容 → 禁止
- 验证 = 检查已有内容是否正确 → 允许

#### 3.3 抽样验证示例

```
# 主 Agent 验证 font_rule
extraction_result.font_rules.ascii_font = "宋体"

# 调用工具验证（验证行为，允许）
stats_result = run("python3 -m sim_docs stats facts.json --style-hint Normal")
# 检查实际段落 ASCII 字体分布是否匹配

# 执行质量规则检查
if extraction_result.font_rules.ascii_font in CHINESE_FONTS:
    # 确定性问题 → 标注（不需要推断正确值）
   标注 = "⚠️ 待确认（模板使用 宋体）"
```

### Step 4: 问题分类处理

根据验证结果分类问题：

```
问题分类
─────────────────────────────────────────────────────

┌─────────────────────────────────────────┐
│           主 Agent 验证                  │
└─────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │     问题分类           │
        └───────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼

┌─────────┐   ┌─────────┐   ┌─────────┐
│确定性错误│   │灰区问题 │   │缺失上下文│
│         │   │         │   │         │
│可自动检测│   │无法裁决 │   │无数据源 │
│并重试   │   │需用户确认│   │需用户提供│
└────┬────┘   └────┬────┘   └────┬────┘
     │             │             │
     ▼             ▼             ▼

┌─────────┐   ┌─────────┐   ┌─────────┐
│重试     │   │标注     │   │询问用户 │
│Extractor│   │⚠️待确认 │   │获取上下文│
│(最多2次)│   │合并输出 │   │重新dispatch│
└─────────┘   └─────────┘   └─────────┘
```

#### 4.1 确定性错误 → 重试

| 确定性错误 | 处理 |
|------------|------|
| cross_validation 缺失 | 重新 dispatch，强制验证 |
| required section 缺失 | 重新 dispatch，强调完整性 |
| tool_errors 非空 | 报告异常，等待用户确认后继续 |

**重试最多 2 次**，超过则标注"待用户确认项"

#### 4.2 灰区问题 → 标注待确认

| 灰区问题 | 处理 |
|----------|------|
| 西文字体为中文字体（宋体等） | 标注"⚠️ 待确认（模板使用宋体）" |
| 样式定义与实际不一致 | 标注冲突，使用实际值 |
| 多种字号混用 | 标注分布情况 |

**关键**：不自动推断正确值，只标注现状

#### 4.3 缺失上下文 → 询问用户

| 缺失情况 | 处理 |
|----------|------|
| 无文字说明验证 | 询问用户是否有格式要求文档 |
| 模板缺少某些 section | 询问用户是否需要这些规则 |

### Step 5: 自迭代闭环

```
自迭代流程
─────────────────────────────────────────────────────

Extractor Agent
      │
      ▼ extraction_result.json
      │
┌─────────────────────────────────────┐
│          主 Agent 验证               │
│                                     │
│  Step 3: 形式检查 + 内容验证         │
│  Step 4: 问题分类                   │
└─────────────────────────────────────┘
      │
      ├──── Pass ────→ Step 6: 合并输出
      │
      ├──── 确定性错误 ────→ 重试 Extractor
      │                         │
      │                         ▼ extraction_result_v2.json
      │                         │
      │                    ┌───────────┐
      │                    │ 再次验证  │
      │                    │ (最多2次) │
      │                    └───────────┘
      │
      ├──── 灰区问题 ────→ 标注待确认 → Step 6
      │
      └──── 缺失上下文 ─→ 询问用户 → 重试 Extractor

迭代次数上限: 2
超过上限: 标注"待用户确认项" → 继续合并
```

### Step 6: 合并输出（通过验证后）

将 `extraction_result.json` 按 profile spec_schema section 顺序转换为 spec.md：

```markdown
# [论文格式规范]

## 来源
- 模板文件：{file_path}
- 解析时间：{timestamp}

## 页面设置
[从 extraction_result.layout_rules]

## 正文
[从 extraction_result.font_rules]

## 标题
[从 extraction_result.heading_rules，按 level 排列]

## 摘要
[从 extraction_result.abstract_rules]

## 关键词
[从 extraction_result.keyword_rules]

## 图表Caption
[从 extraction_result.caption_rules]

## 参考文献
[从 extraction_result.reference_rules]

## 页眉页脚
[从 extraction_result.header_footer_rules]

## 目录
[从 extraction_result.toc_rules]

## 待确认项
[汇总所有标注 ️ 的项]

## Optional Sections (模板未包含)
[从 extraction_result.optional_sections]
```

**合并原则**：
- 只拼接 extraction_result，不填补缺失内容
- 保留所有 ️ 标注，用户自行修正
- 不让主 Agent 推断或猜测

---

## 质量规则

参见 `quality-rules.md`。

**确定性规则**（主 Agent 和 Extractor 都可执行）：

| 规则 | 检查 | 处理 |
|------|------|------|
| Rule 1 | ascii_font ∈ {宋体,黑体,楷体,仿宋} | 标注"⚠️ 待确认" |
| Rule 2 | font_size ∉ [10pt,16pt] | 标注异常 |
| Rule 3 | style ≠ actual | 标注冲突 |
| Rule 4 | required field 缺失 | NEEDS_CONTEXT |
| Rule 5 | source 未标注 | 视为流程错误 |

---

## IRON LAW: 验证边界

**修订版**：区分"执行"与"验证"

```
主 Agent 允许的验证行为：
─────────────────────────
✓ 读取 extraction_result.json
✓ 调用 stats/query-style/query-text 抽样检查
✓ 执行确定性质量规则
✓ 标注问题（不推断正确值）
✓ 要求 Extractor 重试

主 Agent 禁止的执行行为：
─────────────────────────
✗ 解析原始文档（parse-word）
✗ 从零提取规则内容
✗ 自己推断缺失值（如西文字体应为 Times New Roman）
✗ 写 spec.md 正文内容（只做标注和合并）

区分标准：
─────────────────────────
执行 = 从原始数据产生新内容
验证 = 检查已有内容是否正确

验证是允许的，执行是禁止的
```

---

## Token 消耗对比

| 架构 | Token | 验证者 |
|------|-------|--------|
| 旧（9 并行 subagent） | ~180k | 无 |
| 新（1 Extractor + 主Agent验证） | ~40k | 主 Agent |

---

## Prompt 模板位置

- `unified-extractor-prompt.md` - Unified Extractor Agent prompt
- `quality-rules.md` - 确定性质量规则定义