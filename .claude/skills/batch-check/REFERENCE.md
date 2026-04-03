# batch-check Reference

Advanced usage, complete check instruction examples, and troubleshooting for the batch-check engine.

## Complete Check Types

| type | target | expected format | tolerance |
|------|--------|-----------------|-----------|
| `font` | font family | string, scope: `east_asia` / `ascii` | exact match |
| `font_size` | font size in pt | number | 0.2 pt |
| `alignment` | paragraph alignment | `left` / `center` / `right` / `justify` / `distribute` | exact match |
| `line_spacing` | line spacing | `{"mode": "multiple\|exact\|at_least", "value": N}` | 0.1 |
| `spacing_before` | space before in pt | number | 0.5 pt |
| `spacing_after` | space after in pt | number | 0.5 pt |
| `first_line_indent` | first line indent in pt | number | 0.5 pt |
| `margin` | page margin in cm | number, requires `side` | 0.05 cm |
| `page_size` | paper size | `"A4"` | exact match |

## Selectors

| selector | behavior |
|----------|----------|
| `style:<name>` | Match paragraphs whose style_name matches `<name>` or any of `style_aliases` (case-insensitive, whitespace-normalized) |
| `caption:figure` | Match figure captions by `style_aliases` or `caption_prefix_patterns` regex |
| `caption:table` | Match table captions by `style_aliases` or `caption_prefix_patterns` regex |
| `document:layout` | Document-level layout; auto-assigned for `margin` and `page_size` checks |

## Full Check Instruction Examples

### Body text (Normal) — complete check set

```json
[
  {
    "id": "body-font-east",
    "type": "font",
    "scope": "east_asia",
    "selector": "style:Normal",
    "style_aliases": ["Normal", "正文", "Body Text", "Body Text Indent"],
    "expected": "宋体",
    "section": "正文格式",
    "rule_text": "正文中文字体为宋体"
  },
  {
    "id": "body-font-ascii",
    "type": "font",
    "scope": "ascii",
    "selector": "style:Normal",
    "style_aliases": ["Normal", "正文", "Body Text", "Body Text Indent"],
    "expected": "Times New Roman",
    "section": "正文格式"
  },
  {
    "id": "body-font-size",
    "type": "font_size",
    "selector": "style:Normal",
    "style_aliases": ["Normal", "正文", "Body Text", "Body Text Indent"],
    "expected": 12,
    "expected_display": "小四（12pt）",
    "section": "正文格式"
  },
  {
    "id": "body-line-spacing",
    "type": "line_spacing",
    "selector": "style:Normal",
    "style_aliases": ["Normal", "正文", "Body Text", "Body Text Indent"],
    "expected": {"mode": "multiple", "value": 1.5},
    "section": "正文格式"
  },
  {
    "id": "body-indent",
    "type": "first_line_indent",
    "selector": "style:Normal",
    "style_aliases": ["Normal", "正文", "Body Text", "Body Text Indent"],
    "expected": 24,
    "expected_display": "2字符（24pt）",
    "section": "正文格式"
  },
  {
    "id": "body-alignment",
    "type": "alignment",
    "selector": "style:Normal",
    "style_aliases": ["Normal", "正文", "Body Text", "Body Text Indent"],
    "expected": "justify",
    "section": "正文格式"
  }
]
```

### Headings — multi-level example

```json
[
  {
    "id": "h1-font-east",
    "type": "font",
    "scope": "east_asia",
    "selector": "style:Heading 1",
    "style_aliases": ["Heading 1", "标题 1", "heading 1"],
    "expected": "黑体"
  },
  {
    "id": "h1-font-size",
    "type": "font_size",
    "selector": "style:Heading 1",
    "style_aliases": ["Heading 1", "标题 1", "heading 1"],
    "expected": 16,
    "expected_display": "三号（16pt）"
  },
  {
    "id": "h1-alignment",
    "type": "alignment",
    "selector": "style:Heading 1",
    "style_aliases": ["Heading 1", "标题 1", "heading 1"],
    "expected": "center"
  },
  {
    "id": "h2-font-east",
    "type": "font",
    "scope": "east_asia",
    "selector": "style:Heading 2",
    "style_aliases": ["Heading 2", "标题 2", "heading 2"],
    "expected": "黑体"
  },
  {
    "id": "h2-font-size",
    "type": "font_size",
    "selector": "style:Heading 2",
    "style_aliases": ["Heading 2", "标题 2", "heading 2"],
    "expected": 14,
    "expected_display": "四号（14pt）"
  }
]
```

### Captions — figure and table

```json
[
  {
    "id": "fig-caption-font-size",
    "type": "font_size",
    "selector": "caption:figure",
    "style_aliases": ["Caption", "题注", "Figure Caption"],
    "caption_prefix_patterns": ["^图\\s*\\d", "^Figure\\s*\\d"],
    "expected": 10.5,
    "expected_display": "五号（10.5pt）"
  },
  {
    "id": "tbl-caption-font-size",
    "type": "font_size",
    "selector": "caption:table",
    "style_aliases": ["Caption", "题注", "Table Caption"],
    "caption_prefix_patterns": ["^表\\s*\\d", "^Table\\s*\\d"],
    "expected": 10.5
  }
]
```

### Page layout — margins and page size

```json
[
  {"id": "page-size", "type": "page_size", "expected": "A4"},
  {"id": "margin-top", "type": "margin", "side": "top", "expected": 2.54},
  {"id": "margin-bottom", "type": "margin", "side": "bottom", "expected": 2.54},
  {"id": "margin-left", "type": "margin", "side": "left", "expected": 3.17},
  {"id": "margin-right", "type": "margin", "side": "right", "expected": 3.17}
]
```

## Critical Rules

- **`style_aliases` must be complete**: When a rule applies to paragraphs with multiple style names (e.g., body text with both `Normal` and `Body Text`), ALL style names must be listed in `style_aliases`. Missing any one causes missed paragraphs.

- **Use `paragraph-stats` to discover actual style names**: Before constructing check instructions, always run `paragraph-stats --style-hint <hint>` to see what style names the document actually uses.

- **`unresolved` means 0 matches**: If a check returns `unresolved` (matched_count = 0), the selector or style_aliases are likely wrong — the document likely has paragraphs, but under a different style name.

- **Chinese font size mapping**: Common mappings used in `expected_display`:

  | Chinese name | pt value |
  |-------------|----------|
  | 初号 | 42 |
  | 小初 | 36 |
  | 一号 | 26 |
  | 小一 | 24 |
  | 二号 | 22 |
  | 小二 | 18 |
  | 三号 | 16 |
  | 小三 | 15 |
  | 四号 | 14 |
  | 小四 | 12 |
  | 五号 | 10.5 |
  | 小五 | 9 |

- **First line indent**: 2 Chinese characters at 小四 = 24pt. The exact value depends on font size: `indent_pt = font_size_pt * 2`.

## Output Format

```json
{
  "summary": {"total": 10, "pass": 8, "fail": 1, "unresolved": 1},
  "results": [
    {
      "id": "body-font-size",
      "type": "font_size",
      "status": "pass",
      "expected": "小四（12pt）",
      "actual": "300 ok",
      "matched_count": 300,
      "issues": []
    },
    {
      "id": "h1-alignment",
      "type": "alignment",
      "status": "fail",
      "expected": "center",
      "actual": "3 ok / 2 mismatch",
      "matched_count": 5,
      "issues": [
        {"paragraph_id": "p-15", "actual": "left", "text_preview": "第三章 系统设计"}
      ]
    }
  ]
}
```

## Troubleshooting

| symptom | likely cause | fix |
|---------|-------------|-----|
| All checks `unresolved` | Wrong facts file or empty document | Verify facts.json has paragraphs |
| Specific check `unresolved` | Selector mismatch | Run `paragraph-stats` to find correct style names, update `style_aliases` |
| `fail` but values look close | Tolerance exceeded | Check if the tolerance (e.g., 0.2pt for font_size) is appropriate for the rule |
| Caption check `unresolved` | No matching prefix pattern | Add patterns matching the document's actual caption format to `caption_prefix_patterns` |
