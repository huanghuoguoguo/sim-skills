---
name: extract-spec
description: "Use this skill to extract formatting rules from reference materials and produce a spec.md for user review. Triggers: when user provides a template (.docx/.dotm), a sample thesis, or a formatting guide document, and wants rules extracted. Output: a human-readable spec.md covering page setup, body text, headings, captions, abstract, references, TOC, headers/footers. Do NOT use for checking a document — use check-thesis instead. Do NOT use if rules are already written in a spec.md."
---

# extract-spec

从分散的参考材料收敛成一份自然语言规则文档 `spec.md`。

`spec.md` 是核心产物：给用户直接审核和修改，给下游检查流程直接消费。

## 输入类型

- 学校模板：`.docx` / `.dotm`
- 成品论文：格式示例
- 说明文档：写明格式规则的文本

先判断每个文件的角色，再决定取证方式。

## 可用工具

| 工具 | 用途 |
|------|------|
| `parse-word` | 读取段落、样式、页面设置等结构事实 |
| `query-word-style` | 核对正文、标题等样式的最终解析值 |
| `query-word-text` | 检索文档中的格式说明文字 |
| `paragraph-stats` | 采样段落，统计属性分布 |
| `render-word-page` | 视觉复核（仅在冲突时使用） |

## 工作方式

### 1. 分类来源

- 模板或成品论文：样式和页面设置为主要证据
- 说明文档：显式文字规则为主要证据
- 多来源冲突时说明冲突，不静默覆盖

### 2. 提取规则

至少覆盖：页面设置、正文、标题、图题/表题、摘要、参考文献、目录、页眉页脚。

#### 核心原则：样式定义不等于实际格式

中文论文模板中，样式定义和实际段落属性经常不一致（direct formatting 覆盖样式定义是常见做法）。**所有基于样式提取的规则都必须用实际段落交叉验证**，不能仅凭 `query-word-style` 的输出就写结论。

#### 通用验证流程（适用于所有样式：正文、标题、图题等）

对每种样式，必须同时获取两个证据：

1. **样式定义**：`query-word-style --style "Heading 3"` 等
2. **实际段落属性**：`paragraph-stats --style-hint "heading 3"` 采样该样式的真实段落

如果两者矛盾（如样式定义为宋体，实际段落为黑体），必须：
- 优先采用实际段落值（这才是用户看到的效果）
- 在来源标注说明冲突：`模板实际段落（样式定义与实际使用不一致）`
- 或标记为"待确认项"

#### 正文规则的额外约束

- 禁止仅依据 `Normal` 默认样式就写出结论
- 必须先调用 `paragraph-stats` 采样实际正文段落：

```bash
python3 .claude/skills/paragraph-stats/scripts/run.py <facts.json> \
  --style-hint normal --style-hint "body text" \
  --min-length 20 --require-body-shape \
  --exclude-text 摘要 --exclude-text 致谢 \
  --heading-prefix "^第.+章"
```

- 检查 `style_distribution` 输出，将所有包含正文段落的样式名写入 spec.md 的"适用样式"字段（如 `Normal`、`Body Text`、`Body Text Indent` 等）。下游检查需要用这些名称做 `style_aliases`，遗漏任何一个都会导致漏检。
- 如果默认样式和实际正文段落冲突，必须继续查文字说明或标记为"待确认项"

#### 标题规则的额外约束

每级标题都必须用 `paragraph-stats` 采样验证：

```bash
# 示例：验证 Heading 3 的实际属性
python3 .claude/skills/paragraph-stats/scripts/run.py <facts.json> \
  --style-hint "heading 3"
```

#### 推荐证据优先级

1. 实际段落的属性分布（`paragraph-stats` 输出）
2. 说明文档中的显式文字规则
3. 明确命名的样式定义（如 `Body Text`、`Heading 1`）
4. `Normal` 等默认样式
5. 视觉复核

### 3. 写出 `spec.md`

每条规则必须具体可执行。单位统一：边距用 `cm`，段距用 `pt`，字号写成 `小四（12pt）`。保留来源信息。无法确认的项放进"待确认项"。

### 4. 自评

完成后建议调用 `evaluate-spec` 做覆盖性和可执行性自评。
