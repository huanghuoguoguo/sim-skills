# Heading Extractor Subagent

从模板文件中提取各级标题的字体、字号、行距、对齐、段距规则。

## 输入

- 文件路径：`{file_path}`
- 已解析的 facts：`{facts_path}`
- 标题级别：Heading 1, Heading 2, Heading 3, Heading 4

---

## ⚡ IRON LAW: EVERY HEADING LEVEL MUST BE CROSS-VALIDATED

**每级标题都必须用 paragraph-stats 验证实际段落属性，不可仅凭样式定义输出。**

---

## 🚨 Red Flags

| 🚨 Red Flag | 必须执行的动作 |
|-------------|----------------|
| 样式定义与 paragraph-stats 分布不一致 | 用 query-word-text 查文字说明，或标记"待确认项" |
| Heading 3 样式定义与实际段落字体不一致（常见问题） | 特别关注，模板中常见 Heading 3 字体不一致 |
| paragraph-stats 返回 matched_count=0 | 用更宽松条件重新采样，或确认文档中是否真的没有该级标题 |

---

## 🔧 Gate Function: Heading Extraction Steps

```
function extract_heading_rules(file_path, facts_path):

    heading_rules = []
    tool_errors = []
    cross_validation = {}

    for level in [1, 2, 3, 4]:
        style_name = f"Heading {level}"

        # Step 1: 样式定义
        result_1 = run("python3 -m sim_docs query-style {file_path} --style {style_name}")
        if result_1.error:
            tool_errors.append({"tool": "query-word-style", "error": result_1.error, "style": style_name})
            continue

        hypothesis = {
            "east_asia": result_1.east_asia_font,
            "ascii": result_1.ascii_font,
            "font_size": result_1.font_size,
            "line_spacing": result_1.line_spacing,
            "alignment": result_1.alignment,
            "space_before": result_1.space_before,
            "space_after": result_1.space_after
        }

        # Step 2: 实际段落属性
        result_2 = run("python3 -m sim_docs stats {facts_path} --style-hint {style_name}")

        actual = null
        if result_2.matched_count > 0:
            actual = {
                "east_asia": result_2.east_asia_font_distribution[0].value,
                "ascii": result_2.ascii_font_distribution[0].value,
                "font_size": result_2.font_size_distribution[0].value,
                "line_spacing": result_2.line_spacing_distribution[0].value
            }
        else:
            tool_errors.append({"tool": "paragraph-stats", "error": "无匹配段落", "style": style_name})

        # Step 3: 冲突检测
        conflicts = []
        if actual and hypothesis != actual:
            conflicts.append({
                "type": "style_vs_actual",
                "style": hypothesis,
                "actual": actual
            })

        # Step 4: 输出规则
        if actual:
            # 使用实际段落属性（这才是用户看到的）
            # ⚠️ 如果 ascii_font 是中文字体，标注待确认
            ascii_font_value = actual.ascii
            if ascii_font_value in ["宋体", "黑体", "楷体", "仿宋"]:
                ascii_font_value = f"⚠️ 待确认（模板使用 {actual.ascii}）"

            rule = {
                "level": level,
                "east_asia_font": actual.east_asia,
                "ascii_font": ascii_font_value,
                "font_size": actual.font_size,
                "line_spacing": hypothesis.line_spacing,  # 行距通常来自样式
                "alignment": hypothesis.alignment,
                "space_before": hypothesis.space_before,
                "space_after": hypothesis.space_after,
                "source": "actual_paragraphs",
                "conflict_note": conflicts.length > 0 ? "样式定义与实际不一致" : null
            }
        else:
            rule = {
                "level": level,
                "source": "style_definition_only",
                "conflict_note": "无实际段落验证，仅用样式定义"
            }

        heading_rules.append(rule)
        cross_validation[style_name] = {
            "sources": ["style_definition", "paragraph_stats"],
            "hypothesis": hypothesis,
            "actual": actual,
            "conflicts": conflicts
        }

    # Step 5: Common sense check
    common_sense_issues = []
    for rule in heading_rules:
        if rule.ascii_font and rule.ascii_font.startswith("⚠️"):
            common_sense_issues.append(f"Heading {rule.level}: 西文字体需确认")

    common_sense_check = common_sense_issues.length > 0 ? "needs_revision" : "pass"

    # ⚠️ 重要：返回 DONE（不是 NEEDS_CONTEXT）
    # 让主 Agent 合并输出，用户看到标注后自行修正
    return {
        "status": DONE,
        "output": {"heading_rules": heading_rules},
        "cross_validation": cross_validation,
        "tool_errors": tool_errors,
        "common_sense_check": common_sense_check,
        "common_sense_issues": common_sense_issues
    }
```

---

## 📤 Output Format

```json
{
  "status": "DONE",
  "output": {
    "heading_rules": [
      {
        "level": 1,
        "east_asia_font": "黑体",
        "ascii_font": "黑体",
        "font_size": 15,
        "line_spacing": {"mode": "exact", "value": 20},
        "alignment": "center",
        "space_before": 30,
        "space_after": 36,
        "source": "actual_paragraphs",
        "conflict_note": null
      },
      {
        "level": 3,
        "east_asia_font": "黑体",
        "ascii_font": "黑体",
        "font_size": 12,
        "source": "actual_paragraphs",
        "conflict_note": "样式定义宋体，实际段落黑体，存在不一致"
      }
    ]
  },
  "cross_validation": {
    "Heading 1": {
      "sources": ["style_definition", "paragraph_stats"],
      "hypothesis": {...},
      "actual": {...},
      "conflicts": []
    },
    "Heading 3": {
      "conflicts": [{"type": "style_vs_actual", ...}]
    }
  },
  "tool_errors": [],
  "common_sense_check": "needs_revision",
  "common_sense_issues": ["Heading 1: 西文字体 '黑体' 是中文字体"]
}
```