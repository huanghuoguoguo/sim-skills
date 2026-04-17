# Quality Rules for Spec Extraction

确定性质量规则，用于自动检测并标注问题。主 Agent 和 Unified Extractor 都可执行这些检查。

## 规则类型

| 类型 | 自动裁决 | 处理方式 |
|------|----------|----------|
| 确定性规则 | ✓ 可以 | 标注 + 继续 |
| 灰区问题 | ✗ 不可以 | 标注"⚠️ 待确认" |

---

## Rule 1: 西文字体常识检查

**检查条件**:
```
font_rule.ascii_font ∈ {宋体, 黑体, 楷体, 仿宋}
```

**判定**: 确定性问题（中文字体不应作为西文字体）

**处理**:
- 标注: `"⚠️ 待确认（模板使用 {font_value}）"`
- common_sense_check: `"needs_revision"`
- **禁止**: 自动推断正确值（如 Times New Roman）

**示例**:
```json
{
  "font_rule": {
    "ascii_font": "⚠️ 待确认（模板使用 宋体）"
  },
  "common_sense_check": "needs_revision",
  "common_sense_issues": ["ASCII font '宋体' is Chinese font"]
}
```

---

## Rule 2: 字号范围检查

**检查条件**:
```
font_rule.font_size ∉ [10pt, 16pt]
```

**判定**: 灰区问题（可能是特殊样式，如标题）

**处理**:
- 标注异常值
- 不阻止输出

**示例**:
```json
{
  "font_rule": {
    "font_size": 18,
    "font_size_note": "超出正文范围 [10-16pt]，可能为标题样式"
  }
}
```

---

## Rule 3: 样式一致性检查

**检查条件**:
```
style_definition.font ≠ actual_paragraphs.top_font
```

**判定**: 灰区问题（可能是直接格式化覆盖）

**处理**:
- 记录冲突
- 使用实际段落值（用户看到的是实际值）
- 标注来源差异

**示例**:
```json
{
  "cross_validation": {
    "conflicts": [
      {
        "type": "style_vs_actual",
        "style_font": "宋体",
        "actual_font": "黑体",
        "resolution": "USE actual_paragraphs (直接格式化覆盖)"
      }
    ]
  }
}
```

---

## Rule 4: 必需字段完整性检查

**检查条件**:
```
required_fields ⊄ extraction_result
```

**required_fields** (per section):
- layout: `paper_size`, `margins` (4 sides)
- font: `east_asia_font`, `ascii_font`, `font_size`
- heading: `font`, `font_size` (per level)
- abstract: `title_format`, `body_format`
- keyword: `label_format`, `content_format`
- caption: `style`, `numbering_style`
- reference: `font`, `font_size`, `citation_style`
- header_footer: `header_format`, `footer_format`, `page_numbering`
- toc: `toc_format`, `heading_levels_included`

**判定**: 确定性错误（数据缺失）

**处理**:
- 标注缺失字段
- 返回 `status: "NEEDS_CONTEXT"`（如无法补全）

---

## Rule 5: 数据来源标注检查

**检查条件**:
```
section.source 未标注
```

**判定**: 确定性错误（不符合规范）

**处理**:
- 要求标注来源

**valid_sources**:
- `"facts_layout"` - 直接从 facts.json layout 字段
- `"style_definition"` - query-style 返回
- `"actual_paragraphs"` - stats 分布统计
- `"text_instructions"` - query-text 文字说明
- `"document_instructions"` - 文档内的格式说明文字

---

## 灰区问题处理原则

灰区问题 = 无法自动裁决，需用户确认

| 灰区问题 | 处理 |
|----------|------|
| 西文字体为中文字体 | 标注"⚠️ 待确认"，不推断 |
| 样式与实际不一致 | 使用实际值，标注冲突 |
| 多种字号混用 | 标注分布情况，不选单一值 |
| 缺少文字说明 | 标注"无文字说明验证" |

---

## 执行时机

**Unified Extractor 内部**:
- 在输出前执行 Rule 1, 2, 3
- 发现问题立即标注

**主 Agent 验证层**:
- 执行 Rule 4, 5（完整性检查）
- 可抽样验证 Rule 1, 2, 3
- 发现确定性错误→重试 Extractor
- 发现灰区问题→标注待确认