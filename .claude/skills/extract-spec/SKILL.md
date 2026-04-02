---
name: extract-spec
description: 从模板、成品论文和说明文档中提取论文格式规则，输出用户可精校的 spec.md。
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

正文规则必须额外约束：

- 禁止仅依据 `Normal` 默认样式就写出结论
- 必须先调用 `paragraph-stats` 采样实际正文段落：

```bash
python3 .claude/skills/paragraph-stats/scripts/run.py <facts.json> \
  --style-hint normal --style-hint "body text" \
  --min-length 20 --require-body-shape \
  --exclude-text 摘要 --exclude-text 致谢 \
  --heading-prefix "^第.+章"
```

- 如果默认样式和实际正文段落冲突，必须继续查文字说明或标记为"待确认项"

推荐证据优先级：

1. 实际正文段落的属性分布
2. 明确命名的正文样式（如 `Body Text`）
3. 说明文档中的显式文字规则
4. `Normal` 等默认样式
5. 视觉复核

### 3. 写出 `spec.md`

每条规则必须具体可执行。单位统一：边距用 `cm`，段距用 `pt`，字号写成 `小四（12pt）`。保留来源信息。无法确认的项放进"待确认项"。

### 4. 自评

完成后建议调用 `evaluate-spec` 做覆盖性和可执行性自评。
