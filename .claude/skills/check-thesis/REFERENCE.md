# check-thesis Reference

Advanced patterns, complete workflow examples, and troubleshooting for thesis format checking.

## Complete Workflow Example

### Step 1: Parse the document

```bash
python3 -m sim_docs parse thesis.docx --output facts.json
```

### Step 2: Discover actual styles

Before constructing checks, always confirm what style names the document uses:

```bash
# Body text styles
python3 -m sim_docs stats facts.json \
  --style-hint normal --style-hint "body text" \
  --min-length 20 --require-body-shape

# Heading styles
python3 -m sim_docs stats facts.json \
  --style-hint "heading 1"

python3 -m sim_docs stats facts.json \
  --style-hint "heading 2"
```

Check the `style_distribution` output — include ALL style names in `style_aliases`.

### Step 3: Construct check instructions

Write checks.json directly from the rules. See `batch-check/REFERENCE.md` for complete examples.

### Step 4: Run batch-check

```bash
python3 -m sim_docs check facts.json checks.json --output result.json
```

### Step 5: Investigate failures

```bash
# Find specific paragraphs by keyword
python3 -m sim_docs query-text thesis.docx --keyword "摘要"

# Visual verification of a specific page
python3 -m sim_docs render thesis.docx --page 1 --output page1.png
```

## Deterministic vs Semantic Rules

### Deterministic (use batch-check)

These can be fully automated with check instructions:

- Font family (Chinese / English)
- Font size
- Line spacing (mode + value)
- Paragraph alignment
- First line indent
- Spacing before / after
- Page margins
- Page size
- Caption format (font, size, alignment)

### Semantic (Agent judgment required)

These require context understanding and cannot be expressed as simple property checks:

| rule type | what to check | how to check |
|-----------|--------------|--------------|
| Abstract format | Word count, language, paragraph structure | `query-word-text --keyword "摘要"`, then Agent reads and judges |
| References format | GB/T 7714 compliance, numbering, punctuation | `query-word-text --keyword "参考文献"`, then Agent validates patterns |
| TOC structure | Heading levels, numbering scheme, dot leaders | Agent reads parsed headings and judges structure |
| Chapter numbering | Correct sequence, format consistency | Agent checks heading text patterns |
| Page number placement | Position, starting page | `render-word-page` for visual verification |
| Header/footer content | Text matches requirements | Check `headers`/`footers` in facts.json |

## Handling `unresolved` Results

`unresolved` (matched_count = 0) almost always means a selector problem, not a missing document section.

**Resolution procedure:**

1. Run `paragraph-stats` to see actual style names:
   ```bash
   python3 -m sim_docs stats facts.json --style-hint normal
   ```

2. Compare output `style_distribution` with your `style_aliases`

3. Common mismatches:

   | you wrote | document actually uses |
   |-----------|----------------------|
   | `Normal` | `Body Text`, `正文` |
   | `Heading 1` | `标题 1`, `heading 1` |
   | `Caption` | `题注`, `Figure Caption` |

4. Update `style_aliases` and re-run batch-check

5. Only report as "not applicable" after confirming the document truly has no such paragraphs

## Report Template

The output report should follow this structure:

```markdown
# 格式检查报告

**文档**: thesis.docx
**规则来源**: spec.md
**检查时间**: 2024-XX-XX

## 检查结果摘要

| 类别 | 通过 | 不通过 | 待确认 |
|------|------|--------|--------|
| 页面设置 | 4 | 1 | 0 |
| 正文格式 | 5 | 0 | 0 |
| 标题格式 | 8 | 2 | 0 |
| 语义规则 | 3 | 0 | 1 |

## 详细结果

### 页面设置

- [PASS] 纸张大小: A4 (Python 检查)
- [FAIL] 上边距: 期望 2.54cm, 实际 3.0cm (Python 检查)

### 正文格式

- [PASS] 中文字体: 宋体, 300 段落全部通过 (Python 检查)
...

### 语义规则

- [PASS] 摘要格式: 中英文摘要均存在，字数符合要求 (Agent 判断)
- [PENDING] 参考文献格式: 需人工确认 GB/T 7714 合规性 (Agent 判断)
```

## Critical Rules

- **Always do style discovery first**: Never construct checks blindly. Run `paragraph-stats` before writing `style_aliases`.

- **Aggregate failures**: Same rule failing on multiple paragraphs should be reported once with a count, not listed per-paragraph.

- **Mark sources**: Every result must state whether it came from `Python 检查` or `Agent 判断`.

- **Completeness traceback**: After all checks, go back to the original rules and verify no rule was missed.

- **Cross-validate style definitions**: In Chinese templates, style definitions often differ from actual paragraph properties (direct formatting overrides). Always prefer `paragraph-stats` evidence over `query-word-style` output.
