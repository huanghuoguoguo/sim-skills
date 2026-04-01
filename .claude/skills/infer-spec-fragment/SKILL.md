---
name: infer-spec-fragment
description: 从 DocumentIR、文本线索和样式线索中提取某个 selector 的局部规则片段，适合被 extract-spec workflow 反复调用。
---

# infer-spec-fragment

这是一个 analysis skill。

输入通常包括：

- `DocumentIR`
- 文字线索
- 样式线索
- 目标 selector

输出应是一个局部 `spec fragment`，只覆盖单个 selector 或单个布局主题。

建议输出形状：

```json
{
  "selector": "body.paragraph",
  "properties": {
    "font_family_zh": "宋体",
    "font_size_pt": 12
  },
  "evidence": [
    "来自样式定义",
    "来自模板说明文字"
  ]
}
```
