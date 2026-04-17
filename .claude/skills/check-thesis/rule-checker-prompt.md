# Rule Checker Subagent

执行确定性规则检查（batch-check），并做完整性回溯。

## 输入

- 文档 facts：`{facts_path}`
- spec.md 规则：`{spec_path}`

---

## ⚡ IRON LAW: ALL RULES MUST BE CHECKED

**每条规则都必须检查，不能跳过。unresolved 必须调查，不能假设"没问题"。**

---

## 🚨 Red Flags

| 🚨 Red Flag | 必须执行的动作 |
|-------------|----------------|
| batch-check 返回 `unresolved` (matched_count=0) | 用 paragraph-stats 确认实际样式名，修正 style_aliases |
| style_aliases 遗漏 spec.md 中列出的"适用样式" | 补充缺失的样式名，重新执行 batch-check |
| 工具调用失败 | 记录到 tool_errors，不跳过检查 |

---

## 🔧 Gate Function: Rule Checking Steps

```
function check_rules(facts_path, spec_path):

    tool_errors = []
    check_results = []
    coverage_status = {"checked": [], "skipped": [], "errors": []}

    # Step 1: Parse spec.md to construct check instructions
    spec = parse_spec_md(spec_path)
    checks = construct_checks_from_spec(spec)

    # Step 2: Execute batch-check
    result = run("python3 -m sim_docs check {facts_path} checks.json")

    if result.error:
        tool_errors.append({"tool": "batch-check", "error": result.error})
        return BLOCKED

    # Step 3: Process results
    for check_result in result.results:
        if check_result.status == "unresolved":
            # Step 3.1: Investigate unresolved
            stats_result = run("python3 -m sim_docs stats {facts_path} --style-hint {check_result.style}")

            if stats_result.matched_count > 0:
                # 样式名有误，修正 style_aliases
                actual_styles = stats_result.style_distribution
                coverage_status.errors.append({
                    "rule": check_result.rule,
                    "issue": "style_aliases_incomplete",
                    "actual_styles": actual_styles
                })
            else:
                # 文档中确实没有该类段落
                coverage_status.skipped.append({
                    "rule": check_result.rule,
                    "reason": "文档不包含此类段落"
                })
        else:
            coverage_status.checked.append(check_result.rule)
            check_results.append(check_result)

    # Step 4: Completeness traceback
    original_rules = extract_rules_from_spec(spec_path)
    missing_rules = []

    for rule in original_rules:
        if rule not in coverage_status.checked and rule not in coverage_status.skipped:
            missing_rules.append(rule)

    if missing_rules:
        coverage_status.errors.append({
            "type": "missing_rules",
            "rules": missing_rules
        })

    # Step 5: Determine status
    status = DONE
    if coverage_status.errors:
        status = NEEDS_CONTEXT  # 有错误需要修正

    return {
        "status": status,
        "output": {
            "check_results": check_results,
            "coverage_status": coverage_status
        },
        "cross_validation": {
            "style_aliases_verification": "verified",
            "completeness_traceback": "done"
        },
        "tool_errors": tool_errors,
        "common_sense_check": "pass"  # batch-check 不涉及常识检查
    }
```

---

## 📤 Output Format

```json
{
  "status": "DONE" | "NEEDS_CONTEXT" | "BLOCKED",
  "output": {
    "check_results": [
      {"rule": "正文字体", "status": "pass", "matched_count": 50},
      {"rule": "正文字号", "status": "fail", "mismatch_count": 5}
    ],
    "coverage_status": {
      "checked": ["正文字体", "正文字号", "标题字体"],
      "skipped": [{"rule": "目录格式", "reason": "文档不包含目录"}],
      "errors": []
    }
  },
  "cross_validation": {
    "style_aliases_verification": "verified",
    "completeness_traceback": "done"
  },
  "tool_errors": [],
  "common_sense_check": "pass"
}
```

---

## Completeness Traceback Format

检查结束后，必须输出每条原始规则的检查状态：

```
原始规则列表（来自 spec.md）:
1. 正文字体 → ✅ 已检查 (pass)
2. 正文字号 → ✅ 已检查 (fail, 5 处不匹配)
3. 页边距 → ✅ 已检查 (pass)
4. 目录格式 → ⚠️ 文档不包含目录
5. 封面格式 → ❌ 未检查 (需要视觉检查)
```