---
name: merge-spec-fragments
description: 合并多个局部 spec fragment，收敛为 spec.json 草稿，并保留冲突和待确认项。
---

# merge-spec-fragments

这是一个 analysis skill。

职责：

- 合并多个 selector 级别的局部规则
- 识别冲突来源
- 生成 `spec.json` 草稿
- 把不确定项显式保留给 gate 或人工确认

输出要求：

- 结构尽量稳定
- 冲突不应被静默覆盖
