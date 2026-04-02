# MVP 设计

## 1. MVP 目标

验证 Agent + 工具脚本的模式能跑通两条完整路径：

1. **上游**：从参考文件提取规则 → `spec.md`
2. **下游**：用 `spec.md` 检查论文 → 检查报告

## 2. MVP 范围

### 支持

- 输入文档：`.docx`、`.dotm`
- 场景：高校论文 / 毕业设计
- 执行模式：Agent 读 Skill 后自主规划，调用工具脚本

### 不支持

- PDF 作为主检查对象
- 自动修复文档
- 复杂公式、文本框、图形对象

## 3. 规则覆盖

MVP 至少覆盖以下格式要素：

| 要素 | 检查方式 |
|------|---------|
| 页边距（上下左右） | Python |
| 正文字体（中文/西文） | Python |
| 正文字号 | Python |
| 行距 | Python |
| 首行缩进 | Python |
| 段前/段后距 | Python |
| 各级标题样式 | Python |
| 图题/表题格式 | Python |
| 摘要格式 | Agent |
| 参考文献格式 | Agent |
| 目录结构 | Agent |

## 4. 最小组件集

### 工具脚本（5 个，上下游共享）

| 脚本 | 职责 |
|------|------|
| `parse_word.py` | docx → 结构化事实（段落、样式、布局、页眉页脚） |
| `query_text.py` | 按关键词检索段落 |
| `query_style.py` | 样式属性查询，含完整继承链解析 |
| `render_page.py` | 页面渲染为图片 |
| `batch_check.py` | 批量格式检查（接受检查指令，输出 pass/fail） |

### Skill（3 个）

| Skill | 职责 |
|-------|------|
| `extract-spec` | 指导 Agent 从参考文件提取规则，输出 spec.md |
| `evaluate-spec` | 指导 Agent 评估 spec.md 质量，给出补充建议 |
| `check-thesis` | 指导 Agent 检查论文，混合使用 Python + 语义推理 |

## 5. 数据流

### 上游：提取规则

```
用户提供参考文件（模板 / 成品 / 说明文档）
  → Agent 读 extract-spec Skill
  → 调用 parse_word / query_text / query_style / render_page
  → Agent 综合推理，输出 spec.md
  → Agent 读 evaluate-spec Skill，自评质量
  → 用户精校 spec.md
```

### 下游：检查文档

```
用户提供论文 + 定稿 spec.md
  → Agent 读 check-thesis Skill
  → 调用 parse_word 解析论文
  → 确定性规则 → 调用 batch_check 批量扫描
  → 语义性规则 → Agent 用 query_text + 推理判断
  → 对照 spec.md 逐条回溯，确认无遗漏
  → 输出检查报告（Markdown）
```

## 6. batch_check 检查指令

Agent 从 spec.md 翻译规则为结构化指令：

```json
{
  "checks": [
    {"type": "font", "scope": "east_asia", "selector": "style:Normal", "expected": "宋体"},
    {"type": "font_size", "selector": "style:Normal", "expected": "12pt"},
    {"type": "line_spacing", "selector": "style:Normal", "expected": {"mode": "multiple", "value": 1.5}},
    {"type": "margin", "side": "left", "expected": "3cm"}
  ]
}
```

输出每条 check 的 pass/fail + expected/actual + 位置信息。

## 7. 验收标准

1. 给定模板 + 说明文档，Agent 能输出覆盖上述要素的 spec.md
2. 用户精校后，Agent 能检查论文并输出合理的报告
3. 报告中每条结果有：规则、pass/fail、期望值/实际值、定位
4. 确定性规则由 Python 检查，语义规则由 Agent 判断，均标注来源
5. Agent 能对照 spec.md 回溯确认无遗漏
