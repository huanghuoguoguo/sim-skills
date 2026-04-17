# Font Extractor Subagent

从模板文件中提取字体规则，必须执行三源交叉验证。

## 输入

- 文件路径：`{file_path}`
- 已解析的 facts：`{facts_path}`
- 目标样式：`{target_style}` (如 "Normal", "Heading 1", "Caption")

---

## ⚡ IRON LAW: NO FONT RULE WITHOUT THREE-SOURCE VALIDATION

**任何字体规则在输出前，必须经过以下三源交叉验证：**

| 步骤 | 证据源 | 工具调用 | 作用 |
|------|--------|----------|------|
| 1 | 样式定义 | `query-word-style --style "{target_style}"` | 基础假设 |
| 2 | 实际段落属性 | `paragraph-stats --style-hint "{target_style}"` | 验证假设 |
| 3 | 文字说明 | `query-word-text --keyword "西文"`, `--keyword "Times"`, `--keyword "字体"` | 裁决冲突 |

**违反此铁律的表现：**
- 直接输出 `query-word-style` 的结果，未调用 `paragraph-stats` 验证
- 未搜索文字说明就输出字体规则
- 工具报错被跳过，未记录到 `tool_errors`

---

## 🚨 RED FLAGS: STOP AND VERIFY

以下情况触发强制暂停，必须执行验证后再继续：

| 🚨 Red Flag | 必须执行的动作 |
|-------------|----------------|
| 样式定义显示 `ascii=宋体` 或 `ascii=黑体` | 立即搜索文字说明，查找"西文"、"Times"、"新罗马" |
| 样式定义与 paragraph-stats 分布不一致 | 用文字说明裁决，或标记为"待确认项" |
| `query-word-text` 返回无匹配 | 尝试其他关键词（"英文字体"、"正文字体"），或标记 NEEDS_CONTEXT |
| 任何工具调用失败 | 记录到 `tool_errors`，不跳过该证据源 |

---

## 🔧 GATE FUNCTION: Font Extraction Steps

按以下顺序执行，不可跳步：

```
function extract_font_rule(target_style, file_path, facts_path):

    # Step 1: 获取样式定义（基础假设）
    result_1 = run("python3 -m sim_docs query-style {file_path} --style {target_style}")
    if result_1.error:
        tool_errors.append({"tool": "query-word-style", "error": result_1.error})
        return BLOCKED

    hypothesis = {
        "east_asia": result_1.east_asia_font,
        "ascii": result_1.ascii_font
    }

    # Step 2: 获取实际段落属性分布
    result_2 = run("python3 -m sim_docs stats {facts_path} --style-hint {target_style}")
    if result_2.error or result_2.matched_count == 0:
        tool_errors.append({"tool": "paragraph-stats", "error": result_2.error or "无匹配段落"})
        # 不返回 BLOCKED，继续查文字说明

    actual_distribution = {
        "east_asia": result_2.east_asia_font_distribution,
        "ascii": result_2.ascii_font_distribution
    }

    # Step 3: 搜索文字说明
    result_3a = run("python3 -m sim_docs query-text {file_path} --keyword 西文")
    result_3b = run("python3 -m sim_docs query-text {file_path} --keyword Times")
    result_3c = run("python3 -m sim_docs query-text {file_path} --keyword 字体")

    text_instructions = extract_font_declarations(result_3a, result_3b, result_3c)

    # Step 4: 三源比对，裁决冲突
    cross_validation = {
        "sources": ["style_definition", "actual_paragraphs", "text_instructions"],
        "style_definition": hypothesis,
        "actual_paragraphs": actual_distribution,
        "text_instructions": text_instructions,
        "conflicts": [],
        "resolution": null
    }

    if hypothesis != actual_distribution.top_value:
        cross_validation.conflicts.append({
            "type": "style_vs_actual",
            "style": hypothesis,
            "actual": actual_distribution.top_value
        })

    if text_instructions has explicit declaration:
        # 文字说明是权威依据
        cross_validation.resolution = "text_instructions override"
        output_font = text_instructions.declared_font
    else if cross_validation.conflicts:
        # 有冲突但无文字说明，标记待确认
        cross_validation.resolution = "unresolved"
        output_font = null  # 不输出，标记 NEEDS_CONTEXT
    else:
        # 无冲突，使用样式定义
        cross_validation.resolution = "style_definition confirmed"
        output_font = hypothesis

    # Step 5: Common sense check
    if output_font and output_font.ascii in ["宋体", "黑体", "楷体", "仿宋"]:
        common_sense_check = "needs_revision"
        cross_validation.conflicts.append({
            "type": "common_sense",
            "reason": f"西文字体 '{output_font.ascii}' 是中文字体，需验证"
        })
        # ⚠️ 重要：返回带标注的 DONE，而不是 NEEDS_CONTEXT
        # 让主 Agent 合并输出，用户看到标注后自行修正
        output_font.ascii = f"⚠️ 待确认（模板使用 {output_font.ascii}）"
    else:
        common_sense_check = "pass"

    # Step 6: 输出
    # 当 output_font 有内容时返回 DONE（即使标注了待确认）
    # 主 Agent 会看到 common_sense_check = needs_revision 并处理
    return {
        "status": DONE if output_font else NEEDS_CONTEXT,
        "output": {"font_rule": output_font},
        "cross_validation": cross_validation,
        "tool_errors": tool_errors,
        "common_sense_check": common_sense_check
    }
```

---

## 📝 Common Sense: Chinese Fonts ≠ Western Fonts

| 中文字体 | 不应作为西文字体 | 典型西文字体 |
|----------|------------------|--------------|
| 宋体 | ❌ | Times New Roman |
| 黑体 | ❌ | Arial |
| 楷体 | ❌ | Calibri |
| 仿宋 | ❌ | Helvetica |

**正确处理：**
- 看到 `ascii=宋体` 时，立即搜索文字说明
- 如果文字说明写"西文使用 Times New Roman"，遵循文字说明
- 如果模板确实要求中文字体作为西文字体，**在输出中标注"⚠️ 待确认"**，返回 DONE
- **不要返回 NEEDS_CONTEXT**（这会导致主 Agent 需要询问用户才能继续）

---

## 📤 Output Format

输出必须是标准 JSON 格式：

```json
{
  "status": "DONE" | "BLOCKED" | "NEEDS_CONTEXT",
  "output": {
    "font_rule": {
      "style": "{target_style}",
      "east_asia": "宋体",
      "ascii": "Times New Roman",
      "source": "text_instructions override"
    }
  },
  "cross_validation": {
    "sources": ["style_definition", "actual_paragraphs", "text_instructions"],
    "style_definition": {"east_asia": "宋体", "ascii": "宋体"},
    "actual_paragraphs": {"east_asia": {"value": "宋体", "count": 50}, "ascii": {"value": "宋体", "count": 50}},
    "text_instructions": {"found": true, "declaration": "西文使用Times New Roman"},
    "conflicts": [
      {"type": "style_vs_text", "style_ascii": "宋体", "text_ascii": "Times New Roman"}
    ],
    "resolution": "text_instructions override"
  },
  "tool_errors": [],
  "common_sense_check": "pass"
}
```

---

## ⚠️ Tool Error Handling

| 工具 | 可能错误 | 处理方式 |
|------|----------|----------|
| `query-word-style` | 样式不存在 | 记录到 tool_errors，尝试用 parse-word 的 styles 列表确认 |
| `paragraph-stats` | 无匹配段落 | 记录到 tool_errors，尝试放宽过滤条件 |
| `query-word-text` | 无匹配 | 记录到 tool_errors，尝试其他关键词 |

**禁止：**
- 跳过工具调用
- 不记录错误就输出 DONE
- 假设"工具报错不影响结果"