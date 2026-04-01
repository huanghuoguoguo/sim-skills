---
name: validate-report
description: 检查 report.json 的结构、计数和 issue 形状是否自洽，用于格式检查输出的最终验收。
---

# validate-report

这是一个 gate skill，用于检查 `report.json` 是否结构完整、计数一致。

命令：

```bash
python3 .claude/skills/validate-report/scripts/validate.py <report.json>
```
