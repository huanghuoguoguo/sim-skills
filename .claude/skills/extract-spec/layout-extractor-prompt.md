# Layout Extractor Subagent

从模板文件中提取页面设置规则（纸张尺寸、页边距、页眉页脚距离）。

## 输入

- 文件路径：`{file_path}`
- 已解析的 facts：`{facts_path}`

---

## ⚡ IRON LAW: NO LAYOUT RULE WITHOUT PARSE VERIFICATION

**页面设置规则必须从 parse-word 输出的 layout 字段提取，不可跳过验证。**

---

## 🔧 Gate Function: Layout Extraction Steps

```
function extract_layout_rules(file_path, facts_path):

    # Step 1: 获取 layout facts
    facts = load_json(facts_path)
    layout = facts.get("layout", {})

    if not layout:
        tool_errors.append({"tool": "parse-word", "error": "layout 字段为空"})
        return BLOCKED

    # Step 2: 提取页面设置
    page_setup = {
        "paper_size": layout.get("page_width") and layout.get("page_height")
            ? f"{layout.page_width}cm × {layout.page_height}cm"
            : null,
        "margins": {
            "top": layout.get("margin_top"),
            "bottom": layout.get("margin_bottom"),
            "left": layout.get("margin_left"),
            "right": layout.get("margin_right")
        },
        "header_distance": layout.get("header_distance"),
        "footer_distance": layout.get("footer_distance")
    }

    # Step 3: 单位转换（如有必要）
    # 如果原值是英寸或 pt，转换为 cm
    for key, value in page_setup.margins:
        if value and value.unit != "cm":
            page_setup.margins[key] = convert_to_cm(value)

    # Step 4: 检查完整性
    missing = []
    if not page_setup.paper_size:
        missing.append("paper_size")
    for side in ["top", "bottom", "left", "right"]:
        if not page_setup.margins[side]:
            missing.append(f"margin_{side}")

    if missing:
        return NEEDS_CONTEXT with {"missing_fields": missing}

    # Step 5: 输出
    return {
        "status": DONE,
        "output": {"layout_rules": page_setup},
        "cross_validation": {
            "sources": ["parse-word layout"],
            "verified": true
        },
        "tool_errors": [],
        "common_sense_check": "pass"  # layout 无常识冲突
    }
```

---

## 📤 Output Format

```json
{
  "status": "DONE" | "BLOCKED" | "NEEDS_CONTEXT",
  "output": {
    "layout_rules": {
      "paper_size": "A4 (21cm × 29.7cm)",
      "margins": {
        "top": "2.54cm",
        "bottom": "2.54cm",
        "left": "3.57cm",
        "right": "2.77cm"
      },
      "header_distance": "1.5cm",
      "footer_distance": "1.75cm"
    }
  },
  "cross_validation": {
    "sources": ["parse-word layout"],
    "verified": true
  },
  "tool_errors": [],
  "common_sense_check": "pass"
}
```

---

## ⚠️ Error Handling

| 错误 | 处理 |
|------|------|
| layout 字段为空 | 返回 BLOCKED，建议用 inspect-word-xml 查 raw XML |
| 页边距值缺失 | 返回 NEEDS_CONTEXT，列出 missing_fields |
| 单位转换失败 | 记录到 tool_errors，保留原单位输出