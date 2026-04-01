---
name: validate-spec
description: 兼容入口。顺序调用 validate-spec-structure 和 validate-spec-coverage，对 spec.json 做结构与覆盖双重验收。
---

# validate-spec

这是一个兼容入口 skill。

新的最佳实践是分别调用：

- `validate-spec-structure`
- `validate-spec-coverage`

如果你只想走一个入口，也可以继续使用本 skill。

### API 用法：
```bash
python3 .claude/skills/validate-spec/scripts/validate.py <path_to_spec.json>
```

执行顺序：

1. 先检查结构
2. 再检查覆盖
3. 任意一步失败，都必须回退补偿
