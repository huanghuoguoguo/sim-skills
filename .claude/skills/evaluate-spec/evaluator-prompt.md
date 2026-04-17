# Spec Evaluator Subagent

评估 spec.md 的质量，执行程序化检查（common-sense、structure、conflicts）。

## 输入

- spec.md 文件路径：`{spec_path}`

---

## ⚡ IRON LAW: NO SEMANTIC EVALUATION WITHOUT COMMON-SENSE CHECK

**语义评估前，必须先执行 `spec-check --mode common-sense`。**

检查顺序（不可跳步）：

1. common-sense check → 通过后才执行下一步
2. structure check
3. conflicts check
4. body-consistency check (如有 evidence)

---

## 🔧 Gate Function: Evaluation Sequence

```
function evaluate_spec(spec_path):

    tool_errors = []
    check_results = {}

    # Step 1: Common-sense check (MUST PASS FIRST)
    result_1 = run("python3 -m sim_docs spec-check --mode common-sense {spec_path}")

    if result_1.error:
        tool_errors.append({"tool": "spec-check common-sense", "error": result_1.error})
        return BLOCKED

    check_results.common_sense = {
        "status": result_1.status,
        "conflicts": result_1.conflicts,
        "summary": result_1.summary
    }

    if result_1.status == "needs_revision":
        # 拒绝继续，必须修正
        return {
            "status": BLOCKED,
            "output": {"evaluation": "common_sense_failed"},
            "cross_validation": check_results,
            "tool_errors": tool_errors,
            "common_sense_check": "needs_revision"
        }

    # Step 2: Structure check
    result_2 = run("python3 -m sim_docs spec-check --mode structure {spec_path}")

    if result_2.error:
        tool_errors.append({"tool": "spec-check structure", "error": result_2.error})
    else:
        check_results.structure = {
            "status": result_2.status,
            "covered_sections": result_2.covered_sections,
            "missing_sections": result_2.missing_sections
        }

    # Step 3: Conflicts check
    result_3 = run("python3 -m sim_docs spec-check --mode conflicts {spec_path}")

    if result_3.error:
        tool_errors.append({"tool": "spec-check conflicts", "error": result_3.error})
    else:
        check_results.conflicts = {
            "status": result_3.status,
            "conflicts": result_3.conflicts
        }

    # Step 4: Aggregate results
    overall_status = "pass"
    issues = []

    if check_results.structure and check_results.structure.missing_sections:
        overall_status = "needs_revision"
        issues.append(f"缺失章节: {check_results.structure.missing_sections}")

    if check_results.conflicts and check_results.conflicts.conflicts:
        overall_status = "needs_revision"
        issues.append(f"内部冲突: {check_results.conflicts.conflicts.length} 项")

    return {
        "status": DONE,
        "output": {
            "evaluation_result": overall_status,
            "issues": issues,
            "checks_passed": ["common_sense", "structure", "conflicts"]
        },
        "cross_validation": check_results,
        "tool_errors": tool_errors,
        "common_sense_check": "pass"
    }
```

---

## 📤 Output Format

**成功输出：**

```json
{
  "status": "DONE",
  "output": {
    "evaluation_result": "pass",
    "issues": [],
    "checks_passed": ["common_sense", "structure", "conflicts"]
  },
  "cross_validation": {
    "common_sense": {"status": "pass", "conflicts": []},
    "structure": {"status": "pass", "covered_sections": [...], "missing_sections": []},
    "conflicts": {"status": "pass", "conflicts": []}
  },
  "tool_errors": [],
  "common_sense_check": "pass"
}
```

**Common-sense 检查失败输出：**

```json
{
  "status": "BLOCKED",
  "output": {"evaluation": "common_sense_failed"},
  "cross_validation": {
    "common_sense": {
      "status": "needs_revision",
      "conflicts": [
        {"line_number": 22, "type": "font_common_sense_conflict", ...}
      ]
    }
  },
  "tool_errors": [],
  "common_sense_check": "needs_revision"
}
```

---

## ⚠️ Error Handling

| 错误 | 处理 |
|------|------|
| common-sense check 返回 JSON 解析错误 | 返回 BLOCKED，记录到 tool_errors |
| structure check 失败 | 记录到 tool_errors，继续执行 conflicts check |
| 所有检查都失败 | 返回 BLOCKED，汇总所有 tool_errors |