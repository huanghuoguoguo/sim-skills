---
name: validate-spec-coverage
description: 检查 spec.json 对当前论文场景的规则覆盖是否足够。支持按 profile 定义覆盖要求。
---

# validate-spec-coverage

这是一个 gate skill，检查 spec 的场景覆盖范围。

默认 profile 为 `thesis-basic`。

命令：

```bash
python3 .claude/skills/validate-spec-coverage/scripts/validate.py <spec.json> [--profile thesis-basic]
```
